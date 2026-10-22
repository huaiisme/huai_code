# MyST 增强扩展
## 1. colon_fence
### (1) 提示类指令
功能说明
用 ::: 替代反引号 ``` 来书写 MyST 指令（如提示框、代码块、表格等），视觉上更简洁，和普通代码块的反引号围栏区分度更高，避免语法混淆。
所有原本用 ````{指令名}`` 格式的指令，都可以替换为 :::{指令名}，结尾用 ::: 闭合。

:::{note}
这是普通提示框，用于补充说明、概念解释，语气平和。
:::

:::{warning}
这是警告提示框，用于标注风险点、踩坑提醒、操作禁忌。
:::

:::{tip}
这是技巧提示框，用于分享最佳实践、高效用法、冷门技巧。
:::

:::{danger}
这是危险提示框，用于标注不可逆操作、严重错误、安全风险。
:::

### (2)带参数的代码块指令
:::{code-block} python
:linenos:
:caption: 示例：Hello Sphinx
:emphasize-lines: 1

def hello():
    print("Hello, Huai Knowledge Base!")
    return True
:::

## 2. linkify
项目仓库地址：https://github.com/huaiisme/huai_code

联系邮箱：[406031496@qq.com](mailto:406031496@qq.com)

无需任何包裹，直接写纯文本网址即可自动变成可点击链接。

效果说明
仅识别完整格式的网址（带 http/https 协议）和标准邮箱格式
适合快速贴参考链接、仓库地址，不用额外排版
代码块、行内代码中的网址不会被转换

## 3. tasklist
功能说明
支持 GitHub 风格的复选框任务列表，用于待办清单、学习计划、项目进度管理，视觉上清晰直观。

#### 知识库迭代计划
- [x] 完成 Sphinx 基础搭建
- [x] 接入 MyST Markdown 解析
- [x] 完成 Docker 工具链优化
- [ ] 补充 Python 技术栈章节
- [ ] 增加自动驾驶感知模块笔记
  - [x] 完成 CenterPoint 原理笔记
  - [ ] 补充 BEV Fusion 实践记录
- [ ] 配置 GitHub Pages 自动部署

## 4. html_image
功能说明
允许在 Markdown 中直接使用 HTML <img> 标签渲染图片，不会被转义为纯文本。相比原生 Markdown 图片语法，可以更灵活地控制图片尺寸、对齐方式、边框、圆角等样式。

:::{figure} ../../../_static/images/demo.png
:alt: demo示意图
:width: 30%
:align: center
:class: img-bordered
:target: ../../../_static/images/demo.png
:name: fig-demo-1
demo示意图
:::
具体效果如 {numref}`fig-demo-1` 所示
:::{figure} ../../../_static/images/demo.png
:alt: demo示意图2
:width: 30%
:align: center
:class: img-bordered
:target: ../../../_static/images/demo.png
:name: fig-demo-2
demo示意图2
:::
具体效果如 {numref}`fig-demo-2` 所示

效果说明
支持所有 HTML 图片原生属性：width/height/align/alt/title
可通过 style 写内联样式，实现圆角、边框、阴影等自定义效果
适合对图片排版要求高的示意图、对比图


## 5. deflist
功能说明
支持「定义列表」（Definition List），用于术语解释、名词释义、参数说明，比普通无序列表结构更清晰，专业文档常用。

Sphinx
: 基于 Python 的专业文档生成工具，支持结构化输出 HTML、PDF、EPUB 等多种格式，是技术文档的工业级标准方案。

MyST Parser
: Sphinx 的 Markdown 解析扩展，兼容标准 CommonMark 语法，同时支持丰富的指令扩展，兼顾 Markdown 的简洁与 Sphinx 的专业能力。

Read the Docs 主题
:  Sphinx 生态最流行的文档主题，侧边栏导航+全文搜索+响应式布局，广泛用于开源项目文档。

## 6. attrs_block
功能说明
给块级元素（标题、段落、提示框、代码块、块级图片等）添加自定义属性，包括 id（锚点）、class（样式类）、style（内联样式）。
这是实现自定义排版、精准跳转的核心扩展。
补充：如果需要给行内元素（行内图片、行内代码、文字链接）加属性，可在 myst_enable_extensions 中补充开启 attrs_inline。

（1）给标题加自定义锚点
用于长文档内精准跳转，替代自动生成的英文锚点：

{#docker-optimize-guide}
### Docker 工具链优化指南

详细说明请参考：{ref}`docker-optimize-guide`


{.highlight-box}
这段文字会应用 custom.css 中 .highlight-box 类的样式。

:::{container} .highlight-box
测试文字：如果能看到这段文字，说明容器生成成功，是样式没生效；如果完全看不到，说明指令解析失败。
:::

<!-- :::{raw} html
<div class="highlight-box">
这是一段带蓝色左侧边框和浅蓝背景的高亮提示文字
</div>
:::


:::{raw} html
<div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 4px; margin: 16px 0;">
这是一段带蓝色左侧边框和浅蓝背景的高亮提示文字，适合重点内容强调。
</div>
::: -->


