# -*- coding: utf-8 -*-
"""本地端到端：把 20 课「在线实练」的起始代码真实跑一遍并判分。

在进程内启动新版服务，注入 BASE，用真实 requests/lxml/bs4 执行案例代码，
再走后端 judge_case 比对答案。用于上线前发现案例代码/答案不一致。
"""
import io
import json
import os
import sys
import threading
import traceback
from http.server import ThreadingHTTPServer
from pathlib import Path

# 脚本放在 tests/ 下，项目根目录是上一级
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'server'))
os.chdir(ROOT / 'server')

from app import Handler, judge_case, case_public  # noqa: E402
from cases import CASES  # noqa: E402

Handler.log_message = lambda self, *a: None
srv = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d' % PORT

passed, failed = [], []

for c in CASES:
    g = {'__name__': '__main__', 'BASE': BASE}
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    err = None
    ans = None
    try:
        exec(c['starter'], g)
        ans = g.get('answer')
    except BaseException:
        err = traceback.format_exc()
    finally:
        sys.stdout = old

    if err:
        failed.append((c['slug'], '代码异常: ' + err.strip().splitlines()[-1]))
        print('  FAIL %-22s 代码异常' % c['slug'])
        print('       ', err.strip().splitlines()[-1])
        continue
    if ans is None:
        failed.append((c['slug'], '未给 answer 赋值'))
        print('  FAIL %-22s 未给 answer 赋值' % c['slug'])
        continue

    payload = json.dumps(ans, ensure_ascii=False)
    res = judge_case(c['slug'], payload)
    if res['ok']:
        passed.append(c['slug'])
        print('  OK   %-22s %s' % (c['slug'], str(ans)[:52]))
    else:
        failed.append((c['slug'], res['message'] + ' / got=' + str(ans)[:80]))
        print('  FAIL %-22s %s' % (c['slug'], res['message']))
        print('       got:', str(ans)[:120])

# 接口层：案例列表不得泄露标准答案
pub = case_public(CASES[0])
api_ok = 'answer' not in pub and 'hint' in pub and 'starter' in pub
print('\n[cases API] 不含 answer:', api_ok)

srv.shutdown()
print('\n' + '=' * 56)
print('案例代码通过: %d / %d' % (len(passed), len(CASES)))
if failed:
    for slug, why in failed:
        print('  -', slug, why)
    sys.exit(1)
if not api_ok:
    sys.exit(1)
print('CASE SELFTEST OK')
