# 和其他 skills 的配合

本 skill 管流程和工具：画法用 figgenie-paper-diagram，论文的说法和数字以论文自己的写作指南为准（项目里有的话），图件契约和数据图的规范来自 nature-figure。规则冲突时：论文的说法、数字听写作指南；版面、配色、字号听本 skill 和这篇论文的 profile（它已经把 figgenie、nature-figure 的规则和用户的要求合在一起）。

## 这些 skill 在哪、能不能调用

每台机器不一样。先看会话的 skill 列表；列表里没有的，在 `~/.claude/skills`、`~/.codex/skills`、`~/.agents/skills` 和项目的 `.claude/skills`、`.agents/skills` 里找。能调用的就调用；装了但不能直接调用的，直接读它的文件。`make_from_saved.sh --check` 会报告 figgenie 的 scripts 目录找没找到（也可以用环境变量 `FIGGENIE_SCRIPTS` 指定）。

没有 figgenie 时：从零出初稿这条路走不了，`K.formula`、`tw()` 和不给 `w=` 的 `K.text_box` 也不能用（它们要 figgenie 的 `svg2pptx.py` 和 `measure_text.py`）；在已有 pptx 上改形状、出图、检查照常。

## figgenie-paper-diagram

用在：出初稿全程；迭代时量文字宽度、挑颜色、找部件。

| 步骤 | 用它的什么 |
|---|---|
| brief | `references/brief-template.md`（AI 家族那一节）；用 `references/ai/kinds.md`、`domains.md` 定图的种类和领域 |
| 参考图 | `scripts/find_ai_exemplars.py search … → sheet → files`：出带编号的拼图，让用户挑 2–4 张（这是一道门），再逐张看 `print.webp`、`source.svg`。系统类的图用 `find_exemplars.py`；整个模型的图看 `references/ai/model-architectures.md` |
| 版式、配色、编码 | `references/ai/layouts.md`、`ai/palettes.md`、`palettes.json`（配色方案的名字写进 spec 的 `meta.palette`）、`ai/encoding.md` |
| 部件 | `assets/symbols/`（`index.json`、`catalog-*.png`）：`original` 的可以直接用，`corpus` 的只作参考 |
| 量字、放字 | `scripts/measure_text.py`、`place_text.py`（`pptx_kit.tw` 调的就是它） |
| 检查 | `spec_validate.py`、`check.py`（lint）、`render.py` |
| 交付 | `embed_fonts.py`、`export_pdf.py`、`svg2pptx.py`（加 `--latin <字体>`）、`pptx_check.py` |

本流程改动了它的几处：
- figgenie 的 venue 里没有这篇论文的会议或期刊时：选最接近的，宽度用 `width_pt` 写真值；取值记在 profile 的「版面」里。
- 公式用本机 LaTeX（`latex_math.py`），不用它的 MathJax（`tex_fill.py`）。
- SVG 根元素加 `text-rendering="geometricPrecision"`（Chromium 的字距问题）。
- svg2pptx 之后跑 `pptx_strip_style.py`（LibreOffice 的阴影问题）；Windows 上设 `PYTHONUTF8=1`（它按本地编码读 spec.json）。
- 交出 SVG 前删掉它留下的工具注释（`audit_outputs.py --svg`）。
- 它的参考图和部件只作风格参考，版权归原作者，不进稿子。

## 论文的写作指南（项目里有的话）

用在：写图注、核对图上的说法和数字、定术语。动手画之前读一遍和图有关的部分。

和图有关的条目抄进 profile 的「硬规则」「图注与用词」「数字与口径」：指标的口径、数字的出处和三处一致、用词和术语、AI 使用声明由谁写、投稿格式和匿名要求。写作指南更新了，以指南为准，并同步改 profile。项目里没有这样的指南时，写作规则从论文自己的作者须知和已有的正文里读，记进 profile。

## nature-figure

只用三样：
- 出初稿时的图件契约五点（`static/core/contract.md`，细节见 `references/figure-contract.md`）：一句话结论、证据链、原型、后端、出口要求，写进 brief。
- 数据纪律和基本立场（`static/core/stance.md`）：一个主角面板、克制的配色、统计和数据完整性是图的一部分。
- 交付前的 QA 清单（`references/qa-contract.md`）。

只读这几个文件时，不必调用整个 skill。要调用它画数据图时，一开始就说明后端（绘图语言按项目的实际情况，写进 brief），它「先问 Python 还是 R」的门就过了。

它的隐私规则（回复和产物里不露本地路径、私人文件名）：图、图注、论文正文、交付的 PDF 和 PPTX 里照此执行（匿名投稿本来就要求这样，别的投稿也不会因此受损）；和用户聊天时要不要给完整路径，按 profile 的「语言与沟通」。

不用的部分：AI 生图（各刊的政策不同，没核实就不用；而且会编造内容）、Nature 的版面尺寸（版面尺寸以 profile 为准）。

## writing-skills

只在修改本 skill 时用：先编两三个场景（例如「用户开着最新的 pptx，让我把某个图标放大」「新起一张图」「数据出来了，填进结果图」「换一篇论文」），让子代理带着本 skill 说出它会怎么做，看它守不守红线；补上漏洞再交付。description 只写什么时候用，不写流程。

## 资料

| 资料 | 在哪 | 怎么用 |
|---|---|---|
| figgenie 的参考图库 | `<figgenie>/assets/exemplars/` | 挑参考图，学版式和密度 |
| figgenie 的部件库 | `<figgenie>/assets/symbols/` | `original` 的直接用 |
| 用户下载的论文源码和图标 | 交付目录旁边（路径写在 profile 的「文件放哪」） | 切图、借画法（见 `intake-and-materials.md`） |
| 论文的代码和实验记录 | profile 里写的位置 | 写 `claims_vs_code.md`、核对数字 |
