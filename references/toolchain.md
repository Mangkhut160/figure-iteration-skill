# 环境

## 1. 需要什么，脚本怎么找到它们（任何机器）

先跑 `bash $SK/scripts/make_from_saved.sh --check`。它按下表的顺序找，缺什么、该设哪个环境变量，都会写出来。

| 要什么 | 谁用 | 找的顺序 | 找不到时 |
|---|---|---|---|
| 有 python-pptx、lxml、Pillow 的 Python（`PY_PATCH`） | 补丁、figgenie 的脚本 | `PY_PATCH`；figgenie 的虚拟环境（`~/.codex`、`~/.claude`、`~/.agents` 下 skills 里的 `.venv`）；`python3`；`python`。取第一个能导入 pptx 和 lxml 的 | 设 `PY_PATCH` |
| 有 PyMuPDF、Pillow、numpy 的 Python（`PY_SYS`） | 渲染、检查、提取素材 | `PY_SYS`，否则 `python` | 设 `PY_SYS` |
| LibreOffice | `render_pptx.py` | `SOFFICE`；Windows 的用户安装（`%LOCALAPPDATA%\Programs\LibreOffice`）和系统安装（`%ProgramFiles%\LibreOffice`）；macOS 的 `/Applications/LibreOffice.app`；PATH 上的 `soffice`、`libreoffice` | 设 `SOFFICE` |
| TeX Live（latex、dvisvgm） | `latex_math.py` | `TEXLIVE_BIN`；PATH；常见安装位置（`~/texlive/*/bin/*`、`/usr/local/texlive/*/bin/*`、`C:/texlive/*/bin/*`、`/Library/TeX/texbin`） | 设 `TEXLIVE_BIN`，或把它的 bin 放进 PATH |
| figgenie-paper-diagram | 从零出初稿（`make_draft.sh`）、`K.formula`、`pptx_kit.tw()`、`latex_check`、`pdf_text_width_check` | `FIGGENIE_SCRIPTS`；`~/.codex`、`~/.claude`、`~/.agents` 下 skills 里的 `figgenie-paper-diagram/scripts` | 设 `FIGGENIE_SCRIPTS`；不装的话上面这些用不了，其余照常 |
| Chromium（playwright） | 从零出初稿：figgenie 用它渲染 PNG、导出 PDF | figgenie 的 Python 环境里装的 playwright | 在那个 Python 里 `python -m playwright install chromium`；不装则 `make_draft.sh` 用不了 |
| Arial 字体（或论文要求的别的字体） | 渲染和检查 | 系统字体 | LibreOffice 用度量兼容的 Liberation Sans 代替；PDF 里的字体名会对不上，字号检查照常 |
| Inkscape（可选） | 查 SVG 路径的范围（`--query-all`） | PATH | 不装也行 |

环境变量：

| 变量 | 给谁用 | 默认 |
|---|---|---|
| `FIGGENIE_SCRIPTS` | pptx_kit、latex_check、pdf_text_width_check、make_draft.sh | 见上表 |
| `FIG_DIR` | pptx_kit、pptx_user_edits、pptx_inspect | make_from_saved.sh 从补丁所在目录往上找第一个有 `figure.env` 或 `assets/` 的目录 |
| `FIGURE_ITERATION_SCRIPTS` | 补丁模板 | make_from_saved.sh 设成本 skill 的 `scripts/`，让补丁优先导入本 skill 的 `pptx_kit.py`，不导入图目录里的旧版 |
| `FIG_PAGE`、`FIG_SIZES`、`FIG_MAX_MB`、`FIG_MIN_PPI`、`FIG_FORBID` | make_from_saved.sh、make_draft.sh 里的检查 | 都不设：不查页面尺寸、字号、文件大小（会提示），位图最低分辨率按 300 ppi；`FIG_FORBID` 无（底稿里编辑软件写的账号名会自动拦；`FIG_FORBID` 用来多拦几个词，逗号分隔，例如工具名、机构名）。写在图目录的 `figure.env` 里，没有默认值：别的论文的数不会漏进来 |
| `FIG_INK`、`FIG_FONT`、`FIG_LATIN` | pptx_kit 加的公式、build_figure.py 骨架、svg2pptx | 000000；arial；Arial |
| `TEXLIVE_BIN`、`LATEX_CACHE`、`LATEX_PREAMBLE` | latex_math | 见上表；不缓存；不加（数学字体用 Computer Modern，别的数学字体在这里加 `\usepackage`） |
| `PYTHONDONTWRITEBYTECODE` | 两个 .sh | 设成 1：脚本不往 skill 目录里写 `__pycache__` |
| `SOFFICE` | render_pptx | 见上表 |
| `PY_PATCH`、`PY_SYS` | make_from_saved.sh、make_draft.sh | 见上表 |

## 2. Windows + Git Bash 的坑

- 传给 Windows 程序的路径，用 `cygpath -m` 转成 `C:/…` 的形式。设了 `MSYS_NO_PATHCONV=1` 时，`/tmp/...` 这类路径不会被自动转换，Python 会打不开。两种做法不要混用。
- `soffice`、`inkscape` 的参数里有以 `/` 开头的或 `file:///` 的，设 `MSYS_NO_PATHCONV=1`。
- figgenie 在 Windows 上按本地编码（cp1252）读 spec.json：设 `PYTHONUTF8=1`；输出里有中文时设 `PYTHONIOENCODING=utf-8`。
- 在 heredoc 里写 Python 时用 `<<'EOF'`（带引号），不然反斜杠和 `$` 会被 shell 改掉。就算带引号，经命令行工具转手的普通字符串里，反斜杠也可能被吞掉（例如 LaTeX 的 `\theta` 里的 `\t` 会变成制表符，文件照样写出来，只是内容错了）：含反斜杠的内容写进文件，或用编辑工具改，不要放在命令行里的普通字符串里；改完用眼睛看一遍结果，别只看有没有报错。
- LibreOffice 每次用临时的用户配置（`-env:UserInstallation=file:///<临时目录>/profile`），而且只转副本。
- 没有 Microsoft Office 的机器上，svg2pptx 出不了 OMML 公式；本 skill 的公式一律是自由形状，所以不受影响。

## 3. 这台机器上的记录

skill 要能原样带到别处，所以各工具在某台机器上的具体位置不写在这里：记在你自己的笔记或记忆里。值得记的：`PY_PATCH`、`PY_SYS`、`SOFFICE`、`TEXLIVE_BIN`、`FIGGENIE_SCRIPTS` 该设成什么，Git Bash 或 LibreOffice 在这台机器上遇到过的坑。

LibreOffice 只能在容器里跑的机器上，`render_pptx.py` 不能直接用：给它一个能直接执行的 `soffice`（可以是调用容器的包装脚本，用 `SOFFICE` 指定），或者换一个出 PDF 的办法，再把办法记下来。
