/* SpiderLab 在线实练沙箱（Web Worker）。
 * 用户 Python 代码只在这个 Worker 的 Pyodide/WASM 环境里运行，
 * 不接触服务器进程、文件系统或外部网络。
 *
 * 安全策略：
 *  1) 网络白名单：只允许同站 /lab/、/robots.txt、/sitemap.xml；外域一律抛错。
 *  2) 浏览器禁设的请求头（Referer/Cookie/User-Agent）改写为 X-Sl-* 别名。
 *  3) 死循环：主线程看门狗 12 秒后 terminate() 整个 Worker（见 CodeLab.vue）。
 *  4) 每次运行使用全新 globals dict，stdout 截断 8KB。
 */

const ALLOWED_PATHS = ['/lab/', '/assets/', '/media/', '/robots.txt', '/sitemap.xml']
const HEADER_ALIAS = {
  'Referer': 'X-Sl-Referer',
  'Cookie': 'X-Sl-Cookie',
  'User-Agent': 'X-Sl-Ua',
  'Host': 'X-Sl-Host',
}
// 沙箱只允许请求本站靶场。用域名而不是 IP：课程里的示例代码统一走域名，
// 白名单也跟着对齐，学员照抄代码不会被拦。
const LOCAL_HOSTS = ['spider.skkk.uno', '127.0.0.1', 'localhost']

let pyodide = null
let initPromise = null

function checkUrl(raw) {
  let u
  try {
    u = new URL(String(raw), self.location.origin)
  } catch (e) {
    throw new Error('URL 不合法：' + raw)
  }
  // 课程示例里的绝对 BASE 重写到当前源，其余外域一律拒绝
  if (u.origin !== self.location.origin) {
    if (LOCAL_HOSTS.indexOf(u.hostname) >= 0) {
      u = new URL(u.pathname + u.search, self.location.origin)
    } else {
      throw new Error('安全限制：只能访问本站 /lab/ 靶场，禁止请求 ' + u.host)
    }
  }
  const p = u.pathname
  if (!ALLOWED_PATHS.some((x) => p === x || p.startsWith(x))) {
    throw new Error('安全限制：路径 ' + p + ' 不在允许范围（仅 /lab/、/media/、/robots.txt、/sitemap.xml、/assets/）')
  }
  // PAC 兜底；顺带 Ru 掉可能的 URL 里混进的 scheme 外链
  return u
}

// 同步 XHR 桥：Python shim 调它发请求，白名单在这里强制。
self._slRequest = function (method, url, headersJson, bodyStr) {
  const u = checkUrl(url)
  const xhr = new XMLHttpRequest()
  xhr.open(method, u.pathname + u.search, false)
  let headers = {}
  try { headers = JSON.parse(headersJson || '{}') } catch (e) { /* noop */ }
  for (const k of Object.keys(headers)) {
    const name = HEADER_ALIAS[k] || k
    try { xhr.setRequestHeader(name, String(headers[k])) } catch (e) { /* forbidden */ }
  }
  try {
    xhr.send(bodyStr == null ? null : String(bodyStr))
  } catch (e) {
    return JSON.stringify({ status: 0, text: '', error: String(e), cookies: '' })
  }
  return JSON.stringify({
    status: xhr.status,
    text: xhr.responseText || '',
    cookies: xhr.getResponseHeader('X-Sl-Set-Cookie') || '',
    error: '',
  })
}

// 注入到 Python 的极简 requests 兼容层（标准库 urllib.parse + JS 同步 XHR）。
// 学员写的 requests.get / Session / .json() 全部可用，真实 HTML 来自本站靶场。
const PY_PREAMBLE = String.raw`
import sys as _sl_sys, types as _sl_types, json as _sl_json
import io as _sl_io, traceback as _sl_tb
from urllib.parse import urlencode as _sl_urlencode, urlsplit as _sl_urlsplit
from js import _slRequest as _sl_jsreq
from js import location as _sl_location

BASE = str(_sl_location.origin)

class _ChiBuf(object):
    def __init__(self): self.parts = []
    def write(self, s):
        if len(''.join(self.parts)) < 16000: self.parts.append(str(s))
    def flush(self): pass
    def getvalue(self): return ''.join(self.parts)

class _ChiResponse(object):
    def __init__(self, raw, cookies):
        self.status_code = int(raw.get('status', 0))
        self.text = raw.get('text', '') or ''
        self.headers = {}
        self.cookies = cookies
        self._error = raw.get('error', '') or ''
        if self._error:
            raise RuntimeError(self._error)
    @property
    def content(self): return self.text.encode('utf-8')
    def json(self): return _sl_json.loads(self.text)
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('HTTP ' + str(self.status_code))
    def __repr__(self):
        return '<Response [%s]>' % self.status_code

class _ChiSession(object):
    def __init__(self):
        self.headers = {}
        self.cookies = {}
    def _url(self, url, params):
        u = str(url)
        if params:
            u += ('&' if '?' in u else '?') + _sl_urlencode(params)
        # 判断是否本站请求：按 hostname 匹配，不写死任何 IP
        _host = _sl_urlsplit(u).netloc.split(':')[0]
        if _host in ('spider.skkk.uno', '127.0.0.1', 'localhost'):
            u = BASE + _sl_urlsplit(u).path + ('?' + _sl_urlsplit(u).query if _sl_urlsplit(u).query else '')
        return u
    def _do(self, method, url, kw):
        url = self._url(url, kw.get('params'))
        hdrs = dict(self.headers)
        hdrs.update(kw.get('headers') or {})
        hdrs['X-Sl-Shim'] = '1'
        if self.cookies:
            hdrs['Cookie'] = '; '.join('%s=%s' % kv for kv in self.cookies.items())
        body = None
        if kw.get('json') is not None:
            body = _sl_json.dumps(kw['json'])
            hdrs['Content-Type'] = 'application/json'
        elif kw.get('data') is not None:
            body = _sl_urlencode(kw['data'])
            hdrs['Content-Type'] = 'application/x-www-form-urlencoded'
        raw = _sl_jsreq(method, url, _sl_json.dumps(hdrs), body)
        d = _sl_json.loads(str(raw))
        if d.get('cookies'):
            for part in d['cookies'].split(';'):
                if '=' in part:
                    k, v = part.strip().split('=', 1)
                    self.cookies[k] = v
        return _ChiResponse(d, self.cookies)
    def get(self, url, **kw): return self._do('GET', url, kw)
    def post(self, url, **kw): return self._do('POST', url, kw)
    def request(self, method, url, **kw): return self._do(method, url, kw)

class _ChiRequests(object):
    def __init__(self): self.Session = _ChiSession
    def get(self, url, **kw): return _ChiSession().get(url, **kw)
    def post(self, url, **kw): return _ChiSession().post(url, **kw)

_sl_mod = _sl_types.ModuleType('requests')
_sl_inst = _ChiRequests()
_sl_mod.get = _sl_inst.get
_sl_mod.post = _sl_inst.post
_sl_mod.Session = _ChiSession
_sl_mod.Response = _ChiResponse
_sl_sys.modules['requests'] = _sl_mod
`

// 把用户代码包在独立 globals + 受限 stdout 里；answer 变量序列化后回传。
const RUNNER = String.raw`
import sys as _r_sys, io as _r_io, json as _r_json, traceback as _r_tb
_r_ans = None
_r_err = ''
_r_buf = _ChiBuf()
_r_old = _r_sys.stdout
_r_sys.stdout = _r_buf
_r_g = {'__name__': '__main__', 'BASE': BASE}
try:
    exec(_SL_USER_CODE, _r_g)
    _r_ans = _r_g.get('answer')
except BaseException:
    _r_err = _r_tb.format_exc()[-5000:]
finally:
    _r_sys.stdout = _r_old
_r_r = {
    'answer': _r_json.dumps(_r_ans, ensure_ascii=False, default=str) if _r_ans is not None else None,
    'stdout': _r_buf.getvalue()[:8000],
    'error': _r_err,
}
_r_json.dumps(_r_r, ensure_ascii=False)
`

async function ensureInit() {
  if (initPromise) return initPromise
  initPromise = (async () => {
    self.postMessage({ type: 'status', message: '正在下载 Python 运行时（约 9 MB，首次较慢）...' })
    // Pyodide 314.x 只支持 module worker：用 ESM 入口动态加载，
    // importScripts 在 module worker 里不可用。
    // 用变量持有路径，避免 Rollup 在构建期尝试解析这个运行时 URL。
    const PYODIDE_ESM = '/pyodide/pyodide.mjs'
    const { loadPyodide } = await import(/* @vite-ignore */ PYODIDE_ESM)
    self.postMessage({ type: 'status', message: '正在编译 WASM 解释器（约 3-8 秒）...' })
    pyodide = await loadPyodide({ indexURL: '/pyodide/' })
    self.postMessage({ type: 'status', message: '正在载入 lxml / BeautifulSoup（约 2 MB）...' })
    await pyodide.loadPackage(['lxml', 'beautifulsoup4', 'cssselect'])
    pyodide.globals.set('_SL_WORKER_READY', true)
    pyodide.runPython(PY_PREAMBLE)
    self.postMessage({ type: 'ready' })
  })()
  return initPromise
}

self.onmessage = async (ev) => {
  const msg = ev.data || {}
  if (msg.type === 'init') {
    try { await ensureInit() } catch (e) { self.postMessage({ type: 'error', message: String(e) }) }
    return
  }
  if (msg.type !== 'run') return
  try {
    await ensureInit()
    self.postMessage({ type: 'status', message: '正在执行代码...' })
    pyodide.globals.set('_SL_USER_CODE', String(msg.code || ''))
    pyodide.globals.set('_SL_SAVED', true)
    const out = pyodide.runPython(RUNNER)
    self.postMessage({ type: 'done', id: msg.id, result: JSON.parse(String(out)) })
  } catch (e) {
    self.postMessage({ type: 'done', id: msg.id,
      result: { answer: null, stdout: '', error: String(e && e.message || e) } })
  }
}
