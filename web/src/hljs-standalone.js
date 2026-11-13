/* 供服务端渲染页面（靶场 / 兜底课程页）使用的独立高亮脚本。
 * 打包成 IIFE 后放到 /assets/highlight.js，页面无框架也能高亮代码块。
 * 使用 highlight.js/lib/common：覆盖 Python / XML / Bash / JSON / JS / CSS / SQL 等常用语言。
 */
import hljs from 'highlight.js/lib/common'

window.hljs = hljs

window.slHighlightAll = function () {
  document.querySelectorAll('pre code, pre.sl-code, pre.lab-code').forEach(function (block) {
    if (block.dataset && block.dataset.highlighted) return
    var target = block.tagName === 'CODE' ? block : block
    if (block.tagName !== 'CODE' && block.querySelector('code')) target = block.querySelector('code')
    var text = target.textContent
    try {
      target.innerHTML = hljs.highlightAuto(text).value
      target.classList.add('hljs')
      target.dataset.highlighted = '1'
    } catch (e) {
      /* 高亮失败保留原文 */
    }
  })
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', window.slHighlightAll)
} else {
  window.slHighlightAll()
}
