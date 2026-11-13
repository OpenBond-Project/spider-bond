# -*- coding: utf-8 -*-
"""用真实 Chromium 校验 CSP 没有打断站点功能。

CSP 最容易出的事故不是"被绕过"，而是写太严把功能打死：
主题脚本被拦 → 夜间模式闪白；动态 import 被拦 → 沙箱起不来；
内联样式被拦 → Element Plus 组件错位。这些都不会报 500，只会静默失效。
"""
import sys
import time

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8099'


def main():
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()

        logs = []
        page.on('console', lambda m: logs.append((m.type, m.text)))
        page.on('pageerror', lambda e: logs.append(('pageerror', str(e))))

        print('=== 1. 首页 ===')
        page.goto(BASE + '/', wait_until='networkidle', timeout=60000)
        theme = page.evaluate("document.documentElement.getAttribute('data-theme')")
        app_kids = page.evaluate("document.querySelector('#app') ? document.querySelector('#app').children.length : -1")
        print('  data-theme =', theme)
        print('  #app 子节点数 =', app_kids)
        if not theme:
            problems.append('主题脚本被 CSP 拦掉（data-theme 为空）→ 夜间模式会闪白')
        if app_kids <= 0:
            problems.append('Vue 未挂载（#app 无子节点）')

        print('\n=== 2. 课程详情（CodeMirror 编辑器）===')
        page.goto(BASE + '/#/courses/requests', wait_until='networkidle', timeout=60000)
        try:
            page.wait_for_selector('.cm-editor', timeout=25000)
            cm = True
        except Exception:
            cm = False
        print('  .cm-editor 存在 =', cm)
        if not cm:
            problems.append('CodeMirror 编辑器未渲染（可能 style-src 或脚本被拦）')

        print('\n=== 3. 训练场（Element Plus 组件）===')
        page.goto(BASE + '/#/training', wait_until='networkidle', timeout=60000)
        try:
            page.wait_for_selector('.task-card', timeout=25000)
        except Exception:
            pass
        cards = page.query_selector_all('.task-card')
        print('  关卡卡片数 =', len(cards))
        if len(cards) == 0:
            problems.append('训练场卡片未渲染')

        print('\n=== 4. 靶场页（SSR）===')
        page.goto(BASE + '/lab/books?page=1', wait_until='domcontentloaded', timeout=60000)
        books = page.query_selector_all('.book')
        print('  书籍条目数 =', len(books))
        if len(books) == 0:
            problems.append('靶场页内容未渲染')

        print('\n=== 5. 控制台异常 ===')
        refused = [t for k, t in logs if 'Refused to' in (t or '')]
        errors = [(k, t) for k, t in logs if k in ('error', 'pageerror')]
        if refused:
            print('  CSP 拦截 %d 条：' % len(refused))
            for t in refused[:6]:
                print('    -', t[:150])
            problems.append('存在 CSP 拦截，共 %d 条' % len(refused))
        else:
            print('  无 CSP 拦截')
        others = [t for k, t in errors if 'Refused to' not in (t or '')]
        if others:
            print('  其他错误 %d 条：' % len(others))
            for t in others[:4]:
                print('    -', str(t)[:130])
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
    print('PASS：CSP 未打断任何功能')
    return 0


if __name__ == '__main__':
    sys.exit(main())
