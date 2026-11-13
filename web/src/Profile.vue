<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  Calendar, Activity, Target, Award, Flame, Github, LogIn, CircleDot,
} from 'lucide-vue-next'

const props = defineProps({
  authUser: { type: Object, default: null },
  ghEnabled: { type: Boolean, default: false },
  tasks: { type: Object, default: () => ({}) },
  levels: { type: Array, default: () => [] },
  doneIds: { type: Array, default: () => [] },
})

const loading = ref(true)
const events = ref([])     // [{ item, day, ts }]
const doneSet = ref([])    // 已通关 id
const fromCloud = ref(false)
const studyMap = ref({})   // { '2026-11-13': 秒 }

function dayKey(d) {
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
}

function localDayFromISO(iso) {
  const t = Date.parse(iso)
  return Number.isNaN(t) ? '' : dayKey(new Date(t))
}

async function load() {
  loading.value = true
  try {
    if (props.authUser) {
      const r = await fetch('/api/profile')
      if (r.ok) {
        const d = await r.json()
        fromCloud.value = true
        doneSet.value = d.done || []
        studyMap.value = d.study || {}
        events.value = (d.events || []).map((e) => ({
          item: e.item,
          ts: e.ts,
          day: localDayFromISO(e.ts),
        }))
        loading.value = false
        return
      }
    }
    // 未登录（或云端不可用）：用本地记录
    fromCloud.value = false
    let raw = []
    try { raw = JSON.parse(localStorage.getItem('sl_events') || '[]') } catch (e) { raw = [] }
    events.value = raw.map((e) => ({ item: e.i, day: e.d, ts: new Date(e.t).toISOString() }))
    doneSet.value = props.doneIds.slice()
    try { studyMap.value = JSON.parse(localStorage.getItem('sl_study') || '{}') } catch (e) { studyMap.value = {} }
  } catch (e) {
    fromCloud.value = false
  }
  loading.value = false
}

onMounted(load)
watch(() => props.authUser, load)
watch(() => props.doneIds, (v) => {
  if (!fromCloud.value) doneSet.value = v.slice()
})

/* ---------------- 统计 ---------------- */
const titleOf = (id) => (props.tasks[id] || {}).title || id
const pointsOf = (id) => (props.tasks[id] || {}).points || 0

const totalPoints = computed(() =>
  doneSet.value.reduce((s, id) => s + pointsOf(id), 0))

const dayCount = computed(() => {
  const m = {}
  for (const e of events.value) {
    if (e.day) m[e.day] = (m[e.day] || 0) + 1
  }
  return m
})

const activeDays = computed(() => Object.keys(dayCount.value).length)

const totalSeconds = computed(() =>
  Object.values(studyMap.value).reduce((a, b) => a + (Number(b) || 0), 0))

function fmtDuration(sec) {
  const m = Math.round(sec / 60)
  if (m < 60) return m + ' 分'
  const h = m / 60
  return (h >= 10 ? Math.round(h) : h.toFixed(1)) + ' 时'
}

async function doLogout() {
  try { await fetch('/auth/logout', { method: 'POST' }) } catch (e) { /* noop */ }
  location.hash = '#/'
  location.reload()
}

const streak = computed(() => {
  const m = dayCount.value
  let n = 0
  const cur = new Date()
  cur.setHours(0, 0, 0, 0)
  // 今天没打卡不算断，从昨天开始找
  if (!m[dayKey(cur)]) cur.setDate(cur.getDate() - 1)
  for (;;) {
    if (m[dayKey(cur)]) { n += 1; cur.setDate(cur.getDate() - 1) } else break
  }
  return n
})

/* ---------------- 日历（最近 53 周） ---------------- */
const weeks = computed(() => {
  const map = dayCount.value
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const end = new Date(today)
  end.setDate(end.getDate() + (6 - today.getDay()))
  const cur = new Date(end)
  cur.setDate(cur.getDate() - 52 * 7 + 1)

  const out = []
  for (let w = 0; w < 53; w++) {
    const col = []
    for (let d = 0; d < 7; d++) {
      const key = dayKey(cur)
      const c = map[key] || 0
      col.push({
        key,
        c,
        future: cur.getTime() > today.getTime(),
        label: key + (c ? ' · ' + c + ' 关' : ' · 无记录')
          + (studyMap.value[key] ? ' · ' + Math.round(studyMap.value[key] / 60) + ' 分钟' : ''),
      })
      cur.setDate(cur.getDate() + 1)
    }
    out.push(col)
  }
  return out
})

const levelOf = (c) => (c === 0 ? 0 : c === 1 ? 1 : c <= 2 ? 2 : c <= 4 ? 3 : 4)

/* ---------------- 最近动态 ---------------- */
const recent = computed(() =>
  events.value
    .filter((e) => e.ts)
    .sort((a, b) => (a.ts < b.ts ? 1 : -1))
    .slice(0, 20))

function relDay(day) {
  if (!day) return ''
  const today = dayKey(new Date())
  const y = new Date(); y.setDate(y.getDate() - 1)
  if (day === today) return '今天'
  if (day === dayKey(y)) return '昨天'
  return day.slice(5)
}

/* ---------------- 分级进度 ---------------- */
const levelStats = computed(() =>
  props.levels.map((lv) => {
    const ids = lv.tasks || []
    const done = ids.filter((id) => doneSet.value.includes(id)).length
    return {
      code: lv.code,
      name: lv.name,
      done,
      total: ids.length,
      pct: ids.length ? Math.round((done / ids.length) * 100) : 0,
    }
  }))
</script>

<template>
  <div class="sl-page-head">
    <h1>我的</h1>
    <p>这里记录你的通关情况与每天的学习轨迹。登录后可跨设备同步。</p>
  </div>

  <div class="me-card">
    <img v-if="authUser && authUser.avatar" class="me-avatar" :src="authUser.avatar" alt="" />
    <div v-else class="me-avatar me-avatar-empty"><CircleDot :size="22" /></div>
    <div class="me-id">
      <b>{{ authUser ? (authUser.name || authUser.login) : '本地访客' }}</b>
      <span v-if="authUser" class="me-sub">
        <Github :size="12" /> {{ authUser.login }} ·
        {{ fromCloud ? '进度已同步到云端' : '同步中…' }}
      </span>
      <span v-else class="me-sub">
        进度只保存在这台设备。登录后可跨设备同步。
      </span>
    </div>
    <a v-if="!authUser && ghEnabled" class="me-login" href="/auth/github">
      <LogIn :size="14" /> 登录同步
    </a>
    <button v-else-if="authUser" class="me-login" @click="doLogout">退出登录</button>
  </div>

  <div class="me-stats">
    <div class="me-stat">
      <b>{{ doneSet.length }}</b>
      <small>已通关</small>
    </div>
    <div class="me-stat">
      <b>{{ totalPoints }}</b>
      <small>总积分</small>
    </div>
    <div class="me-stat">
      <b>{{ fmtDuration(totalSeconds) }}</b>
      <small>学习时长</small>
    </div>
    <div class="me-stat">
      <b>{{ streak }}</b>
      <small>连续天数</small>
    </div>
  </div>

  <div class="sl-card">
    <h2><Calendar :size="18" /> 学习轨迹</h2>
    <p class="sl-muted" style="margin:0 0 14px;font-size:13px">
      最近 12 个月每天通关的关卡数，颜色越深做得越多。
    </p>
    <div class="heat-scroll">
      <div class="heat">
        <div v-for="(col, wi) in weeks" :key="wi" class="heat-col">
          <i v-for="cell in col" :key="cell.key" class="heat-cell"
             :class="['lv' + levelOf(cell.c), { future: cell.future }]"
             :title="cell.label"></i>
        </div>
      </div>
    </div>
    <div class="heat-foot">
      <span class="sl-muted" style="font-size:12px">
        共 {{ activeDays }} 天有记录，{{ doneSet.length }} 关已通过
      </span>
      <span class="heat-legend">
        少
        <i class="heat-cell lv0"></i>
        <i class="heat-cell lv1"></i>
        <i class="heat-cell lv2"></i>
        <i class="heat-cell lv3"></i>
        <i class="heat-cell lv4"></i>
        多
      </span>
    </div>
  </div>

  <div class="sl-card">
    <h2><Target :size="18" /> 分级进度</h2>
    <div class="me-levels">
      <div v-for="lv in levelStats" :key="lv.code" class="me-level">
        <div class="me-level-top">
          <b>{{ lv.code }} {{ lv.name }}</b>
          <span>{{ lv.done }} / {{ lv.total }}</span>
        </div>
        <div class="me-bar"><i :style="{ width: lv.pct + '%' }"></i></div>
      </div>
    </div>
  </div>

  <div class="sl-card">
    <h2><Activity :size="18" /> 最近动态</h2>
    <div v-if="loading" class="sl-loading" style="padding:20px">加载中…</div>
    <ul v-else-if="recent.length" class="me-events">
      <li v-for="(e, i) in recent" :key="i">
        <span class="me-when">{{ relDay(e.day) }}</span>
        <span class="me-what">
          通关 <b>{{ e.item }}</b> {{ titleOf(e.item) }}
        </span>
        <span class="me-pt">+{{ pointsOf(e.item) }}</span>
      </li>
    </ul>
    <p v-else class="sl-muted" style="margin:0;font-size:13px">
      还没有通关记录。去训练场挑一关开始吧。
    </p>
  </div>
</template>

<style scoped>
.me-card {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 18px; margin: 16px 0;
  border: 1px solid var(--sl-line); background: var(--sl-surface);
}
.me-avatar { width: 46px; height: 46px; display: block; flex: none; border-radius: 50%; }
.me-avatar-empty {
  display: flex; align-items: center; justify-content: center;
  background: var(--sl-surface-2); color: var(--sl-muted);
}
.me-id { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.me-id b { font-size: 16px; color: var(--sl-navy); }
.me-sub {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12.5px; color: var(--sl-muted);
}
.me-login {
  margin-left: auto; display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; border: 1px solid var(--sl-line);
  background: none; cursor: pointer;
  font: inherit; font-size: 13px; font-weight: 600; color: var(--sl-blue);
}
.me-login:hover { border-color: var(--sl-blue); text-decoration: none; }

.me-stats {
  display: grid; grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--sl-line); background: var(--sl-surface); margin-bottom: 18px;
}
.me-stat { padding: 14px 18px; border-right: 1px solid var(--sl-line); }
.me-stat:last-child { border-right: 0; }
.me-stat b { display: block; font-size: 22px; color: var(--sl-navy); line-height: 1.2; }
.me-stat small { color: var(--sl-muted); font-size: 12.5px; }

.heat-scroll { overflow-x: auto; padding-bottom: 4px; }
.heat { display: flex; gap: 3px; width: max-content; }
.heat-col { display: flex; flex-direction: column; gap: 3px; }
.heat-cell {
  width: 11px; height: 11px; display: block;
  background: var(--sl-line); border-radius: 2px;
}
.heat-cell.lv1 { background: var(--sl-green); opacity: .3; }
.heat-cell.lv2 { background: var(--sl-green); opacity: .5; }
.heat-cell.lv3 { background: var(--sl-green); opacity: .75; }
.heat-cell.lv4 { background: var(--sl-green); opacity: 1; }
.heat-cell.future { opacity: .12; }
.heat-foot {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap; margin-top: 12px;
}
.heat-legend { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: var(--sl-muted); }
.heat-legend .heat-cell { width: 10px; height: 10px; }

.me-levels { display: grid; gap: 12px; }
.me-level-top {
  display: flex; align-items: baseline; justify-content: space-between;
  font-size: 13px; margin-bottom: 5px;
}
.me-level-top b { color: var(--sl-navy); font-weight: 600; }
.me-level-top span { color: var(--sl-muted); font-size: 12.5px; }
.me-bar { height: 6px; background: var(--sl-surface-2); }
.me-bar i { display: block; height: 100%; background: var(--sl-blue); transition: width .3s; }

.me-events { list-style: none; margin: 0; padding: 0; }
.me-events li {
  display: flex; align-items: baseline; gap: 12px;
  padding: 8px 0; border-bottom: 1px solid var(--sl-line); font-size: 13.5px;
}
.me-events li:last-child { border-bottom: 0; }
.me-when { flex: none; width: 46px; color: var(--sl-muted); font-size: 12.5px; }
.me-what { flex: 1; color: var(--sl-body); }
.me-what b { color: var(--sl-ink); font-family: var(--sl-mono); font-size: 12.5px; }
.me-pt { flex: none; color: var(--sl-green); font-size: 12.5px; font-weight: 600; }

@media (max-width: 560px) {
  .me-stats { grid-template-columns: repeat(2, 1fr); }
  .me-stat:nth-child(2) { border-right: 0; }
  .me-stat:nth-child(-n+2) { border-bottom: 1px solid var(--sl-line); }
  .me-card { flex-wrap: wrap; }
  .me-login { margin-left: 0; }
}
</style>
