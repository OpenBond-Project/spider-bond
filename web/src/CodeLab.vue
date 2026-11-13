<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Play, RotateCcw, Lightbulb, ShieldCheck, Terminal, Send, CheckCircle2, XCircle, LoaderCircle } from 'lucide-vue-next'

const props = defineProps({ caseData: { type: Object, default: null } })

const code = ref('')
const ready = ref(false)
const loading = ref(false)
const running = ref(false)
const status = ref('')
const stdout = ref('')
const runError = ref('')
const judgeResult = ref(null)
const answerSource = ref('')   // 兜底提示：答案是从哪来的
const showHint = ref(false)
const editorEl = ref(null)

let view = null
let worker = null
let watchdog = null      // 代码执行看门狗（12 秒，防死循环）
let bootTimer = null     // 运行时加载超时（120 秒，下载 9MB 需要时间）
let pending = null
let seq = 0

/* 每道题一个草稿 key：刷新、切页面、关浏览器都能接着写 */
function draftKey(c) {
  if (!c) return ''
  return 'sl_code_' + (c.kind === 'task' ? c.id : c.slug)
}

watch(() => props.caseData, (c) => {
  let saved = null
  try {
    saved = c ? localStorage.getItem(draftKey(c)) : null
  } catch (e) { /* 隐私模式禁用存储 */ }
  code.value = saved != null ? saved : (c ? c.starter : '')
  stdout.value = ''
  runError.value = ''
  judgeResult.value = null
  answerSource.value = ''
  showHint.value = false
  nextTick(() => initEditor())
}, { immediate: true })

// 边写边存草稿；文本量小，直接同步写不会有感知
watch(code, (v) => {
  const c = props.caseData
  if (!c) return
  try {
    localStorage.setItem(draftKey(c), v)
    // 通知外层：已登录时由 App 防抖推送到云端
    window.dispatchEvent(new CustomEvent('sl-draft-saved'))
  } catch (e) { /* 配额满或隐私模式，忽略 */ }
})

async function initEditor() {
  if (!editorEl.value || view) return
  const [
    { EditorView, basicSetup }, { python },
    { HighlightStyle, syntaxHighlighting }, { tags },
  ] = await Promise.all([
    import('codemirror'), import('@codemirror/lang-python'),
    import('@codemirror/language'), import('@lezer/highlight'),
  ])

  // 用语义类名替代 CodeMirror 内置的浅色调色板，颜色交给 CSS 变量，
  // 切换夜间模式时编辑器语法高亮会自动跟随。
  const slHighlight = HighlightStyle.define([
    { tag: tags.keyword, class: 'sl-tok-kw' },
    { tag: [tags.self, tags.atom, tags.bool, tags.null], class: 'sl-tok-kw' },
    { tag: [tags.string, tags.special(tags.string), tags.regexp], class: 'sl-tok-str' },
    { tag: [tags.comment, tags.lineComment, tags.blockComment, tags.docComment], class: 'sl-tok-com' },
    { tag: [tags.number, tags.integer, tags.float], class: 'sl-tok-num' },
    { tag: [tags.function(tags.variableName), tags.function(tags.propertyName)], class: 'sl-tok-fn' },
    { tag: [tags.className, tags.typeName, tags.standard(tags.name), tags.definition(tags.variableName)], class: 'sl-tok-cls' },
    { tag: [tags.operator, tags.punctuation, tags.bracket], class: 'sl-tok-op' },
    { tag: [tags.variableName, tags.propertyName], class: 'sl-tok-var' },
    { tag: [tags.meta, tags.processingInstruction, tags.annotation], class: 'sl-tok-meta' },
  ])

  view = new EditorView({
    doc: code.value,
    extensions: [
      basicSetup,
      python(),
      syntaxHighlighting(slHighlight),
      EditorView.lineWrapping,
      EditorView.updateListener.of((u) => {
        if (u.docChanged) code.value = u.state.doc.toString()
      }),
      EditorView.theme({
        // 全部用主题变量，切换夜间模式时编辑器自动跟随
        '&': { fontSize: '14px', backgroundColor: 'var(--sl-code-bg)', color: 'var(--sl-code-ink)' },
        '.cm-content': { fontFamily: 'var(--sl-mono)', padding: '12px 0', lineHeight: '1.75' },
        '.cm-gutters': { backgroundColor: 'var(--sl-surface-2)', color: 'var(--sl-muted)', border: 'none' },
        '.cm-activeLine': { backgroundColor: 'var(--sl-blue-soft)' },
        '.cm-activeLineGutter': { backgroundColor: 'var(--sl-blue-soft)' },
        // CodeMirror 默认补全项用 emoji 作图标，本站统一禁用（补全文字保留）
        '.cm-completionIcon': { display: 'none !important' },
      }),
    ],
    parent: editorEl.value,
  })
}

function resetCode() {
  code.value = props.caseData.starter
  if (view) {
    view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: code.value } })
  }
  stdout.value = ''
  runError.value = ''
  judgeResult.value = null
  answerSource.value = ''
}

function destroyWorker() {
  if (watchdog) { clearTimeout(watchdog); watchdog = null }
  if (bootTimer) { clearTimeout(bootTimer); bootTimer = null }
  if (worker) { worker.terminate(); worker = null }
  ready.value = false
  pending = null
}

function ensureWorker() {
  if (worker) return
  loading.value = true
  status.value = '正在下载 Python 运行时（首次约 9 MB，通常 10-30 秒；之后走浏览器缓存，秒开）...'
  // Pyodide 314.x 要求 module worker；classic worker 会报
  // "Classic web workers are not supported"
  worker = new Worker(new URL('./codelab.worker.js', import.meta.url), { type: 'module' })
  worker.onmessage = (ev) => {
    const m = ev.data || {}
    if (m.type === 'status') { status.value = m.message; return }
    if (m.type === 'ready') {
      ready.value = true
      loading.value = false
      status.value = '沙箱就绪'
      if (bootTimer) { clearTimeout(bootTimer); bootTimer = null }
      return
    }
    if (m.type === 'error') {
      loading.value = false
      status.value = m.message
      if (bootTimer) { clearTimeout(bootTimer); bootTimer = null }
      return
    }
    if (m.type === 'done') {
      if (watchdog) { clearTimeout(watchdog); watchdog = null }
      running.value = false
      const r = m.result || {}
      stdout.value = r.stdout || ''
      runError.value = r.error || ''
      if (pending) { pending.resolve(r); pending = null }
    }
  }
  worker.onerror = (e) => {
    loading.value = false
    status.value = '沙箱启动失败：' + (e.message || '未知错误')
    destroyWorker()
  }
  worker.postMessage({ type: 'init' })

  // 加载阶段单独计时：下载 9MB 运行时 + 编译 WASM，慢网下 30 秒很正常，
  // 不能和「代码执行 12 秒」共用同一个看门狗（否则首次运行必然超时）。
  bootTimer = setTimeout(() => {
    if (ready.value) return
    destroyWorker()
    loading.value = false
    running.value = false
    status.value = '运行时加载超时。若网络正常，可能是浏览器扩展拦截了 .wasm 文件——把本站加入白名单后重试。'
    if (pending) { pending.reject(new Error('boot-timeout')); pending = null }
  }, 120000)
}

// 执行看门狗：只统计用户代码真正跑的这段时间（不含运行时加载）
function armExecWatchdog(reject) {
  if (watchdog) clearTimeout(watchdog)
  watchdog = setTimeout(() => {
    destroyWorker()
    running.value = false
    runError.value = '执行超过 12 秒已被强制终止（疑似死循环）。请检查 while / for 循环的终止条件，下次运行会自动重建沙箱。'
    reject(new Error('timeout'))
  }, 12000)
}

function runCode() {
  return new Promise((resolve, reject) => {
    ensureWorker()
    const id = ++seq
    pending = { id, resolve, reject }
    running.value = true
    runError.value = ''
    stdout.value = ''
    judgeResult.value = null
    const send = () => {
      if (!worker) { reject(new Error('沙箱未就绪')); return }
      worker.postMessage({ type: 'run', id, code: code.value })
      armExecWatchdog(reject)  // 开始执行后才计时
    }
    if (ready.value) { send(); return }
    // 运行时还没加载完：等它准备好再发。加载阶段由 bootTimer 兜底，
    // 这里不能设短超时（否则首次运行会被 12 秒误杀）。
    const t = setInterval(() => {
      if (ready.value) { clearInterval(t); send() }
      else if (!worker) { clearInterval(t); reject(new Error('沙箱已重置')) }
    }, 150)
  })
}

async function doRun(submit) {
  if (running.value) return
  try {
    const r = await runCode()
    if (r.error) return

    // 兜底：没定义 answer 时，用最后一行非空输出当答案。
    // 很多人习惯直接 print 结果，不该因为少写一行赋值就被卡住。
    let payload = r.answer
    answerSource.value = ''
    if (payload == null) {
      const lines = String(r.stdout || '').split('\n').filter((x) => x.trim())
      if (!lines.length) {
        runError.value = '代码没有产出结果。请把最终结果赋给 answer，或用 print() 输出。'
        return
      }
      let last = lines[lines.length - 1].trim()
      // 起始代码最后一行是 print('answer =', answer)，
      // 兜底取这一行时必须把前缀剥掉，否则会把 "answer = xxx" 整串当答案提交。
      const m = last.match(/^answer\s*=\s*(.+)$/i)
      if (m) last = m[1].trim()
      if (!last || /^none$/i.test(last)) {
        runError.value = '没有检测到结果：请把最终值赋给 answer 变量，或 print 出结果。'
        return
      }
      payload = last
      answerSource.value = '未检测到 answer 变量，已取最后一行输出作为答案：' + payload.slice(0, 90)
    }

    if (!submit) return

    const isTask = props.caseData.kind === 'task'
    const resp = await fetch(isTask ? '/api/check' : '/api/check_case', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(isTask
        ? { task_id: props.caseData.id, answer: payload }
        : { slug: props.caseData.slug, answer: payload }),
    })
    judgeResult.value = await resp.json()
    // 训练场里通关要记账（外层据此更新进度与云端同步）
    if (isTask && judgeResult.value && judgeResult.value.ok) {
      window.dispatchEvent(new CustomEvent('sl-task-passed', {
        detail: { id: props.caseData.id },
      }))
    }
  } catch (e) {
    if (e.message !== 'timeout') runError.value = String(e.message || e)
  }
}

onMounted(() => {
  // 用户读课程正文时就在后台把运行时下下来（约 9MB）。
  // 等他滚到练习区点「运行代码」，多半已经就绪，不用干等进度。
  setTimeout(() => {
    if (!worker && props.caseData) ensureWorker()
  }, 2500)
})

onBeforeUnmount(destroyWorker)
</script>

<template>
  <div v-if="caseData" class="codelab">
    <div class="codelab-head">
      <div>
        <h2><Terminal :size="18" /> {{ caseData.kind === 'task' ? '在线编写与运行' : '在线实练 · ' + caseData.title }}</h2>
        <p v-if="caseData.kind !== 'task'" class="sl-muted">{{ caseData.brief }}</p>
      </div>
      <span class="sl-tag primary"><ShieldCheck :size="13" /> 浏览器沙箱</span>
    </div>

    <div class="codelab-safety">
      <ShieldCheck :size="15" />
      <span>Web Worker 内运行，服务器不执行学员代码；网络仅允许访问本站 <code class="inline">/lab/</code> 靶场，禁止外域。</span>
    </div>

    <div class="codelab-body" :class="{ stacked: caseData.kind === 'task' }">
      <div class="codelab-editor">
        <div class="editor-bar">
          <span><Terminal :size="14" /> main.py</span>
          <button class="link-btn" @click="resetCode"><RotateCcw :size="13" /> 重置代码</button>
        </div>
        <div ref="editorEl" class="editor-host"></div>
      </div>

      <div class="codelab-side">
        <div class="side-block">
          <h3><Terminal :size="15" /> 运行输出</h3>
          <pre class="out" :class="{ 'out-err': !!runError }">{{ stdout || (runError || '点击「运行代码」查看输出') }}</pre>
          <div v-if="runError && stdout" class="sl-note no" style="margin-top:8px">
            <XCircle :size="15" /> <span>{{ runError }}</span>
          </div>
        </div>
        <div class="side-block">
          <h3><Lightbulb :size="15" /> 提示</h3>
          <button class="link-btn" @click="showHint = !showHint">
            {{ showHint ? '收起提示' : '查看提示' }}
          </button>
          <p v-if="showHint" class="hint">{{ caseData.hint }}</p>
        </div>
        <p v-if="answerSource" class="answer-src">{{ answerSource }}</p>
        <div v-if="judgeResult" class="sl-note" :class="judgeResult.ok ? 'ok' : 'no'">
          <component :is="judgeResult.ok ? CheckCircle2 : XCircle" :size="17" />
          <span><b>{{ judgeResult.ok ? '通过' : '未通过' }}：</b>{{ judgeResult.message }}
            <span v-if="!judgeResult.ok && judgeResult.hint"><br>提示：{{ judgeResult.hint }}</span>
          </span>
        </div>
      </div>
    </div>

    <div class="codelab-actions">
      <el-button :loading="running" @click="doRun(false)">
        <Play :size="15" /> 运行代码
      </el-button>
      <el-button type="primary" :loading="running" @click="doRun(true)">
        <Send :size="15" /> 运行并判分
      </el-button>
      <span class="status" :class="{ busy: loading || running }">
        <LoaderCircle v-if="loading || running" :size="14" class="spin" />
        {{ status || '沙箱待启动（进入本页后会自动预加载运行时）' }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.codelab { border: 1px solid var(--sl-line); background: #fff; margin: 18px 0; }
.codelab-head {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 14px;
  padding: 16px 20px; border-bottom: 1px solid var(--sl-line);
}
.codelab-head h2 { font-size: 16px; margin: 0 0 5px; display: flex; align-items: center; gap: 8px; }
.codelab-head p { margin: 0; font-size: 13.5px; }
.codelab-safety {
  display: flex; gap: 8px; align-items: flex-start;
  padding: 9px 20px; background: #f3f8ff; border-bottom: 1px solid var(--sl-line);
  font-size: 12.8px; color: #4a5a70;
}
.codelab-safety svg { flex: none; margin-top: 2px; }
.codelab-body { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(240px, 1fr); }
/* 训练场里整行宽度够用，改成上下布局：编辑器占满宽度 + 更高 */
.codelab-body.stacked { grid-template-columns: 1fr; }
.codelab-body.stacked .codelab-editor { border-right: 0; border-bottom: 1px solid var(--sl-line); }
.codelab-body.stacked .editor-host,
.codelab-body.stacked .editor-host :deep(.cm-editor) { min-height: 420px; }
.codelab-editor { border-right: 1px solid var(--sl-line); min-width: 0; }
.editor-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 7px 12px; background: #f2f5fa; border-bottom: 1px solid var(--sl-line);
  font-size: 12.5px; color: #4a5a70;
}
.editor-bar span { display: flex; align-items: center; gap: 6px; font-weight: 600; }
.link-btn { background: none; border: 0; color: var(--sl-blue); font-size: 12.5px; display: flex; align-items: center; gap: 5px; cursor: pointer; padding: 2px 4px; }
.link-btn:hover { text-decoration: underline; }
.editor-host { min-height: 320px; }
.editor-host :deep(.cm-editor) { min-height: 320px; outline: none; }
.codelab-side { padding: 14px 16px; min-width: 0; }
.side-block { margin-bottom: 16px; }
.side-block h3 { font-size: 13.5px; margin: 0 0 8px; display: flex; align-items: center; gap: 6px; }
.out {
  background: #f7f9fc; border: 1px solid var(--sl-line);
  padding: 10px 12px; margin: 0; min-height: 92px; max-height: 220px; overflow: auto;
  font: 12.5px/1.65 var(--sl-mono); color: #25344a; white-space: pre-wrap; word-break: break-all;
}
.out-err { border-left-color: var(--sl-red); color: var(--sl-red); }
.hint { font-size: 13px; color: var(--sl-body); background: var(--sl-amber-bg); border-left: 3px solid var(--sl-amber); padding: 9px 12px; margin: 8px 0 0; }
.answer-src { margin: 8px 0 0; font-size: 12.5px; line-height: 1.6; color: var(--sl-amber); }
.codelab-actions {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 13px 20px; border-top: 1px solid var(--sl-line); background: #fbfcfe;
}
.status { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--sl-muted); }
.status.busy { color: var(--sl-blue); }
.spin { animation: sl-spin 1s linear infinite; }
@keyframes sl-spin { to { transform: rotate(360deg); } }
@media (max-width: 900px) {
  .codelab-body { grid-template-columns: 1fr; }
  .codelab-editor { border-right: 0; border-bottom: 1px solid var(--sl-line); }
}
@media (max-width: 560px) {
  .codelab-head { flex-direction: column; gap: 10px; }
  .codelab-actions { flex-wrap: wrap; }
  .editor-host, .editor-host :deep(.cm-editor) { min-height: 260px; }
  .codelab-side { padding: 12px; }
}
</style>
