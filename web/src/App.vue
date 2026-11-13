<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import CodeLab from './CodeLab.vue'
import Profile from './Profile.vue'
import {
  Bug, BookOpen, Home, Server, Target, ShieldCheck, AlertTriangle, Map,
  ArrowRight, Code2, Layers, ListChecks, Trophy, Rocket, Braces, Boxes,
  Clock, ChevronRight, Info, List, ExternalLink, Flag, Send, Lightbulb,
  CheckCircle2, XCircle, Play, KeyRound, Network, RefreshCw, ScrollText,
  Scale, Eye, Route, Globe2, CircleHelp, Terminal,
  Moon, Sun, Github, Link2, User, BarChart3,
} from 'lucide-vue-next'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import xml from 'highlight.js/lib/languages/xml'
import bash from 'highlight.js/lib/languages/bash'
import jsonLang from 'highlight.js/lib/languages/json'
import javascript from 'highlight.js/lib/languages/javascript'
import cssLang from 'highlight.js/lib/languages/css'
import sql from 'highlight.js/lib/languages/sql'

;['python', 'xml', 'bash', 'json', 'javascript', 'css', 'sql'].forEach((name, i) => {
  hljs.registerLanguage(name, [python, xml, bash, jsonLang, javascript, cssLang, sql][i])
})

const escapeHtml = (s) => String(s || '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

function guessLang(s) {
  const t = String(s || '').trim()
  if (/^<(!DOCTYPE|html|div|table|body|script|head|article|blockquote)/i.test(t)) return 'xml'
  if (/^\s*[{[]/.test(t)) return 'json'
  if (/^(pip |scrapy |npm |apt |curl |python -m|python3 |GET |POST |HTTP\/1\.|#!)/.test(t)) return 'bash'
  return 'python'
}
const hl = (s) => {
  // robots.txt 这类纯配置文本不做语言高亮，只转义
  if (/^\s*User-agent:/i.test(String(s || ''))) return escapeHtml(s)
  try { return hljs.highlight(String(s || ''), { language: guessLang(s), ignoreIllegals: true }).value }
  catch (e) { return escapeHtml(s) }
}

/* 纯文本示例（同样走高亮） */
const SAMPLE_FIRST_REQUEST = `import requests
r = requests.get('https://spider.skkk.uno/lab/books?page=1', timeout=8)
print(r.status_code)   # 200
print(r.text[:200])    # HTML 源码里直接含书籍数据`
const ROBOTS_TEXT = `User-agent: *
Allow: /
Disallow: /api/check
Disallow: /api/check_case
Disallow: /lab/trap/
Disallow: /admin/
Crawl-delay: 0.5

User-agent: SpiderBond-Student
Allow: /lab/
Crawl-delay: 0.5

Sitemap: https://spider.skkk.uno/sitemap.xml`

/* ---------------- 路由（hash，服务端无需 fallback） ---------------- */
const hash = ref(location.hash.slice(1) || '/')
window.addEventListener('hashchange', () => {
  hash.value = location.hash.slice(1) || '/'
  window.scrollTo(0, 0)
})
const parts = computed(() => hash.value.split('/').filter(Boolean))
const view = computed(() => parts.value[0] || 'home')
const param = computed(() => parts.value[1] || '')
const go = (p) => { location.hash = '#' + p }

const BOND_LOGO = '/assets/bond-logo.svg'

const LICENSE_TEXT = `MIT License

Copyright (c) 2026 OpenBond Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.`

/* 第三方组件及其许可证，与 package.json / 运行时实际依赖一致。
   repo 指向官方仓库；lic 指向 SPDX 的许可证原文——用 SPDX 而不是各仓库里的
   LICENSE 文件，因为后者路径会随版本变动，SPDX 的链接长期稳定。
   Python 与 Pyodide 分成两行：前者是 PSF-2.0、后者是 MPL-2.0，许可证不同，
   合并成一行会让人误以为是一份许可。 */
const DEPS = [
  { name: 'Vue 3', use: '前端框架',
    repo: 'https://github.com/vuejs/core',
    lic: [{ t: 'MIT', u: 'https://spdx.org/licenses/MIT.html' }] },
  { name: 'Vite', use: '构建与开发服务器',
    repo: 'https://github.com/vitejs/vite',
    lic: [{ t: 'MIT', u: 'https://spdx.org/licenses/MIT.html' }] },
  { name: 'Element Plus', use: 'UI 组件库（按需引入）',
    repo: 'https://github.com/element-plus/element-plus',
    lic: [{ t: 'MIT', u: 'https://spdx.org/licenses/MIT.html' }] },
  { name: 'Bootstrap 5', use: '基础样式与栅格',
    repo: 'https://github.com/twbs/bootstrap',
    lic: [{ t: 'MIT', u: 'https://spdx.org/licenses/MIT.html' }] },
  { name: 'Lucide Icons', use: '全站图标',
    repo: 'https://github.com/lucide-icons/lucide',
    lic: [{ t: 'ISC', u: 'https://spdx.org/licenses/ISC.html' }] },
  { name: 'CodeMirror 6', use: '在线代码编辑器',
    repo: 'https://github.com/codemirror/dev',
    lic: [{ t: 'MIT', u: 'https://spdx.org/licenses/MIT.html' }] },
  { name: 'Pyodide', use: '浏览器内 Python 运行时',
    repo: 'https://github.com/pyodide/pyodide',
    lic: [{ t: 'MPL-2.0', u: 'https://spdx.org/licenses/MPL-2.0.html' }] },
  { name: 'CPython', use: 'Pyodide 承载的 Python 实现',
    repo: 'https://github.com/python/cpython',
    lic: [{ t: 'PSF-2.0', u: 'https://spdx.org/licenses/PSF-2.0.html' }] },
  { name: 'highlight.js', use: '静态代码块语法高亮',
    repo: 'https://github.com/highlightjs/highlight.js',
    lic: [{ t: 'BSD-3-Clause', u: 'https://spdx.org/licenses/BSD-3-Clause.html' }] },
  { name: 'lxml', use: 'HTML / XML 解析',
    repo: 'https://github.com/lxml/lxml',
    lic: [{ t: 'BSD-3-Clause', u: 'https://spdx.org/licenses/BSD-3-Clause.html' }] },
  { name: 'Beautiful Soup', use: 'HTML 解析',
    repo: 'https://code.launchpad.net/beautifulsoup',
    lic: [{ t: 'MIT', u: 'https://spdx.org/licenses/MIT.html' }] },
  { name: 'Nginx', use: '反向代理、gzip 与静态缓存',
    repo: 'https://github.com/nginx/nginx',
    lic: [{ t: 'BSD-2-Clause', u: 'https://spdx.org/licenses/BSD-2-Clause.html' }] },
]

const isAdmin = ref(false)       // 仅用于决定是否显示后台入口；真正的权限校验在后端

const navItems = [
  { key: 'home', label: '首页', href: '#/', icon: Home },
  { key: 'courses', label: '课程', href: '#/courses', icon: BookOpen },
  { key: 'labs', label: '示例靶站', href: '#/labs', icon: Server },
  { key: 'training', label: '训练场', href: '#/training', icon: Target },
  { key: 'compliance', label: '合规说明', href: '#/compliance', icon: ShieldCheck },
  { key: 'about', label: '关于', href: '#/about', icon: Info },
]

// 后台入口只对管理员出现。注意这是 UI 层的显隐，真正的校验在 /admin 路由里：
// 手动在地址栏输入 /admin 非管理员一样会被 403 拦下。
const navList = computed(() => {
  const list = navItems.slice()
  if (isAdmin.value) {
    list.push({ key: 'admin', label: '后台', href: '/admin', icon: BarChart3 })
  }
  return list
})

/* ---------------- 数据 ---------------- */
const courses = ref([])
const tracks = ref([])
const sites = ref([])
const levels = ref([])
const tasks = ref({})
const loaded = ref(false)
const loadError = ref('')
const courseFull = ref(null)
const caseData = ref(null)
const quizPicked = ref({})

/* 亮色 / 夜间模式 */
const isDark = ref(document.documentElement.getAttribute('data-theme') === 'dark')
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t)
  document.documentElement.classList.toggle('dark', t === 'dark')
  isDark.value = t === 'dark'
  try { localStorage.setItem('sl_theme', t) } catch (e) { /* noop */ }
}
const toggleTheme = () => applyTheme(isDark.value ? 'light' : 'dark')

async function getJSON(url) {
  const r = await fetch(url)
  if (!r.ok) throw new Error(url + ' -> ' + r.status)
  return r.json()
}

/* 视图标题：hash 路由对搜索引擎不可见，但至少要保证用户在标签页/收藏/分享时
   看到的是当前页面名，而不是全站同一个标题。 */
const VIEW_TITLES = {
  home: 'Spider Bond · Python 爬虫实训平台',
  courses: 'Python 爬虫课程目录 | Spider Bond',
  labs: '示例靶站 · 可合法抓取的练习站 | Spider Bond',
  training: '分级训练场 · 30 关实战 | Spider Bond',
  compliance: '爬虫合规说明 | Spider Bond',
  privacy: '隐私政策 | Spider Bond',
  about: '关于 Spider Bond',
  me: '我的学习记录 | Spider Bond',
}

watch([view, param], () => {
  let title = VIEW_TITLES[view.value] || VIEW_TITLES.home
  if (view.value === 'courses' && param.value) {
    const c = courses.value.find((x) => x.slug === param.value)
    if (c) title = `${c.title} · 第 ${c.no} 课 | Spider Bond`
  } else if (view.value === 'training' && param.value) {
    const t = tasks.value[param.value]
    if (t) title = `${param.value} ${t.title} · 实战关卡 | Spider Bond`
  }
  document.title = title

  // 同步 og:title / og:description，避免分享出去时还带着首页文案
  const ogTitle = document.querySelector('meta[property="og:title"]')
  if (ogTitle) ogTitle.setAttribute('content', title)
}, { immediate: true })

onMounted(async () => {
  try {
    const [c, t, s, lv] = await Promise.all([
      getJSON('/api/courses'), getJSON('/api/tracks'),
      getJSON('/api/labs'), getJSON('/api/levels'),
    ])
    courses.value = c
    tracks.value = t
    sites.value = s
    levels.value = lv.levels
    tasks.value = lv.tasks
    loaded.value = true
  } catch (e) {
    loadError.value = e.message
    loaded.value = true
  }

  // 账号状态：失败就静默降级为纯本地模式，不影响使用
  startStudyClock()
  await loadMe()
  if (authUser.value) await pullProgress()

  // 沙箱里通关后由 CodeLab 广播，这里记账并同步
  window.addEventListener('sl-task-passed', (e) => {
    const id = e.detail && e.detail.id
    if (!id || doneIds.value.includes(id)) return
    doneIds.value = [...doneIds.value, id]
    try { localStorage.setItem('sl_done', JSON.stringify(doneIds.value)) } catch (err) { /* noop */ }
    recordLocalEvent(id)
    pushProgress()
  })
  // 草稿变更：防抖后推云端
  window.addEventListener('sl-draft-saved', pushProgress)
})

watch([view, param], async () => {
  quizPicked.value = {}
  if (view.value === 'courses' && param.value) {
    courseFull.value = null
    caseData.value = null
    try { courseFull.value = await getJSON('/api/courses/' + param.value) }
    catch (e) { courseFull.value = null }
    try { caseData.value = await getJSON('/api/cases/' + param.value) }
    catch (e) { caseData.value = null }
  }
}, { immediate: true })

const prevCourse = computed(() => {
  const i = courses.value.findIndex((c) => c.slug === param.value)
  return i > 0 ? courses.value[i - 1] : null
})
const nextCourse = computed(() => {
  const i = courses.value.findIndex((c) => c.slug === param.value)
  return i >= 0 && i < courses.value.length - 1 ? courses.value[i + 1] : null
})
const pickQuiz = (qi, oi) => {
  if (quizPicked.value[qi] !== undefined) return
  quizPicked.value = { ...quizPicked.value, [qi]: oi }
}

const totalPoints = computed(() =>
  Object.values(tasks.value).reduce((s, t) => s + (t.points || 0), 0))
const doneIds = ref(JSON.parse(localStorage.getItem('sl_done') || '[]'))
const earnedPoints = computed(() =>
  doneIds.value.reduce((s, id) => s + ((tasks.value[id] || {}).points || 0), 0))
const passRate = computed(() =>
  totalPoints.value ? Math.round(earnedPoints.value / totalPoints.value * 100) : 0)

/* 学习时长：只统计「页面可见 + 2 分钟内有交互」的时间。
   挂着不动不算，避免把「打开页面」当学习。 */
const studyToday = ref(0)
let studyTimer = null
let lastTickAt = Date.now()
let lastActiveAt = Date.now()
let studyTicks = 0

function localDayKey(d) {
  const pad = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
}

function readStudy() {
  try { return JSON.parse(localStorage.getItem('sl_study') || '{}') } catch (e) { return {} }
}

function startStudyClock() {
  const k = localDayKey(new Date())
  studyToday.value = readStudy()[k] || 0
  lastTickAt = Date.now()
  const bump = () => { lastActiveAt = Date.now() }
  ;['mousemove', 'keydown', 'scroll', 'click', 'touchstart'].forEach((ev) =>
    window.addEventListener(ev, bump, { passive: true }))
  document.addEventListener('visibilitychange', () => { lastTickAt = Date.now() })

  studyTimer = setInterval(() => {
    const now = Date.now()
    if (document.visibilityState !== 'visible') { lastTickAt = now; return }
    if (now - lastActiveAt < 120000) {
      studyToday.value += (now - lastTickAt) / 1000
      try {
        const m = readStudy()
        m[localDayKey(new Date())] = Math.round(studyToday.value)
        localStorage.setItem('sl_study', JSON.stringify(m))
      } catch (e) { /* noop */ }
      studyTicks += 1
      if (studyTicks % 10 === 0) pushProgress()   // 约 5 分钟推一次
    }
    lastTickAt = now
  }, 30000)
}

/* 本地活动流水：未登录也能画出学习日历 */
function recordLocalEvent(item) {
  if (!item) return
  try {
    const d = new Date()
    const pad = (n) => String(n).padStart(2, '0')
    const today = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
    const evs = JSON.parse(localStorage.getItem('sl_events') || '[]')
    if (evs.some((e) => e.d === today && e.i === item)) return
    evs.push({ d: today, i: item, t: Date.now() })
    localStorage.setItem('sl_events', JSON.stringify(evs.slice(-1000)))
  } catch (e) { /* noop */ }
}

/* 账号与云端同步 ---------------- */
const ghEnabled = ref(false)     // 服务端是否配了 GitHub OAuth
const authUser = ref(null)       // { login, name, avatar } 或 null
let pushTimer = null

async function loadMe() {
  try {
    const r = await fetch('/api/me')
    if (!r.ok) return
    const d = await r.json()
    ghEnabled.value = !!d.enabled
    authUser.value = d.user || null
    isAdmin.value = !!d.is_admin
  } catch (e) { /* 后端不可达时静默降级为纯本地模式 */ }
}

/* 把本地进度和草稿推上去（首次登录、通关、改代码都会触发） */
function pushProgress() {
  if (!authUser.value) return
  clearTimeout(pushTimer)
  pushTimer = setTimeout(async () => {
    const drafts = {}
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i)
        if (k && k.startsWith('sl_code_')) drafts[k.slice(8)] = localStorage.getItem(k)
      }
    } catch (e) { /* 隐私模式 */ }

    const study = {}
    try {
      for (const [d, sec] of Object.entries(readStudy())) study[d] = sec
    } catch (e) { /* noop */ }

    try {
      await fetch('/api/progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ done: doneIds.value, drafts, study }),
      })
    } catch (e) { /* 同步失败不影响本地使用 */ }
  }, 1200)
}

/* 登录后拉云端进度，与本地取并集，再把结果回推 */
async function pullProgress() {
  if (!authUser.value) return
  try {
    const r = await fetch('/api/progress')
    if (!r.ok) return
    const d = await r.json()
    const merged = new Set(doneIds.value)
    for (const id of d.done || []) merged.add(id)
    doneIds.value = [...merged]
    try { localStorage.setItem('sl_done', JSON.stringify(doneIds.value)) } catch (e) { /* noop */ }
    // 云端有、本地没有的草稿回填（本地已有的不覆盖，保留当前设备上更新的内容）
    for (const [item, code] of Object.entries(d.drafts || {})) {
      const key = 'sl_code_' + item
      try {
        if (!localStorage.getItem(key)) localStorage.setItem(key, code)
      } catch (e) { /* noop */ }
    }
    pushProgress()
  } catch (e) { /* 忽略 */ }
}

async function logout() {
  try { await fetch('/auth/logout', { method: 'POST' }) } catch (e) { /* noop */ }
  authUser.value = null
}

/* ---------------- 训练场 ---------------- */
const activeLevel = ref('L1')
const activeTask = computed(() => param.value && tasks.value[param.value] ? param.value : '')

/* 把当前关卡包装成 CodeLab 需要的结构：在线写代码 → 运行 → 直接判分 */
const taskCase = computed(() => {
  const id = activeTask.value
  const t = id ? tasks.value[id] : null
  if (!t) return null
  return {
    kind: 'task',
    id,
    title: t.title,
    brief: t.goal,
    starter: t.starter || '',
    hint: t.hint || '',
    urls: [t.target],
    type: t.type,
  }
})
const answer = ref('')
const judgeResult = ref(null)
const judging = ref(false)
const showHint = ref(false)

watch(activeTask, (id) => {
  answer.value = ''
  judgeResult.value = null
  showHint.value = false
  if (id) activeLevel.value = (tasks.value[id] || {}).level || 'L1'
}, { immediate: true })

async function submit() {
  if (!activeTask.value || !answer.value.trim()) return
  judging.value = true
  try {
    const r = await fetch('/api/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: activeTask.value, answer: answer.value.trim() }),
    })
    judgeResult.value = await r.json()
    if (judgeResult.value.ok && !doneIds.value.includes(activeTask.value)) {
      doneIds.value = [...doneIds.value, activeTask.value]
      localStorage.setItem('sl_done', JSON.stringify(doneIds.value))
      recordLocalEvent(activeTask.value)
      pushProgress()
    }
  } catch (e) {
    judgeResult.value = { ok: false, message: '判分请求失败：' + e.message, hint: '' }
  }
  judging.value = false
}

function resetProgress() {
  doneIds.value = []
  localStorage.removeItem('sl_done')
  judgeResult.value = null
}

/* ---------------- 展示辅助 ---------------- */
const trackIcon = (name) => ({
  '基础篇': Rocket, '解析篇': Braces, '进阶篇': Layers, '工程篇': Boxes,
}[name] || BookOpen)
const levelIcon = (code) => ({
  L1: Play, L2: ListChecks, L3: KeyRound, L4: Network, L5: Trophy,
}[code] || Target)
const levelTag = (code) => ({
  L1: 'primary', L2: 'success', L3: 'warning', L4: 'danger', L5: 'dark',
}[code] || 'primary')
const levelType = (code) => ({
  L1: 'primary', L2: 'success', L3: 'warning', L4: 'danger', L5: 'info',
}[code] || 'primary')
const levelTasks = (code) =>
  (levels.value.find((l) => l.code === code) || { tasks: [] }).tasks
const byTrack = (name) => courses.value.filter((c) => c.track === name)
</script>

<template>
  <header class="sl-header">
    <div class="sl-nav">
      <a class="sl-brand" href="#/">
        <Bug :size="21" :stroke-width="2.2" /> Spider <i>Bond</i>
      </a>
      <nav class="sl-links">
        <a v-for="n in navList" :key="n.key" :href="n.href"
           :class="{ on: view === n.key }">
          <component :is="n.icon" :size="15" /> {{ n.label }}
        </a>
      </nav>
      <div class="sl-right">
        <a class="sl-auth" :class="{ on: authUser }" href="#/me"
           :title="authUser ? ('已登录 ' + authUser.login + '，查看我的主页') : '查看学习记录'">
          <img v-if="authUser && authUser.avatar" :src="authUser.avatar" alt="" width="18" height="18" />
          <Github v-else :size="14" />
          <span>{{ authUser ? authUser.login : '我的' }}</span>
        </a>
        <button class="theme-toggle" @click="toggleTheme"
                :title="isDark ? '切换到日间模式' : '切换到夜间模式'">
          <component :is="isDark ? Sun : Moon" :size="15" />
          <span>{{ isDark ? '日间' : '夜间' }}</span>
        </button>
        <a class="sl-org" href="https://bond.skkk.uno" target="_blank" rel="noopener"
           title="OpenBond Project · bond.skkk.uno">
          <!-- 用 v-bind 传字符串：静态 src 会被 Rollup 当成模块去解析并报错 -->
          <img class="brand-mark" :src="BOND_LOGO" alt="OpenBond" width="21" height="21" />
          <span>OpenBond</span>
        </a>
      </div>
    </div>
  </header>

  <main class="sl-main">
    <div v-if="loadError" class="sl-note no">
      <AlertTriangle :size="17" />
      <span>部分数据加载失败：{{ loadError }}。靶场页面仍可通过 <a href="/lab/">/lab/</a> 访问。</span>
    </div>

    <!-- ==================== 首页 ==================== -->
    <template v-if="view === 'home'">
      <section class="sl-hero">
        <h1>从第一行 requests 到完整爬虫项目</h1>
        <p>一套部署在真实服务器上的 Python 爬虫实训平台：系统化课程、可合法爬取的示例靶站、按难度分级的实战训练场，每一关都带自动判分。</p>
        <p>所有靶场均为服务端渲染，HTML 源码里就有数据，XPath / lxml / BeautifulSoup 练习不会被前端框架架空。</p>
        <div class="sl-hero-actions">
          <el-button class="hero-btn" @click="go('/courses')"><BookOpen :size="16" /> 开始学习</el-button>
          <el-button class="hero-btn ghost" @click="go('/training')"><Target :size="16" /> 进入训练场</el-button>
        </div>
        <div class="sl-hero-badges">
          <span><Code2 :size="13" /> {{ courses.length || 20 }} 门课程</span>
          <span><Server :size="13" /> {{ sites.length || 11 }} 个示例靶站</span>
          <span><Layers :size="13" /> {{ levels.length || 5 }} 级训练场</span>
          <span><ListChecks :size="13" /> {{ Object.keys(tasks).length || 20 }} 道实战关卡</span>
        </div>
      </section>

      <div class="sl-stats">
        <div class="sl-stat">
          <div class="ico-wrap"><BookOpen :size="19" /></div>
          <div><b>{{ courses.length || 20 }}</b><small>系统课程</small></div>
        </div>
        <div class="sl-stat">
          <div class="ico-wrap"><Server :size="19" /></div>
          <div><b>{{ sites.length || 11 }}</b><small>示例靶站</small></div>
        </div>
        <div class="sl-stat">
          <div class="ico-wrap"><Layers :size="19" /></div>
          <div><b>{{ levels.length || 5 }}</b><small>难度级别</small></div>
        </div>
        <div class="sl-stat">
          <div class="ico-wrap"><Trophy :size="19" /></div>
          <div><b>{{ totalPoints || 960 }}</b><small>可获积分</small></div>
        </div>
      </div>

      <div class="section-head">
        <h2><Map :size="18" /> 学习路径</h2>
        <a href="#/courses">查看全部课程 <ArrowRight :size="14" /></a>
      </div>
      <div class="sl-grid">
        <a v-for="t in tracks" :key="t.name" class="sl-tile" href="#/courses">
          <div class="tile-icon"><component :is="trackIcon(t.name)" :size="19" /></div>
          <h3>{{ t.name }} · {{ t.count }} 课</h3>
          <p>{{ t.desc }}</p>
        </a>
      </div>

      <div class="section-head">
        <h2><Layers :size="18" /> 五级训练场</h2>
        <a href="#/training">全部关卡 <ArrowRight :size="14" /></a>
      </div>
      <div class="sl-grid">
        <a v-for="lv in levels" :key="lv.code" class="sl-tile lv-card" :class="'lv-' + lv.code"
           :href="'#/training/' + lv.tasks[0]">
          <div class="lv-head">
            <h3><component :is="levelIcon(lv.code)" :size="17" /> {{ lv.code }} {{ lv.name }}</h3>
            <el-tag size="small" :type="levelType(lv.code)" effect="light">{{ lv.badge }}</el-tag>
          </div>
          <p>{{ lv.desc }}</p>
          <div class="tile-meta">
            <span v-for="s in lv.skills.slice(0, 3)" :key="s" class="sl-tag">{{ s }}</span>
          </div>
        </a>
      </div>

      <div class="sl-card" style="margin-top: 22px">
        <h2><Rocket :size="18" /> 三步开始</h2>
        <div class="sl-grid">
          <div>
            <h3><span class="course-no" style="display:inline-flex">1</span> 学课程</h3>
            <p class="sl-muted">从第 1 课合规底线开始，依次掌握 HTTP、XPath、lxml、BeautifulSoup、Session、Scrapy。</p>
          </div>
          <div>
            <h3><span class="course-no" style="display:inline-flex">2</span> 爬靶站</h3>
            <p class="sl-muted">{{ sites.length || 11 }} 个靶场全部服务端渲染，robots.txt 明确允许，不用怕把别人生产站打挂。</p>
          </div>
          <div>
            <h3><span class="course-no" style="display:inline-flex">3</span> 过关卡</h3>
            <p class="sl-muted">L1 到 L5 逐级闯关，提交答案即时判分，进度自动保存在本地浏览器。</p>
          </div>
        </div>
      </div>

      <div class="sl-note info">
        <ShieldCheck :size="17" />
        <span>本站所有 <code class="inline">/lab/</code> 靶场均为虚构演示数据，不含任何真实个人信息。
        练习时仍请遵守 <a href="/robots.txt">robots.txt</a> 的 Crawl-delay 与低频率要求。</span>
      </div>
    </template>

    <!-- ==================== 课程列表 ==================== -->
    <template v-else-if="view === 'courses' && !param">
      <div class="sl-page-head">
        <h1>课程目录</h1>
        <p>共 {{ courses.length }} 课，四个篇章覆盖 Python 爬虫全链路，每课均含可运行示例与实练任务。</p>
      </div>
      <div v-if="!loaded" class="sl-loading"><el-skeleton :rows="6" animated /></div>
      <template v-else>
        <template v-for="t in tracks" :key="t.name">
          <div class="track-title"><component :is="trackIcon(t.name)" :size="18" /> {{ t.name }}
            <el-tag size="small" effect="plain">{{ t.count }} 课</el-tag>
          </div>
          <a v-for="c in byTrack(t.name)" :key="c.slug" class="course-row"
             :href="'#/courses/' + c.slug">
            <div class="course-no">{{ c.no }}</div>
            <div class="c-main">
              <b>{{ c.title }}</b>
              <small>{{ c.summary }}</small>
            </div>
            <el-tag size="small" effect="plain">{{ c.level }}</el-tag>
            <span class="sl-muted" style="font-size:13px;white-space:nowrap">
              <Clock :size="13" style="vertical-align:-2px" /> {{ c.minutes }} 分钟
            </span>
            <ChevronRight :size="17" class="sl-muted" />
          </a>
        </template>
      </template>
    </template>

    <!-- ==================== 课程详情 ==================== -->
    <template v-else-if="view === 'courses' && param">
      <div class="sl-breadcrumb">
        <a href="#/courses">课程目录</a> <ChevronRight :size="13" />
        <span>{{ courseFull ? courseFull.title : '加载中' }}</span>
      </div>
      <div v-if="!courseFull" class="sl-loading"><el-skeleton :rows="8" animated /></div>
      <template v-else>
        <div class="lesson-head">
          <div class="lesson-no">第 {{ String(courseFull.no).padStart(2, '0') }} 课</div>
          <h1>{{ courseFull.title }}</h1>
          <div class="lesson-meta">
            <span class="sl-tag primary">{{ courseFull.track }}</span>
            <span class="sl-tag">{{ courseFull.level }}</span>
            <span class="sl-tag"><Clock :size="12" /> 约 {{ courseFull.minutes }} 分钟</span>
            <span class="sl-tag">{{ courseFull.section_count || 3 }} 节精讲</span>
            <span class="sl-tag"><Target :size="12" /> 1 个在线实练</span>
          </div>
        </div>

        <!-- 学习目标 -->
        <div class="lesson-objectives">
          <h2><Target :size="17" /> 学完这节课，你将能够</h2>
          <ol>
            <li v-for="(o, i) in courseFull.objectives" :key="i">{{ o }}</li>
          </ol>
        </div>

        <!-- 开场 + 类比 + 前置 -->
        <div class="lesson-intro">
          <div class="sl-card" style="margin:0">
            <h2><Info :size="18" /> 为什么学这个</h2>
            <p style="line-height:1.9;margin:0">{{ courseFull.intro }}</p>
          </div>
          <div class="sl-card" style="margin:0">
            <h2><Lightbulb :size="18" /> 打个比方</h2>
            <p style="line-height:1.9;margin:0">{{ courseFull.analogy }}</p>
            <div class="lesson-prereq">
              <b>前置知识：</b>
              <span v-for="(p, i) in courseFull.prereq" :key="i" class="sl-tag">{{ p }}</span>
            </div>
          </div>
        </div>

        <!-- 分节精讲 -->
        <div v-for="(s, si) in courseFull.sections" :key="si" class="lesson-section">
          <div class="lesson-section-head">
            <span class="lesson-section-no">{{ si + 1 }}</span>
            <h2>{{ s.title }}</h2>
          </div>
          <p class="lesson-text">{{ s.body }}</p>
          <ul v-if="s.bullets" class="lesson-bullets">
            <li v-for="(b, bi) in s.bullets" :key="bi">{{ b }}</li>
          </ul>
          <div v-if="s.example" class="lesson-example">
            <div class="lesson-example-label"><Code2 :size="13" /> 小例子</div>
            <pre class="sl-code"><code class="hljs" v-html="hl(s.example)"></code></pre>
          </div>
        </div>

        <!-- 跟我做 -->
        <div class="section-head" style="margin-top:30px">
          <h2><Play :size="18" /> 跟我做</h2>
        </div>
        <div v-for="(w, wi) in courseFull.walkthrough" :key="wi" class="lesson-step">
          <div class="lesson-step-head">
            <span class="lesson-step-no">STEP {{ wi + 1 }}</span>
            <b>{{ w.title }}</b>
          </div>
          <pre class="sl-code"><code class="hljs" v-html="hl(w.code)"></code></pre>
          <p class="lesson-explain"><Lightbulb :size="14" /> {{ w.explain }}</p>
        </div>

        <!-- 完整示例 / 知识点 / 常见坑 -->
        <div class="sl-card">
          <h2><Code2 :size="18" /> 完整示例代码</h2>
          <pre class="sl-code"><code class="hljs" v-html="hl(courseFull.code)"></code></pre>
        </div>
        <div class="sl-card">
          <h2><List :size="18" /> 本课知识点速查</h2>
          <ul class="lesson-bullets">
            <li v-for="(p, i) in courseFull.points" :key="i">{{ p }}</li>
          </ul>
        </div>
        <div class="sl-card">
          <h2><AlertTriangle :size="18" /> 常见坑</h2>
          <ul class="lesson-bullets">
            <li v-for="(p, i) in courseFull.pitfalls" :key="i">{{ p }}</li>
          </ul>
        </div>

        <!-- 在线实练 -->
        <div class="section-head" style="margin-top:30px">
          <h2><Terminal :size="18" /> 在线实练</h2>
        </div>
        <CodeLab v-if="caseData" :case-data="caseData" />
        <div v-else class="sl-loading">正在加载实练案例…</div>
        <div class="sl-note info">
          <Target :size="17" />
          <span><b>课后作业：</b>{{ courseFull.exercise }}
            <a :href="courseFull.lab" target="_blank" rel="noopener" style="margin-left:8px">
              {{ courseFull.lab_text }} <ExternalLink :size="13" style="vertical-align:-2px" />
            </a>
          </span>
        </div>

        <!-- 自测题 -->
        <div class="section-head" style="margin-top:30px">
          <h2><CircleHelp :size="18" /> 自测题</h2>
        </div>
        <div v-for="(q, qi) in courseFull.quiz" :key="qi" class="lesson-quiz">
          <div class="lesson-quiz-q">{{ qi + 1 }}. {{ q.q }}</div>
          <div class="lesson-quiz-opts">
            <button v-for="(o, oi) in q.options" :key="oi" class="quiz-opt"
                    :class="{
                      'picked': quizPicked[qi] === oi,
                      'right': quizPicked[qi] !== undefined && oi === q.answer,
                      'wrong': quizPicked[qi] === oi && oi !== q.answer
                    }"
                    @click="pickQuiz(qi, oi)">
              <span class="quiz-key">{{ String.fromCharCode(65 + oi) }}</span>{{ o }}
            </button>
          </div>
          <div v-if="quizPicked[qi] !== undefined" class="sl-note"
               :class="quizPicked[qi] === q.answer ? 'ok' : 'no'" style="margin:10px 0 0">
            <component :is="quizPicked[qi] === q.answer ? CheckCircle2 : XCircle" :size="16" />
            <span>{{ quizPicked[qi] === q.answer ? '回答正确。' : '再想想。' }}{{ q.explain }}</span>
          </div>
        </div>

        <!-- 小结 / 延伸 -->
        <div class="sl-card lesson-recap">
          <h2><CheckCircle2 :size="18" /> 本课小结</h2>
          <ol>
            <li v-for="(r, i) in courseFull.recap" :key="i">{{ r }}</li>
          </ol>
          <div class="lesson-further">
            <b>延伸阅读 / 下一课</b>
            <ul><li v-for="(f, i) in courseFull.further" :key="i">{{ f }}</li></ul>
          </div>
        </div>

        <div class="lesson-nav">
          <el-button v-if="prevCourse" @click="go('/courses/' + prevCourse.slug)">
            上一课：{{ prevCourse.title }}
          </el-button>
          <el-button v-if="nextCourse" type="primary" @click="go('/courses/' + nextCourse.slug)">
            下一课：{{ nextCourse.title }} <ArrowRight :size="14" />
          </el-button>
          <el-button v-else type="primary" @click="go('/training')">
            课程已学完，去训练场 <Target :size="14" />
          </el-button>
        </div>
      </template>
    </template>

    <!-- ==================== 靶站列表 ==================== -->
    <template v-else-if="view === 'labs'">
      <div class="sl-page-head">
        <h1>示例靶站</h1>
        <p>全部为服务端渲染、结构稳定的教学站点，已在 robots.txt 中明确允许抓取。请保持低频率访问。</p>
      </div>
      <div class="sl-note ok">
        <ShieldCheck :size="17" />
        <span><b>教学授权声明：</b>以下站点数据均为虚构演示数据，专为爬虫解析练习设计，
        可放心采集。查看 <a href="/robots.txt" target="_blank">robots.txt</a> 与
        <a href="/sitemap.xml" target="_blank">sitemap.xml</a>。</span>
      </div>
      <div class="sl-grid">
        <div v-for="s in sites" :key="s.path" class="sl-tile">
          <div class="lv-head">
            <h3><Server :size="17" /> {{ s.name }}</h3>
            <span class="sl-tag">{{ s.level }}</span>
          </div>
          <p>{{ s.desc }}</p>
          <div class="tile-meta">
            <span class="sl-tag"><Code2 :size="12" /> {{ s.tech }}</span>
            <span v-if="s.learn" class="sl-tag">练：{{ s.learn }}</span>
          </div>
          <div style="margin-top:14px">
            <a :href="s.path" target="_blank" rel="noopener">
              <el-button size="small" plain type="primary">进入靶站 <ExternalLink :size="13" /></el-button>
            </a>
          </div>
        </div>
      </div>
      <div class="sl-card" style="margin-top:18px">
        <h2><Braces :size="18" /> 第一个请求</h2>
        <pre class="sl-code"><code class="hljs" v-html="hl(SAMPLE_FIRST_REQUEST)"></code></pre>
      </div>
    </template>

    <!-- ==================== 训练场 ==================== -->
    <template v-else-if="view === 'training'">
      <div class="sl-page-head">
        <h1>分级训练场</h1>
        <p>五级 {{ Object.keys(tasks).length || 30 }} 关，在线写代码直接跑真实靶站，结果自动判分。</p>
      </div>

      <div class="sl-card" style="padding:14px 20px">
        <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
          <span style="font-size:14px;font-weight:600;color:var(--sl-navy);display:flex;align-items:center;gap:7px">
            <Trophy :size="17" /> 学习进度
          </span>
          <span class="sl-muted" style="font-size:13px">
            已通过 {{ doneIds.length }} / {{ Object.keys(tasks).length || 30 }} 关 ·
            {{ earnedPoints }} / {{ totalPoints || 960 }} 分
          </span>
          <el-button size="small" style="margin-left:auto" @click="resetProgress">
            <RefreshCw :size="13" /> 重置进度
          </el-button>
        </div>
        <el-progress :percentage="passRate" :stroke-width="8" :show-text="false" style="margin-top:12px" />
      </div>

      <div class="lv-tabs">
        <button v-for="lv in levels" :key="lv.code" class="lv-tab"
                :class="{ on: activeLevel === lv.code }" @click="activeLevel = lv.code">
          <component :is="levelIcon(lv.code)" :size="15" /> {{ lv.code }} {{ lv.name }}
        </button>
      </div>

      <template v-for="lv in levels" :key="lv.code">
        <div v-if="activeLevel === lv.code" class="lv-pane">
          <div class="lv-brief">
            <div class="lv-brief-head">
              <component :is="levelIcon(lv.code)" :size="16" />
              <b>{{ lv.code }} · {{ lv.name }}</b>
              <span class="lv-brief-count">{{ levelTasks(lv.code).length }} 关</span>
            </div>
            <p>{{ lv.desc }}</p>
            <div class="lv-brief-meta">
              <span><b>需要会：</b>{{ lv.need }}</span>
              <span><b>建议先学：</b>第 {{ (lv.courses || []).join('、') }} 课</span>
              <span><b>核心技能：</b>{{ lv.skills.join(' / ') }}</span>
            </div>
          </div>
          <!-- 关卡卡片网格：一眼看全本级所有题 -->
          <div class="task-grid">
            <button v-for="tid in levelTasks(lv.code)" :key="tid"
                    class="task-card"
                    :class="{ on: activeTask === tid, done: doneIds.includes(tid) }"
                    @click="go('/training/' + tid)">
              <span class="tc-top">
                <span class="tc-id">{{ tid }}</span>
                <CheckCircle2 v-if="doneIds.includes(tid)" :size="15" class="tc-done" />
              </span>
              <b class="tc-title">{{ tasks[tid] ? tasks[tid].title : tid }}</b>
              <span class="tc-foot">
                <span>{{ tasks[tid] ? tasks[tid].points : 0 }} 分</span>
                <span class="tc-go">开始 <ArrowRight :size="12" /></span>
              </span>
            </button>
          </div>

          <!-- 关卡详情：占满整行，编辑器拿到全部宽度 -->
          <div v-if="activeTask && tasks[activeTask]" class="task-full">
            <div class="task-full-head">
              <div>
                <h2><Flag :size="18" /> {{ activeTask }} · {{ tasks[activeTask].title }}</h2>
                <p class="sl-muted">{{ tasks[activeTask].skills.join(' / ') }} · {{ tasks[activeTask].points }} 分</p>
              </div>
              <button class="task-close" @click="go('/training')">
                <XCircle :size="15" /> 收起
              </button>
            </div>

            <div class="task-goal">
              <Target :size="16" />
              <span><b>目标</b>{{ tasks[activeTask].goal }}</span>
            </div>

            <div class="task-kv-row">
              <a class="task-kv" :href="tasks[activeTask].target" target="_blank" rel="noopener">
                <span class="k">靶站</span>
                <span class="v">{{ tasks[activeTask].target_text }} <ExternalLink :size="12" /></span>
              </a>
              <div class="task-kv">
                <span class="k">提交格式</span>
                <span class="v">{{ tasks[activeTask].format }}</span>
              </div>
              <div v-if="tasks[activeTask].spec" class="task-kv">
                <span class="k">字段规范</span>
                <span class="v"><code class="inline">{{ tasks[activeTask].spec }}</code></span>
              </div>
            </div>

            <!-- 在线沙箱：写代码 → 运行 → 取 answer → 自动判分 -->
            <div v-if="taskCase" class="task-sandbox">
              <CodeLab :case-data="taskCase" />
            </div>

            <!-- 沙箱打不开时的备用入口：手填答案 -->
            <details class="task-manual">
              <summary>沙箱打不开？手动填写答案</summary>
              <div class="task-manual-body">
                <el-input v-model="answer" type="textarea" :rows="3"
                          placeholder="在此粘贴你的答案，例如：甲,乙,丙 或 [1, 2, 3]" />
                <div style="margin-top:10px;display:flex;gap:10px;flex-wrap:wrap">
                  <el-button type="primary" :loading="judging" @click="submit">
                    <Send :size="15" /> {{ judging ? '判分中…' : '提交判分' }}
                  </el-button>
                  <el-button @click="showHint = !showHint">
                    <Lightbulb :size="15" /> {{ showHint ? '收起提示' : '查看提示' }}
                  </el-button>
                </div>
                <div v-if="judgeResult" class="sl-note" :class="judgeResult.ok ? 'ok' : 'no'" style="margin-top:14px">
                  <component :is="judgeResult.ok ? CheckCircle2 : XCircle" :size="18" />
                  <span><b>{{ judgeResult.ok ? '通过' : '未通过' }}：</b>{{ judgeResult.message }}
                    <span v-if="!judgeResult.ok && judgeResult.hint"><br>提示：{{ judgeResult.hint }}</span>
                  </span>
                </div>
                <div v-if="showHint" class="sl-note" style="margin-top:10px">
                  <Lightbulb :size="17" /> <span>{{ tasks[activeTask].hint }}</span>
                </div>
              </div>
            </details>
          </div>
        </div>
      </template>
    </template>

    <!-- ==================== 合规说明 ==================== -->
    <template v-else-if="view === 'me'">
      <Profile :auth-user="authUser" :gh-enabled="ghEnabled"
               :tasks="tasks" :levels="levels" :done-ids="doneIds" />
    </template>

    <template v-else-if="view === 'about'">
      <div class="sl-page-head">
        <h1>关于 Spider Bond</h1>
        <p>一个面向初学者的 Python 爬虫实训平台：20 门课程、11 个示例靶站、5 级 20 关训练场。
          每节课都能在浏览器里直接写代码、真实抓取靶站并在线判分。</p>
      </div>

      <div class="sl-card">
        <h2><Info :size="18" /> 为什么做这个</h2>
        <p>市面上的爬虫教程大多止步于「贴一段代码让你照着敲」。但爬虫是一门手艺，
          光看会了、动手就废。真正卡住新手的往往不是语法，而是这几件事：</p>
        <ul class="lesson-bullets">
          <li>不知道该抓什么，只能对着示例网站练，一换真实站点就无从下手</li>
          <li>环境配不起来，或者解析库的语法记住了却不知道什么时候该用哪个</li>
          <li>没有反馈，写完了也不知道对不对，没人告诉你哪儿错了</li>
        </ul>
        <p>所以这里的每节课都配了一个可运行的案例：起始代码已经写好骨架，
          你补完关键几行，点「运行代码」就能真实抓到本站靶站的数据，
          提交后由服务端比对答案。靶站是虚构数据，可以随便练，不会打扰任何人。</p>
      </div>

      <div class="sl-card">
        <h2><Link2 :size="18" /> 链接</h2>
        <div class="about-links">
          <a href="https://skkk.uno" target="_blank" rel="noopener">
            <Globe2 :size="16" /> 博客 skkk.uno <ExternalLink :size="13" />
          </a>
          <a href="https://bond.skkk.uno" target="_blank" rel="noopener">
            <Rocket :size="16" /> 关于 Bond Project <ExternalLink :size="13" />
          </a>
          <a href="https://github.com/OpenBond-Project" target="_blank" rel="noopener">
            <Github :size="16" /> GitHub · OpenBond Project <ExternalLink :size="13" />
          </a>
        </div>
        <p class="sl-muted" style="margin:14px 0 0;font-size:13px">
          发现问题、想补案例、或者想加一个靶站，欢迎在 GitHub 上提 issue。
        </p>
      </div>

      <div class="sl-card">
        <h2><Scale :size="18" /> 开源许可证</h2>
        <p>本项目以 <b>MIT</b> 许可证开源，版权归 OpenBond Project 所有。
          你可以自由使用、修改、分发，包括商业用途，只需保留版权声明与许可声明。
          软件按「原样」提供，不附带任何担保。</p>
        <details style="margin-top:12px">
          <summary style="cursor:pointer;font-weight:600">展开许可证全文</summary>
          <pre class="sl-code" style="margin-top:10px">{{ LICENSE_TEXT }}</pre>
        </details>
      </div>

      <div class="sl-card">
        <h2><Boxes :size="18" /> 第三方组件</h2>
        <p>本站构建在这些开源项目之上，各自遵循其原始许可证。</p>
        <details style="margin-top:8px">
          <summary style="cursor:pointer;font-weight:600">
            展开组件清单（{{ DEPS.length }} 项，含仓库与许可证链接）
          </summary>
          <table class="lab-table" style="margin-top:10px">
            <thead>
              <tr><th>组件</th><th>用途</th><th>许可证</th></tr>
            </thead>
            <tbody>
              <tr v-for="d in DEPS" :key="d.name">
                <td>
                  <a :href="d.repo" target="_blank" rel="noopener">{{ d.name }}</a>
                </td>
                <td>{{ d.use }}</td>
                <td>
                  <template v-for="(l, i) in d.lic" :key="l.t">
                    <a :href="l.u" target="_blank" rel="noopener">{{ l.t }}</a><span
                      v-if="i < d.lic.length - 1"> / </span>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
          <p class="sl-muted" style="font-size:12.5px;margin-top:8px">
            许可证链接指向 SPDX 的原文页面。本站自身以 MIT 许可证开源。
          </p>
        </details>
      </div>
    </template>

    <template v-else-if="view === 'privacy'">
      <h1>隐私政策</h1>
      <p class="sl-muted">最后更新：2026 年 11 月 13 日</p>

      <div class="sl-card">
        <h2><ShieldCheck :size="18" /> 一句话概括</h2>
        <p>本站不接入第三方统计工具，不售卖、不共享你的学习数据。
          不登录时，你的所有记录只存在你自己的浏览器里。</p>
      </div>

      <div class="sl-card">
        <h2>一、未登录时</h2>
        <p>不需要提供任何信息就能使用全部课程与训练场。数据存在浏览器 localStorage 里，
          <b>不会上传到服务器</b>：</p>
        <table class="lab-table">
          <thead><tr><th>键名</th><th>内容</th></tr></thead>
          <tbody>
            <tr><td><code class="inline">sl_done</code></td><td>已通关的关卡编号</td></tr>
            <tr><td><code class="inline">sl_code_*</code></td><td>每道题各自的代码草稿</td></tr>
            <tr><td><code class="inline">sl_study</code></td><td>每天的学习时长（秒）</td></tr>
            <tr><td><code class="inline">sl_events</code></td><td>通关事件流水，用于画学习日历</td></tr>
            <tr><td><code class="inline">sl_theme</code></td><td>日间 / 夜间模式偏好</td></tr>
          </tbody>
        </table>
        <p>清除浏览器数据即可彻底删除，本站没有任何副本。</p>
      </div>

      <div class="sl-card">
        <h2>二、使用 GitHub 登录时</h2>
        <p>登录是可选的。只有你主动点击登录，本站才会通过 GitHub OAuth 获取以下信息
          （权限范围仅为 <code class="inline">read:user</code>）：</p>
        <ul class="lesson-bullets">
          <li>GitHub 用户 ID（作为账号唯一标识）</li>
          <li>用户名、昵称</li>
          <li>头像地址</li>
        </ul>
        <p><b>不获取</b>邮箱、仓库、组织成员关系，也没有任何写入权限。</p>
        <p>这些信息与学习记录一起存放在本站服务器的数据库中，用于跨设备同步进度。
          同步内容包括：通关记录、代码草稿、每日学习时长、通关时间流水。</p>
      </div>

      <div class="sl-card">
        <h2>三、Cookie 清单</h2>
        <table class="lab-table">
          <thead><tr><th>名称</th><th>用途</th><th>时效</th><th>来源</th></tr></thead>
          <tbody>
            <tr><td><code class="inline">sl_sid</code></td>
              <td>登录会话标识（HttpOnly，脚本不可读）</td><td>30 天</td><td>本站</td></tr>
            <tr><td><code class="inline">sl_oauth_state</code></td>
              <td>GitHub 登录的 CSRF 防护</td><td>10 分钟</td><td>本站</td></tr>
            <tr><td><code class="inline">__cf_bm</code> 等</td>
              <td>CDN 的机器人识别与安全防护</td><td>短期</td><td>Cloudflare</td></tr>
          </tbody>
        </table>
        <p>本站自身不使用任何广告或统计类 Cookie。</p>
      </div>

      <div class="sl-card">
        <h2>四、广告</h2>
        <p>本站<b>目前未启用任何广告</b>，页面中不加载 Google AdSense 或其他广告网络的代码，
          也不存在广告相关的 Cookie。</p>
        <p>如果将来启用广告，本节会更新，并明确说明所用平台与 Cookie 用途。</p>
      </div>

      <div class="sl-card">
        <h2>五、服务器日志</h2>
        <p>为了排查故障和防御攻击，服务器会记录访问日志，包含 IP 地址、浏览器标识、
          请求路径与时间。日志不用于用户画像，也从不与账号关联分析，
          按系统的日志轮转策略定期清除（通常保留两周左右）。</p>
      </div>

      <div class="sl-card">
        <h2>六、第三方服务</h2>
        <table class="lab-table">
          <thead><tr><th>服务</th><th>用途</th><th>涉及数据</th></tr></thead>
          <tbody>
            <tr><td>Cloudflare</td><td>CDN 与安全防护</td><td>IP、访问日志</td></tr>
            <tr><td>GitHub</td><td>可选登录</td><td>用户 ID、用户名、头像</td></tr>
          </tbody>
        </table>
      </div>

      <div class="sl-card">
        <h2>七、数据删除</h2>
        <ul class="lesson-bullets">
          <li><b>清空浏览器数据</b>：删除本地全部记录；服务器上若有同步数据需另行处理</li>
          <li><b>退出登录</b>：只清除会话 Cookie，云端学习记录仍保留（便于下次登录恢复）</li>
          <li><b>彻底删除账号与全部云端数据</b>：发邮件到
            <a href="mailto:skkk_lovelove@outlook.com">skkk_lovelove@outlook.com</a>，
            说明你的 GitHub 用户名，7 个工作日内删除并回复确认</li>
        </ul>
      </div>

      <div class="sl-card">
        <h2>八、儿童与政策变更</h2>
        <p>本站面向具备基础编程能力的学习者，不针对 14 岁以下儿童设计，
          也不会主动收集儿童的个人信息。</p>
        <p>本政策如有变更，会直接更新本页并修改「最后更新」日期。</p>
      </div>
    </template>

    <template v-else-if="view === 'compliance'">
      <div class="sl-page-head">
        <h1>合规与爬取约定</h1>
        <p>写爬虫之前，先搞清楚哪些能爬、怎么爬才不越界。这是第 1 课，也是最重要的一课。</p>
      </div>
      <div class="sl-card">
        <h2><ScrollText :size="18" /> 本站 robots.txt</h2>
        <pre class="sl-code"><code class="hljs" v-html="hl(ROBOTS_TEXT)"></code></pre>
        <p style="margin-top:14px">
          <a href="/robots.txt" target="_blank">查看线上 robots.txt <ExternalLink :size="13" /></a>
        </p>
      </div>
      <div class="sl-grid">
        <div class="sl-tile">
          <div class="tile-icon"><Scale :size="19" /></div>
          <h3>只抓公开数据</h3>
          <p>不碰需要登录才能看的个人信息，不绕过权限校验，不抓取敏感数据。本站靶场为虚构数据，可放心练习。</p>
        </div>
        <div class="sl-tile">
          <div class="tile-icon"><Eye :size="19" /></div>
          <h3>标明身份</h3>
          <p>用带联系方式的 User-Agent，方便站长联系你。教学示例统一为 SpiderBond-Student/1.0。</p>
        </div>
        <div class="sl-tile">
          <div class="tile-icon"><Route :size="19" /></div>
          <h3>优雅退让</h3>
          <p>遇到 403 停止并告警，遇到 429 按 Retry-After 退避，5xx 有限重试，不硬闯。</p>
        </div>
        <div class="sl-tile">
          <div class="tile-icon"><Globe2 :size="19" /></div>
          <h3>遵守条款</h3>
          <p>遵守目标站服务条款、著作权与数据合规要求；商用前务必确认授权。</p>
        </div>
      </div>
      <div class="sl-note ok">
        <CheckCircle2 :size="17" />
        <span><b>本站靶场已明确授权：</b>所有 <code class="inline">/lab/</code> 页面为教学用途，
        在 robots.txt 中 Allow，数据结构稳定、内容虚构，是替代真实生产站练手的安全环境。</span>
      </div>
    </template>

    <!-- ==================== 404 ==================== -->
    <template v-else>
      <div class="sl-card" style="text-align:center;padding:50px">
        <CircleHelp :size="38" style="color:var(--sl-muted)" />
        <h2 style="justify-content:center;margin-top:14px">页面不存在</h2>
        <p class="sl-muted">检查一下地址，或返回首页。</p>
        <el-button type="primary" @click="go('/')"><Home :size="15" /> 返回首页</el-button>
      </div>
    </template>
  </main>

  <footer class="sl-footer">
    Spider Bond · 仅供教学演练 · 所有 /lab/ 靶场均已在 robots.txt 中允许爬取 ·
    请遵守 Crawl-delay 与合规要求 · <a href="#/about">关于与开源许可</a> ·
    <a href="#/privacy">隐私政策</a>
  </footer>
</template>
