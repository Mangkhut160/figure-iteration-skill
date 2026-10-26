# 在用户保存的 pptx 上改（核心）

用户在办公软件里手改 pptx，常常在两轮之间保存，有时我还在干活他就保存了。我在聊天里问的选择题，他也常常直接改文件来回答。所以：不重画，在他最新保存的那份的副本上打补丁。补丁按名字找形状，他挪过的东西照样找得到；他又保存了，就在新的那份上重跑同一个补丁。

## 1. 找底稿

```bash
python $SK/scripts/latest_saved.py <交付目录> --glob '<前缀>.v*.pptx'    # 前缀写在 profile 的「文件放哪」里；不给 --glob 时是 fig
```

看四列：`by`（编辑软件存在文件里的 Application 名：`WPS Presentation`、`Microsoft Office PowerPoint` 等；我自己的输出带 python-pptx 模板的名字 `Microsoft Macintosh PowerPoint`，所以别靠这一列判断谁存的，看下面两列）、`author`（set = 编辑软件写进了账号名；我的输出是空的）、`open`（YES = 有锁文件，他正开着）、`after my render`（yes = 我交付后他又保存过，说明他改过）。

- 底稿 = 最新保存的那份。它开着也没关系：只读它（`make_from_saved.sh` 会先复制一份），不写入、不在原处转换、不删锁文件。
- 输出用下一个版本号，不能用他正开着的文件的名字（脚本会拒绝）。
- 底稿也存一份到 `<图目录>/vN/user_saved_<原名>_<时分>.pptx`（`--archive` 会自动做）。

## 2. 看他改了什么

```bash
python $SK/scripts/pptx_user_edits.py <图目录>/vP/fig.vP.pptx <交付目录>/fig.vP.pptx --assets <图目录>/assets
```

第一份是存档里我交出去的原样（`--archive` 存的），第二份是他保存过的：他在编辑软件里存的是交付目录里的同一个文件，原样只剩存档里那份。逐个形状比较种类、文字（图片按 assets/ 里的文件名认）、位置和大小（0.1 pt）、填充色、轮廓、第一段文字的字体，并按组名比较分组的位置和大小。输出分四类：`changed`（同一个形状变了什么：挪了、改字、改色、改字号）、整组被挪或缩放（只有偏移变了就是整组被挪，组里的形状不会逐个列出）、`only in the first deck`（被他删了）、`only in the second deck`（他新加的）。

- 全部保留，写进 brief 的改动记录（§6x，见 `content-sync.md` §3：他删了什么、挪了什么、放大了什么）。
- 看起来像误操作的（拉变形了、压到线上）：告诉他，不擅自改回。
- 如果他是用改文件来回答我上一轮的问题，就照他改的算，并写进记录。

## 3. 补丁脚本

从 `$SK/templates/patch_template.py` 起步，存成 `<图目录>/tools/patch_vN.py`。文件开头写清这一版改什么（和 brief 一致）。

- 补丁运行时的当前目录是补丁所在的目录，素材路径要从 `FIG_DIR` 拼（`os.path.join(FIG_DIR, 'assets', …)`）。
- 模板会优先导入本 skill 的 `pptx_kit.py`（`make_from_saved.sh` 设了 `FIGURE_ITERATION_SCRIPTS`）：别删模板开头那两行，不然补丁会导入图目录里可能留着的旧副本。

### 找形状

写补丁前先看清要动的组：`python $SK/scripts/pptx_inspect.py <底稿副本> --group 'n:<id> '`（不加 `--group` 列出所有顶层的组）。它给出每个形状的种类、文字或图片名、填充色、x/y/w/h 和底边。

svg2pptx 写出的 pptx 里，每个 spec 元素是一个组，名字是「id + 空格 + 标签」：`n:` 节点、`e:` 边、`a:` 标注、`c:` 容器，另有 `legend`。

```python
K = Kit(prs)
g = K.group('n:encoder ')                   # 带上空格，免得 'n:encoder' 也匹配到 'n:encoders'
lab = K.text_of(g, 'Input features')        # 组里文字恰好等于它的那一个
icon = one(K.pics(g, 'icons/lock.png'), 'lock icon')   # 按图片内容认（和 assets/ 里的文件比哈希）
cells = K.boxes(g, fill='5B9BD5')          # 按填充色
box = K.biggest_box(g)                     # 组里最大的矩形，一般是节点的外框
gl = K.glyphs(g)                           # 自由形状（LaTeX 字形），从左到右排好
labels = K.texts(g, 'xx.x')                # 文字相同的几个，从左到右排好
```

- 不按坐标找：他挪过的东西会找错。
- `group`、`top`、`text_of` 找到的不是恰好一个就停下报错；`pics`、`boxes`、`glyphs`、`texts` 返回列表，要恰好一个时套上 `one(列表, '说明')`，要几个就自己断言个数。数不对多半是他删了、改了字：先看一眼他的文件再决定，不要猜。
- 文字相同的几个（如几个 `xx.x`）：按它和已经认出的形状的关系分（例如中心 x 对着哪根柱子），不按绝对坐标。
- 按颜色找时注意同色的别的东西：例如图例的色块常和图里的元素同色，要再用位置关系（如底边落在某条线上）筛一遍。
- 顶层的单个形状（如一条线 `e:enc-head 线`）用 `K.top('e:enc-head ')`。

### 没有分组的 pptx（在编辑软件里从零画的，或别人做的）

形状没有 figgenie 起的名字，名字是 `Rounded Rectangle 1` 这类，不按名字找。先 `pptx_inspect.py <pptx>`（不加 `--group`）看每个顶层形状的文字、图片、填充色、位置，再用 `K.slide` 当作一个没有名字的大组：

- 找：`K.text_of(K.slide, '文字')`、`K.texts(K.slide, …)`、`K.pics(K.slide, 'x.png')`、`K.boxes(K.slide, fill='RRGGBB')`。
- 加：`K.clone(K.slide, 现成的形状)`、`K.text_box(K.slide, 模板, 文字, x=…, baseline=0, top=…)`（手画的文本框通常不是居中对齐的，给 `top`，即文本框的顶边）、`K.add_picture(None, …)`、`K.formula(K.slide, …)`。
- 填充色：`pptx_inspect.py` 里的十六进制值是显式 RGB，能按它找；`theme:accent1`、`style:accent1` 是从调色板里挑的颜色，不能按颜色找，改按文字找。`set_fill`、`set_line` 对两种都能改。
- 手画的图常带主题自带的阴影和渐变（`p:style`）。LibreOffice 画出来的可能和他的编辑软件里看到的不一样：不要擅自去掉，回复里提一句，请他在自己的软件里核对。

### 改

- 坐标单位是 pt：`geom(sh)` 取 x、y、w、h；`put(sh, x=…, w=…)`；`shift(sh, dx, dy)`。组里的形状用的是组自己的子坐标系：svg2pptx 刚出来时它等于页面坐标，但用户挪过整个组之后就不等了（组的偏移变了，子坐标没变）。同一个组里的东西互相对位置，用 `geom` 就行；要和别的组的东西对位置，用 `page_geom(sh)` 取页面坐标。`pptx_inspect.py --group` 会在组名下面写出这个组被挪了多少。
- 文字：`set_text(sh, '新字')`，保留原来的字体、字号、颜色。新标签用 `K.text_box(组, 模板, 文字, x, 基线)`，复制一个现成的文本框：基线偏移按模板自己的高度和字号算（居中对齐的框，svg2pptx 的都是；6 pt、6.5 pt、7 pt 实测误差在 0.1 pt 以内），模板不是居中对齐的就给 `top=`（框的顶边）。文字宽度用 `tw(文字, 字号, 粗体)`（figgenie 的字体度量），据此算居中、对齐、会不会出框。
- 格子和框：`K.clone(组, 现成的格子)`，再用 `put`、`set_fill`、`set_line` 调。格子里写字用 `put_text_in_cell(格子, 文字, 颜色, 现成标签的 a:r)`。
- 图片：`K.add_picture(组, png, x, y, 高, name=…, descr=…)`，按原比例放；印刷后低于 300 ppi 会拒绝。
- 公式：`K.formula(组, r'\hat{y}_t', x, 基线, size=7)`。它用本机 LaTeX 排版，经 svg2pptx 转成自由形状插进去，返回字形和盒子的宽、高、深；每个字形的 `descr` 里记着基线。已有的公式只要挪位置的话，直接 `shift` 它的字形（`K.glyphs`）。
- 换掉已有的公式：`K.replace_formula(组, 旧字形, r'新公式', size=7, align='right')`。它删掉旧字形，在同一条基线上排新的，左边缘（`align='left'`）或右边缘（`align='right'`）和旧的对齐。基线优先读 `descr`；老字形没有 `descr` 时取第一个字形的底边，第一个字形带下伸部分（如 `[`、`p`）时不准，那就自己量好基线，用 `K.formula`。公式变宽或变窄了，旁边的文字跟着挪，保持原来的间距。
- 删除：`remove(sh)`。
- 线和箭头：直线是 `p:cxnSp`，或宽、高为 0 的线，挪端点就是改 x/w 或 y/h；箭头是线端（`a:tailEnd`）。连线要跟着框走：框变宽了，进出它的线也要改。
- 一处改动牵动的东西一起改：框变宽 → 容器、进出的线、标注、图标都跟着挪。

### 收尾

`K.save(输出)` 会：把里面的东西有增减的组的子坐标系拟合到子形状（组自己的位置和缩放不动，所以用户挪过的组留在他挪到的地方，没动过的组原样保留）；清空作者字段（编辑软件写进去的账号名）和 app.xml 里的 Company、Manager（PowerPoint 把单位名写在那里）；检查有没有重复的形状 id；拒绝覆盖已有文件。补丁最后打印你选的数（坐标、宽度），写进 brief。

组里还套着组时，改了内层，外层也会一起拟合。svg2pptx 出的图只有一层组；它起的名字里有中文（`线`、`图例`），是它自己的命名，不是错。

## 4. 一条命令

```bash
bash $SK/scripts/make_from_saved.sh <他保存的 pptx> <图目录>/tools/patch_vN.py <交付目录>/fig.vN --archive <图目录>/vN
```

- 输出：`fig.vN.pptx`（缩略图已换成新渲染）、`.pdf`（无损，元数据清空）、`.png`（300 dpi）、`fig.vN_vs_before.png`（上面是底稿，下面是新版）；`<图目录>/qa/fig.vN_gray_deuteranopia.png`；检查结果。`--archive` 把成品、补丁和底稿存进 `<图目录>/vN/`。
- 每张图的设置放在 `<图目录>/figure.env`（模板在 `$SK/templates/figure.env`）：`FIG_PAGE=<宽>x<高>`（检查页面尺寸，如 `300x180`）、`FIG_SIZES=<允许的字号>`（如 `6,7,8`），数值来自 profile。没有这个文件时不查页面尺寸和字号（脚本会提示）：第一次在某张图上用本 skill 时，复制一份过去。
- 编辑软件写进底稿的账号名，脚本会自动读出来交给检查去拦（`--forbid-authors-of`），不用手填；`FIG_FORBID` 只在要多拦一个词时用。
- 要重来：改补丁，加 `--redo` 重跑。它只删本脚本写过、之后没有人保存过的同名 `.pptx`（对照 `<图目录>/qa/pipeline_outputs.sha1` 里记的内容指纹）；输出名和底稿同名、或那份被改过、被打开着，脚本都拒绝，需要时自己删。
- 他在我干活时又保存了：交付前再跑一次 `latest_saved.py`。有新的，就在新的那份上重跑同一个补丁（补丁按名字找形状，照样能用），输出名不变。

## 5. 编辑软件的脾气

- 保存时会把账号名写进 `docProps/core.xml` 的作者和最后修改者（PowerPoint 还会把单位名写进 `docProps/app.xml`）。我的输出清空了，但他再保存时又会写进去。投稿前用最后一版重跑一次检查，或者提醒他。
- 正开着的文件旁边有锁文件：WPS 和 PowerPoint 是 `~$<文件名>`（Office 对长文件名会截掉开头几个字符），LibreOffice 是 `.~lock.<文件名>#`，脚本都认。崩溃后会留下过期的锁文件，照样当作开着。
- 文件里的缩略图是他保存时的旧截图；我的输出用 `--thumbnail` 换成新渲染。
- LibreOffice 的渲染接近 WPS 和 PowerPoint（都用同一种字体时），但细节可能有一点差别（阴影、渐变、字距）。交付时请他在自己的软件里看一眼改过的地方。
- pptx 里的公式是自由形状，任何编辑软件里都不能当文字改（本 skill 不出 OMML 公式）。他要改公式就告诉我，我重新排。

## 6. 脚本稿和 pptx 主文件

切到 pptx 主文件以后，`build_<图名>.py` 停在最后一版脚本稿，不含他的手改和各版补丁的改动，每次交付都要说清楚。他要回到脚本时，先把 `pptx_user_edits.py` 列出的差别和各版补丁的内容全部并回脚本，重画后再对比，直到只剩有意的差别。
