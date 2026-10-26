# 从零出初稿（用脚本画 SVG，再出 PDF 和 PPTX）

画法和检查以 figgenie-paper-diagram 为主线，它工作流的第 1–7 步照走。这里只写本流程在它之上加的东西。

## 1. 门（前一道没过，不进下一道）

1. 用户确认 brief，包括待确认的假设（最多五条，每条写「我的理解 + 另一种可能」和出处）。假设写在 brief 文件里给他看；聊天里要他当场回答的问题最多三个，其余的他不改就按默认走。
2. 用户从候选参考图里挑 2–4 张。AI 家族的图用 `find_ai_exemplars.py search … sheet` 出带编号的拼图。用户挑多了，就当作整体的风格偏好。brief 和挑参考图可以放在同一条消息里请他看。
3. `claims_vs_code.md` 写完：图上画的，代码里都有（`references/content-sync.md` §1）。代码不在手边时，核不到的标「待核」，并告诉用户这道门只过了一部分。
4. 资料和图标要齐（`references/intake-and-materials.md`）。
5. 检查全过、图看过，再交给用户。

## 2. brief 里要多写的

- nature-figure 的图件契约五点：一句话结论、证据链（每个面板的证据角色）、原型（如 schematic-led composite）、后端（数据图用的绘图语言，按项目既定的）、出口要求（栏宽、文字可编辑、字体嵌入、无 Type 3，数值按 profile）。
- 还没定的设计画成中性标签（例如 `component X`），定了再改字。整个模块的设计都没定时，只画定下来的那一层（输入、输出、「decoder × L」这样的外形），里面不画细节，并在 brief 里列为待确认；或者先问要不要等定稿再画。
- 结果小图的数字一律用 `xx.x` 占位，柱高用一个占位值，脚本里留一个数字字典，数字冻结后从那里填。

## 3. 画图脚本

把 `$SK/templates/build_figure.py` 复制到 `<图目录>/tools/build_<图名>.py`，换掉里面的内容块。它是能直接跑的骨架：页面大小、字号、墨色、字体从 `figure.env` 读（环境变量 `FIG_PAGE`、`FIG_SIZES`、`FIG_INK`、`FIG_FONT`），`tex()` 排公式并量出盒子，`tw()` 量文字宽度，另有节点、边、图例的写法，一次生成 `fig.svg` 和 `spec.json`，SVG 里每个元素和 spec 里的条目一一对应（边的 SVG id 是 `e:` 加 spec 里的边 id）。骨架只覆盖最常见的写法；位图、容器、多个面板的写法看 figgenie 的 `references/spec-guide.md` §4 和参考图的 `source.svg`。

- 画布以 pt 为单位，`viewBox="0 0 W H"`；宽度、`meta.family`、`meta.venue` 或 `meta.venue_style`、`meta.column`、`width_pt` 都按 profile 的「版面」填。figgenie 没有这个会议或期刊时选最接近的，在 profile 里写明选了哪个；validator 关于宽度的提示是预期内的。
- Chromium 导出 PDF 时把页面取整到 CSS 像素（0.75 pt 的整数倍）：画布宽取 0.75 pt 的整数倍，否则页面尺寸会差到 0.37 pt，过不了审计的 0.3 pt 容差（例：240.25 pt 被导成 240.00 pt）。
- 根元素加 `text-rendering="geometricPrecision"`。不加的话，Chromium 导出 PDF 时按取整后的字宽排版：常规体比字体本身窄约 9%，粗体宽约 11%，放大后字母忽松忽紧。骨架里已经加了。
- 字体、字号、字色都从 profile 的「画法约定」来，不要自己定。字体键是 `arial` 时：SVG 路线的 PDF 里嵌的是 Arimo（Arial 的度量兼容字体），pptx 路线的 PDF 里是 Arial。
- 公式：`latex_math.typeset([(tex, size)])` 返回字形路径和盒子尺寸，画成 `<g data-symbol="latex" data-tex data-w data-h data-d transform="translate(x y)">`（y 是基线）。`LATEX_CACHE` 缓存排过的公式（骨架默认放在 `tools/latex_cache.json`）。不用 figgenie 的 MathJax（`tex_fill.py`）：LaTeX 在 7 pt 用 cmmi7，上下标用 cmmi5，比 MathJax 把 10 pt 字形按比例缩小宽 15–20%，笔画也粗一些，而且和正文的公式一样（正文用 Computer Modern 时）。数学字体默认 Computer Modern；论文的数学字体是别的（例如 acmart 的 Libertine）就在 `figure.env` 里设 `LATEX_PREAMBLE`。数学字号比旁边的标签大一档（Computer Modern 的 x 高比 Arial 低约 17%：例如 6 pt 的标签旁边用 7 pt 的公式），具体搭配记在 profile 里；只允许两种字号时，数学就用同一档，并让 `latex_check.py` 量一下。
- 位图：用相对路径指向 `assets/`，交付时由 `embed_fonts.py` 内嵌进 SVG。

## 4. 一条命令

```bash
bash $SK/scripts/make_draft.sh <图目录>                 # 图目录里只有一个 tools/build_*.py；否则加 --build tools/build_<图名>.py
```

读 `<图目录>/figure.env`（要有 `FIG_PAGE` 和 `FIG_SIZES`），依次做下面这些，每一步都打印一个标题；标 must 的失败就停，其余的报告后继续，最后列出失败的步骤：

| 步骤 | 做什么 | |
|---|---|---|
| build | 跑 `tools/build_*.py`，写 `fig.svg`、`spec.json` | must |
| spec_validate | figgenie 的 `spec_validate.py` | must |
| latex_check | 公式有没有出框、压字（figgenie 的 lint 不量公式） | |
| lint | figgenie 的 `check.py`：0 错误；警告逐条判断 | must |
| embed_fonts | `embed_fonts.py`：字体内嵌、位图内联 | must |
| export_pdf、pdf_clean | Chromium 导出 PDF，再清空 Creator / Producer | must |
| render_png | 300 dpi 的 PNG | must |
| pdf_text | PDF 里每段文字的宽度和字体本身的比（竖排文字报的大偏差是误报） | |
| svg2pptx、strip_style | 出 pptx（`--latin` 取 `FIG_LATIN`，默认 Arial），去掉主题阴影引用 | must |
| pptx_check | svg2pptx 有没有丢东西、盖住东西 | |
| lo_check | LibreOffice 打开后的样子（`qa/lo_check.png`） | |
| audit | `audit_outputs.py`，参数来自 `figure.env` | must |
| qa_sheets | 灰度与色弱对照图 | |

- 必须加 `--latin`（脚本已经加了）：不加的话 svg2pptx 按本机装了什么字体来挑，会挑到 Windows 上没有的 Tinos。
- `audit_outputs.py --svg` 会删掉 `embed_fonts.py` 留在 SVG 里的工具注释；交出 SVG 之前必须删（脚本的 audit 步骤做了）。
- pptx 里的公式是自由形状（svg2pptx 出 OMML 公式要 Microsoft Word 带的转换样式表，没有它就出不了；本 skill 的公式一律是自由形状）。编辑软件里显示和 PDF 一样，但不能当文字编辑，要告诉用户。
- 跑完先看 `fig.final.png` 和 `qa/lo_check.png`，再按 `render-and-audit.md` §3 逐条看。

## 5. 交给用户之后

- 复制到交付目录，用这张图的前缀（profile 的「文件放哪」）：`<前缀>.v1.pptx`、`.pdf`、`.png`，加一张和上一版的对照图。这一阶段 SVG 是主文件，PDF 交 Chromium 从 SVG 导出的 `fig.final.pdf`；pptx 成为主文件以后，才改交 LibreOffice 从 pptx 渲的 PDF。同时存一份到 `<图目录>/v1/`，连同 spec、brief、plan（figgenie 工作流第 4 步写的画图计划）和脚本。
- 用户在编辑软件里改过之后，pptx 就成了主文件，后面按 `references/iterate-on-saved-pptx.md` 走。要跟用户说清楚：脚本停在最后一版脚本稿。
- 用户以后想回到脚本：先用 `pptx_user_edits.py` 列出他的手改和各版补丁加的东西，全部并回脚本，再重画，对比到只剩有意的差别为止。
