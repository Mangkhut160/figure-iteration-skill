# 换一篇论文，或换一台机器

流程、脚本、模板不用改。要换的只有三样：这篇论文的 profile、每张图的 `figure.env`、这台机器上的工具位置。

## 零、把 skill 放到能用的地方

- 本 skill 是一个文件夹（`figure-iteration/`，里面有 `SKILL.md`）。放进项目的 `.claude/skills/` 只给这个项目用；放进 `~/.claude/skills/` 所有项目都能用。要用到别处就整个复制过去，不要只复制 `SKILL.md`。
- 脚本不依赖它放在哪，也不依赖用户名：工具靠环境变量、PATH 和常见安装位置找（`references/toolchain.md`）。
- profile 放哪：跟着论文走，放在所有图目录的共同父目录里，文件名 `figure-profile.md`（skill 从图目录往上找，第一个就是它）。skill 本身不存任何一篇论文的 profile，这样 skill 装在用户级目录、同时给几篇论文用时也不会混。

## 一、新论文

按顺序做。每一步都有结果可看，不要跳。

1. **自己先读材料，不问用户。** 论文源码（`\documentclass` 和选项、术语、哪里引用了这张图）；作者须知或模板说明（匿名、字体、位图、文件大小）；已有的 brief、图、素材；用户的记忆；别的图的 `iteration-history.md`（别的论文或别的图走过的路）。
2. **用论文自己的模板量栏宽，不要猜。** 在论文源码（或一个类和选项都相同的小文件）里放下面这几行，编译，读 `WIDTHS` 那一行：

   ```tex
   \maketitle   % 双栏的类到这里才开始分栏；标题、作者随便填
   \begin{figure}\typeout{WIDTHS columnwidth=\the\columnwidth textwidth=\the\textwidth}\end{figure}
   ```

   单栏图宽 = `columnwidth`，通栏图宽 = `textwidth`。自查：双栏论文里这两个数必须明显不同（IEEEtran `journal`：252 和 516 pt；acmart `sigconf`：241.15 和 506.30 pt）；相等说明量早了（直接放在 `\begin{document}` 后面，acmart 会量出两个 506.3）。TeX 的 pt 是 1/72.27 in，图里的 pt 是 1/72 in，差 0.4%：用 `width=\columnwidth` 放进去只会缩小 0.4%，字号检查照常；要严格 1:1，画布宽取量出的数乘 72/72.27。走 SVG 路线（Chromium 导出 PDF）时，页面宽高会取整到 CSS 像素（0.75 pt 的整数倍），所以画布宽取 0.75 pt 的整数倍，免得页面尺寸检查差 0.3 pt 以上。高度由内容定，不能超过版面。
3. **写 profile。** 复制 `templates/profile_template.md`，放到上面「profile 放哪」说的位置，逐项填。读不出来的项，写成给用户看的清单（接在 `templates/materials_request.md` 后面）。一次对话最多问三个问题（`communication.md` §2）；其中硬规则类（匿名、署名、AI 使用声明、投稿格式）没定之前先问，别的项按默认走，并在 profile 里标「默认，待确认」。
4. **起第一张图。** 在图目录里放 `figure.env`（复制 `templates/figure.env`，把里面的占位值改成 profile 里的数）和一个空的 `iteration-history.md`（之后每一版加一行：用户的要求、做法、留下的规则）；在交付目录里定好文件名前缀，写进 profile。
5. **查环境。** `bash $SK/scripts/make_from_saved.sh --check`：缺什么、设什么环境变量，它会说（含 LaTeX 能不能真的排出一个公式）。
6. **干跑一次。** 还没有任何 pptx 时，先造一份测试用的，再用什么都不改的补丁跑一遍整条流水线，输出放进临时目录：

   ```bash
   T=<临时目录>; mkdir -p $T/deliver $T/fig && cp <图目录>/figure.env $T/fig/     # 临时的图目录：qa/ 等输出写在这里，不弄脏真的图目录
   python $SK/scripts/make_test_deck.py $T/deliver/figX.v0.pptx --page <宽>x<高> --size <最大的字号>
   FIG_DIR=$T/fig bash $SK/scripts/make_from_saved.sh $T/deliver/figX.v0.pptx $SK/templates/patch_template.py $T/deliver/figX.v1
   ```

   检查报的页面尺寸、字号应当是这篇论文 profile 里的数；报错就在这里解决，不留到交付时。
7. **出初稿**走 `references/draft-from-scratch.md`：`templates/build_figure.py` 是能直接跑的骨架，`scripts/make_draft.sh <图目录>` 一条命令从 build 跑到审计。
8. **记下来。** 用户这一轮定的事写进 brief；以后还用得上的偏好写进记忆。

## 二、新机器

1. 跑 `bash $SK/scripts/make_from_saved.sh --check`。它按「环境变量，然后 PATH，然后常见安装位置」的顺序找；找不到就在报告里写明该设什么。
2. 设环境变量（见 `references/toolchain.md`）：`PY_PATCH`（有 python-pptx、lxml 的 Python）、`PY_SYS`（有 PyMuPDF 的 Python）、`SOFFICE`、`TEXLIVE_BIN`、`FIGGENIE_SCRIPTS`。
3. 把这台机器上各工具的位置、Git Bash 和 LibreOffice 之类遇到过的坑记在你自己的笔记或记忆里。不要写进 skill：skill 要能原样带到别处。
4. LibreOffice 只能在容器里跑的机器上（常见于服务器），`render_pptx.py` 不能直接用：给它一个本机可执行的 `soffice`（可以是调用容器的包装脚本，用 `SOFFICE` 指定），或者换一个出 PDF 的办法，再把办法记进你的笔记。

## 三、哪些文件属于哪一层

| 层 | 文件 | 换论文时 |
|---|---|---|
| 流程和工具 | `SKILL.md`、`scripts/`、`templates/`，以及 `references/` 里除下面几类以外的 | 不动；发现缺陷就改这里，别改在 profile 里绕 |
| 这篇论文 | profile（`figure-profile.md`）、图目录里的 `figure.env`、`brief.md`、`claims_vs_code.md` | 新建一份 |
| 迭代记录 | 图目录里的 `iteration-history.md` | 每张图一份（第一张图起就建）：每一版加一行，记用户的要求、做法和留下的规则 |
| 用户本人 | 用户的记忆（个人习惯） | 同一个用户不动；换用户就改 |
| 这台机器 | 你自己的笔记或记忆（`references/toolchain.md` §3） | 新记一份 |
