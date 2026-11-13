# -*- coding: utf-8 -*-
"""专项校验：CSP 下两个最容易静默失效的功能。

1) 主题切换按钮（原 onclick 被 CSP 拦，已改为事件委托）
2) 在线沙箱（Pyodide 需要 wasm 编译 + 动态 import + worker，任一项被拦就起不来）

这两处失效不会报错，只会"点了没反应"或"一直转圈"，所以必须实测。
"""
import sys
import time

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8097'


def main():
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append((m.type, m.text)))
        page.on('pageerror', lambda e: logs.append(('pageerror', str(e))))

        print('=== 1. 主题切换按钮（SSR 页，事件委托）===')
        page.goto(BASE + '/lab/books?page=1', wait_until='domcontentloaded', timeout=60000)
        before = page.evaluate("document.documentElement.getAttribute('data-theme')")
        page.click('[data-theme-toggle]')
        page.wait_for_timeout(600)
        after = page.evaluate("document.documentElement.getAttribute('data-theme')")
        print('  点击前 =', before, '-> 点击后 =', after)
        if before == after:
            problems.append('主题切换按钮点了没反应（事件委托未生效）')
        page.click('[data-theme-toggle]')
        page.wait_for_timeout(400)

        print('\n=== 2. 在线沙箱（Pyodide / wasm / worker）===')
        page.goto(BASE + '/#/courses/requests', wait_until='networkidle', timeout=60000)
        pyo = []
        page.on('response', lambda r: pyo.append((r.status, r.url)) if '/pyodide/' in r.url else None)
        page.on('requestfailed', lambda r: pyo.append(('FAIL', r.url)) if '/pyodide/' in r.url else None)
        try:
            page.wait_for_selector('.codelab', timeout=30000)
        except Exception:
            problems.append('课程页的 CodeLab 组件未出现')
            print('  CodeLab 未出现')
        else:
            print('  CodeLab 已渲染，等待预加载后点「运行代码」...')
            page.wait_for_timeout(3000)
            page.click('button:has-text("运行代码")')

            out = ''
            for i in range(70):
                page.wait_for_timeout(1000)
                try:
                    out = page.inner_text('pre.out')
                    st = page.inner_text('.status')
                except Exception:
                    out, st = '', ''
                if out and '点击「运行代码」' not in out:
                    break
                # 状态里出现失败关键字时立即停下，不必等满 70 秒
                if st and ('失败' in st or '超时' in st):
                    break
            preview = (out or '').strip().replace('\n', ' / ')[:160]
            print('  状态文本：', (st or '').strip()[:110])
            print('  运行输出：', preview if preview else '（空）')
            print('  Pyodide 资源：%d 个请求' % len(pyo))
            for code, url in pyo[:8]:
                print('    %-5s %s' % (code, url.split('/pyodide/')[-1]))
            if not preview or '点击「运行代码」' in preview:
                problems.append('沙箱没有产出结果（状态：%s）' % (st or '未知'))
            elif '沙箱启动失败' in preview or '超时' in preview:
                problems.append('沙箱启动失败：' + preview)

        print('\n=== 3. 控制台 ===')
        refused = [t for k, t in logs if 'Refused to' in (t or '')]
        errs = [t for k, t in logs if k in ('error', 'pageerror') and 'Refused to' not in (t or '')]
        if refused:
            print('  CSP 拦截 %d 条：' % len(refused))
            for t in refused[:8]:
                print('    -', t[:160])
            problems.append('CSP 拦截 %d 条' % len(refused))
        else:
            print('  无 CSP 拦截')
        if errs:
            print('  其他错误 %d 条：' % len(errs))
            for t in errs[:5]:
                print('    -', str(t)[:150])
        else:
            print('  无其他错误')

        ctx.close()
        browser.close()

    print('\n' + '=' * 52)
    if problems:
        print('发现问题 %d 项：' % len(problems))
        for x in problems:
            print('  [!]', x)
        return 1
    print('PASS：主题切换与在线沙箱在 CSP 下均正常')
    return 0


if __name__ == '__main__':
    sys.exit(main())
