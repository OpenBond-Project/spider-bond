# -*- coding: utf-8 -*-
"""验证浏览器沙箱内的 Python shim 逻辑（直接从 codelab.worker.js 提取，保持同步）。

把 `from js import ...` 的 JS 桥接替换成本地等价实现，
其余代码一字不改，跑完 20 个案例并判分。
"""
import io
import json
import os
import re
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

# 脚本放在 tests/ 下，项目根目录是上一级
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'server'))
os.chdir(ROOT / 'server')

from app import Handler, judge_case  # noqa: E402
from cases import CASES  # noqa: E402

Handler.log_message = lambda self, *a: None
srv = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d' % PORT

worker_src = (ROOT / 'web' / 'src' / 'codelab.worker.js').read_text(encoding='utf-8')
preamble = re.search(r'const PY_PREAMBLE = String\.raw`(.*?)`', worker_src, re.S).group(1)
runner = re.search(r'const RUNNER = String\.raw`(.*?)`', worker_src, re.S).group(1)

preamble = re.sub(r'^from js import _slRequest as _sl_jsreq$',
                  '_sl_jsreq = _SL_LOCAL_REQ', preamble, flags=re.M)
preamble = re.sub(r'^from js import location as _sl_location$',
                  '_sl_location = _SL_LOCAL_LOC', preamble, flags=re.M)
if '_SL_LOCAL_REQ' not in preamble or '_SL_LOCAL_LOC' not in preamble:
    sys.exit('无法替换 JS 桥接，检查 worker 源码')


class _Loc:
    origin = BASE


def local_req(method, url, headers_json, body_str):
    hdrs = json.loads(headers_json or '{}')
    data = str(body_str).encode('utf-8') if body_str is not None else None
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.dumps({
                'status': r.status,
                'text': r.read().decode('utf-8', 'ignore'),
                'cookies': r.headers.get('X-Sl-Set-Cookie') or '',
                'error': '',
            })
    except urllib.error.HTTPError as e:
        return json.dumps({
            'status': e.code,
            'text': e.read().decode('utf-8', 'ignore'),
            'cookies': e.headers.get('X-Sl-Set-Cookie') or '',
            'error': '',
        })


runner = runner + '\n_SL_FINAL = _r_json.dumps(_r_r, ensure_ascii=False)\n'

passed, failed = [], []
for c in CASES:
    g = {'_SL_LOCAL_REQ': local_req, '_SL_LOCAL_LOC': _Loc()}
    old = sys.stdout
    try:
        exec(preamble, g)
        g['_SL_USER_CODE'] = c['starter']
        exec(runner, g)
        final = json.loads(g['_SL_FINAL'])
    except BaseException as ex:
        failed.append((c['slug'], 'shim 异常: ' + repr(ex)))
        print('  FAIL %-22s shim 异常 %r' % (c['slug'], ex))
        sys.stdout = old
        continue
    finally:
        sys.stdout = old

    if final.get('error'):
        failed.append((c['slug'], '用户代码异常: ' + final['error'].strip().splitlines()[-1]))
        print('  FAIL %-22s 用户代码异常' % c['slug'])
        print('       ', final['error'].strip().splitlines()[-1])
        continue
    answer_json = final.get('answer')
    if answer_json is None:
        failed.append((c['slug'], '未给 answer 赋值'))
        print('  FAIL %-22s 未给 answer 赋值' % c['slug'])
        continue
    res = judge_case(c['slug'], answer_json)
    if res['ok']:
        passed.append(c['slug'])
        print('  OK   %-22s stdout=%d B' % (c['slug'], len(final.get('stdout', ''))))
    else:
        failed.append((c['slug'], res['message'] + ' got=' + answer_json[:90]))
        print('  FAIL %-22s %s' % (c['slug'], res['message']))
        print('       got:', answer_json[:130])

srv.shutdown()
print('\n' + '=' * 56)
print('沙箱 shim 通过: %d / %d' % (len(passed), len(CASES)))
if failed:
    for slug, why in failed:
        print('  -', slug, why)
    sys.exit(1)
print('SHIM SELFTEST OK')
