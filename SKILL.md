---
name: figure-iteration
description: Use when making, revising or finishing a paper figure, especially one the user hand-edits in WPS or PowerPoint between turns (fig.vN.pptx) - e.g. "改图", "出下一版", "在我最新保存的版本上改", "换/加图标", "公式用 LaTeX", "数据出来了，填进结果图", "同步图注", "体检/审核一下", "解释图里的…", starting a new Fig.N, starting figures for a new paper or venue, or picking up a figure handoff (brief.md, claims_vs_code.md, caption.md, patch_vN.py).
---

# figure-iteration：论文图的迭代

论文图按这个流程走：先用脚本画初稿，交给用户在办公软件（WPS、PowerPoint 等）里手改；之后主文件就是用户最后保存的那份 pptx，每一轮都在它的副本上打补丁，然后出图、检查、同步文字，再交回去。本 skill 管流程和工具，对任何一篇论文都一样；具体画法用 figgenie-paper-diagram，论文的说法和数字以论文自己的写作指南为准（项目里有的话）。

**每篇论文的规矩在它的 profile 里**（版面、字号、配色、匿名、AI 声明、数字口径、文件放哪），跟着论文走，不在本 skill 里。找法：从图目录往上走，第一个 `figure-profile.md`。开工前读一遍。找不到，就是这篇论文还没有 profile：先做 `references/new-paper.md`（换了机器也先做它）。

`$SK` 指本 SKILL.md 所在的目录。图目录里的 `iteration-history.md`（每张图一份，记每一版用户的要求和决定），以及图目录里别的说明文件和 `tools/`，记的是那张图当时的做法和用户的决定。做法和本 skill 的流程冲突时，以本 skill 为准；用户记下的决定照他的办（有冲突就告诉他）。

## 红线（每一轮都过一遍）

1. **用户保存的 pptx 是主文件。** 只在它的副本上改，输出用新文件名（vN+1）。旁边有 `~$` 锁文件，说明用户正开着它：不写入、不在原处转换格式、不删锁文件。除非用户明确要求，不从脚本重画。
2. **用户的手改全部保留。** 看到拉变形、压线的地方，告诉用户，不擅自改回。
3. **图上的东西都要有出处。** 每个框、箭头、标签都要能对到代码和成立条件（`claims_vs_code.md`）。没冻结的数字一律占位，不拿快照数字顶替。
4. **交付前跑检查，并亲眼看图。** 看 100% 大小的 PNG，再放大看改过的地方。检查没过、图没看，不说"好了"。检查在一条命令里自动跑，看图也只要几十秒，没有明确要求就不省；用户要求省略某项时照他说的办，并在回复里写明哪些没查。
5. **照 profile 的「硬规则」办。** 匿名、AI 使用声明、署名、投稿系统对 PDF 的要求，都写在 profile 里，和这里的红线同等对待：开工前读，交付前逐条对。profile 没写的：这几类硬规则没定之前先问用户，别的项按默认走并标出来。
6. **公式和带上下标的符号用真 LaTeX 排**（`latex_math.py`；pptx 里用 `K.formula`）。字体字号只用 profile 规定的几种。
7. **图标和照片先用用户给的文件，用户指定的位置照做。** 没有合适的文件：问他要不要我画（`references/intake-and-materials.md` §3）；画了就告诉他是自己画的。
8. **图改了，文字同一轮跟着改**：图注、LaTeX 片段、`claims_vs_code.md`、brief 里的改动记录、`iteration-history.md`。

## 这次是哪种活

| 用户的话或情形 | 活 | 先读 |
|---|---|---|
| 新论文、新期刊、换了机器 | 配置 | `references/new-paper.md` |
| 要一张新图，或接手一张还没出过稿的图 | 出初稿 | `references/intake-and-materials.md`，`references/draft-from-scratch.md` |
| 接手交接包、换了新会话 | 先读交接包，再看下面几行 | `references/intake-and-materials.md` §1 |
| 「改一下」「出下一版」「在我保存的版本上改」「换/加图标」 | 迭代（最常见） | `references/iterate-on-saved-pptx.md` |
| 「数据出来了」「填进结果图」 | 填数据面板 | `references/data-panel.md` |
| 「解释一下…」「列一下还缺什么」「整理到 md 里」 | 写解释文档 | `references/communication.md` §3 |
| 每一轮都要做 | 出图检查、同步文字、交付 | `references/render-and-audit.md`，`references/content-sync.md`，`references/communication.md` |
| 本文的版面、配色、口径、署名规则 | — | 这篇论文的 profile（找法见上） |
| 要用到别的 skill | — | `references/skills-interplay.md` |
| 路径、Python 环境、Git Bash 的坑 | — | `references/toolchain.md` |
| 想知道某条规矩或某个决定是怎么来的 | — | 图目录里的 `iteration-history.md` |

## 一轮迭代（在用户保存的版本上改）

下面 `vP` 是我上次交付的版本号，`vN` 是这次要出的新版本号。

1. **找底稿**：`python $SK/scripts/latest_saved.py <交付目录> --glob '<前缀>.v*.pptx'`（每张图一个前缀，写在 profile 的「文件放哪」里；不给 `--glob` 时前缀是 `fig`）。它列出每份 pptx 的保存时间、由谁保存、是否开着、交付后用户有没有又存过，最后给出要打补丁的那份和下一个版本号。
2. **看用户手改了什么**：`python $SK/scripts/pptx_user_edits.py <图目录>/vP/fig.vP.pptx <交付目录>/fig.vP.pptx --assets <图目录>/assets`。第一份是存档里我交出去的原样，第二份是他保存过的（交付目录里的同名文件已经被他覆盖了）。手改全部保留，并写进 brief 的改动记录。
3. **写补丁** `<图目录>/tools/patch_vN.py`，从 `$SK/templates/patch_template.py` 起步：按组名、文字、颜色、图片内容找形状；新文字、新格子从现有的复制；公式用 `K.formula`；找不到就停下报错。写法见 `references/iterate-on-saved-pptx.md`。
4. **一条命令出图**：`bash $SK/scripts/make_from_saved.sh <他保存的 pptx> <补丁> <交付目录>/fig.vN --archive <图目录>/vN`。它依次做：复制副本、打补丁、用 LibreOffice 出 PDF 和 300 dpi PNG、出前后对照、换缩略图、出灰度与色弱图、跑检查、存档。
5. **看图**：100% 大小的 PNG、前后对照、每处改动放大看、灰度与色弱图（清单在 `references/render-and-audit.md` §3）。有问题就改补丁，加 `--redo` 重跑。
6. **同步文字**：按 `references/content-sync.md` 的清单改。
7. **交付前再跑一次第 1 步**：用户可能在你干活时又存了一次。如果存了，就在新的那份上重跑同一个补丁。
8. **回复用户**：交了哪些文件、改了什么、哪些地方是按我的理解做的、请他在编辑软件里看哪里（`references/communication.md`）。

## 和其他 skills 的配合（速览，细节见 `references/skills-interplay.md`）

| skill | 什么时候用 | 用它的什么 |
|---|---|---|
| figgenie-paper-diagram | 出初稿全程；迭代时量文字宽度、挑配色、找部件 | 简报模板、参考图库（由用户挑）、spec、量字、lint、嵌字体、导出 PDF、svg2pptx；`measure_text` |
| 论文的写作指南（项目里有的话） | 写图注、核对图上的说法和数字、定术语 | 它的硬性规则和版面规则；和图有关的条目抄进 profile |
| nature-figure | 出初稿时写图件契约；画真正的数据图 | 契约五点、数据纪律、QA 清单；绘图后端按 profile 或用户的选择，不重复问 |
| writing-skills | 只在修改本 skill 时用 | 用子代理按场景测试 |

## 文件

| 路径 | 内容 |
|---|---|
| `scripts/check_env.py` | 查这台机器上的模块和程序（`make_from_saved.sh --check` 调它），缺什么、设什么 |
| `scripts/latest_saved.py` | 找用户最后保存的 pptx，看它是否开着 |
| `scripts/pptx_user_edits.py` | 对比两份 pptx，列出手改：挪动、改字、改色、改字号、整组被挪、删除 |
| `scripts/pptx_inspect.py` | 列出形状的种类、文字、颜色、位置（没有分组的 pptx 也行）：写补丁前看，改完读回 |
| `scripts/pptx_kit.py` | 补丁用的函数：找形状、移动、复制、加文字、加图片、加 LaTeX 公式、保存（不动用户挪过的组） |
| `scripts/make_from_saved.sh` | 复制副本 → 打补丁 → 出图 → 检查 → 存档，一条命令；`--check` 查环境 |
| `scripts/make_draft.sh` | 从零出初稿的整条链：build、lint、字体、PDF、PNG、PPTX、检查、审计 |
| `scripts/make_test_deck.py` | 造一份测试 pptx，用来干跑新论文的配置 |
| `scripts/render_pptx.py` | 用 LibreOffice 出无损 PDF 和 PNG，出前后对照，换缩略图 |
| `scripts/audit_outputs.py` | 查页面尺寸、字体嵌入、Type 3、字号、位图 ppi、文件大小、署名和用户名、作者字段、app.xml 的单位名 |
| `scripts/pdf_clean.py` | 清空 Chromium 导出的 PDF 里的 Creator / Producer |
| `scripts/qa_sheets.py` | 出灰度与红绿色弱对照图 |
| `scripts/extract_assets.py` | 从用户给的材料里切图、做图标、按角色改色、把 SVG 转成 PNG |
| `scripts/latex_math.py`、`latex_check.py` | 用 LaTeX 排公式（矢量字形）；检查 SVG 里公式的位置 |
| `scripts/pptx_strip_style.py`、`pdf_text_width_check.py` | 出初稿时用：去掉 svg2pptx 留下的主题阴影引用；检查 Chromium 导出 PDF 的字距 |
| `scripts/_paths.py`、`_deck.py`、`_env.sh` | 内部共用：找程序的位置、读 pptx 的函数、shell 脚本的公共函数 |
| `templates/` | `patch_template.py`、`build_figure.py`（初稿骨架）、`figure.env`、`profile_template.md`（新论文的 profile）、`materials_request.md`（开画前向用户要的资料）、`data_fill_form.md`（填数表） |
| `references/` | 见上面「这次是哪种活」 |

## 常见错误

| 错误 | 后果 | 改法 |
|---|---|---|
| 从脚本重画整张图 | 用户的手改全丢 | 在他保存的版本的副本上打补丁 |
| 写入或转换了带 `~$` 锁的 pptx | 毁掉他正开着的文件 | 只读它；输出用新文件名 |
| 按坐标找形状 | 用户挪过的东西会改错地方 | 按组名、文字、颜色、图片内容找 |
| 交付前没再看一次修改时间 | 交出去的版本缺了他最新的手改 | 做第 7 步 |
| 新加的文字用了别的字号、字体 | 检查不过，和全图不一致 | 从现有的文本框复制 |
| 用普通文字或 Unicode 拼下标、星号 | 不专业，和正文公式不一样 | `K.formula` / `latex_math.py` |
| 把快照数字填进结果图 | 违反数字纪律 | 占位 `xx.x`，冻结后再填 |
| 把用户指定的位置"优化"到别处 | 他得再说一遍 | 照做；觉得不好就提建议，不先动 |
| 没清空作者字段 | 编辑软件的账号名进了投稿文件 | `K.save` 会清空，检查也会查 |
| 长解释写在聊天里 | 用户要解释或清单时，通常要的是能单独打开的文件 | 写成单独的 md，聊天里只给链接 |
| 只说"改好了"，不给证据 | 用户没法确认 | 给出检查结果，并说明请他看哪里 |
| 换了论文还用上一篇的 profile 和 figure.env | 页面尺寸、字号、匿名规则全错 | 先做 `references/new-paper.md` |
