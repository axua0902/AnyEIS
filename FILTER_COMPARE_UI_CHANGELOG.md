# Filter Compare UI / 数据检查重构 — 变更记录

> 涵盖 `EIS/FilterFile/Filter.py`、`EIS/FilterFile/Filterfun.py`、`EIS/Other/Datacheck.py` 的多轮迭代改动。
> 按主题分组,记录问题、修复与最终设计。

---

## 1. 数据检查函数从 `Filter.py` 抽离到 `Datacheck.py`

**起因**: `Filter.py` 第 173-262 行的 `check1`-`check5` 与 `EIS/Other/Datacheck.py` 中已有的同名模块函数逻辑重复。

**修改**:
- `Filter.py:11` 新增 import: `from EIS.Other.Datacheck import check1, check2, check3, check4, check5`
- `Filter.py:173-262` 的 5 个方法替换为薄包装,内部委托给 `Datacheck.py` 中的模块函数
- 保留 `self.check*` 调用兼容性:
  - `self.check1()` / `self.check2()` 内部用 `self.selectlist` / `self.prodata` 注入参数
  - `self.check3(data, namelist)` / `self.check4(prodata, refdata)` 签名不变
  - `self.check5(data, namelist)` 参数列表兼容,`namelist` 已被 `Datacheck.check5(data)` 取代(原 `check5` 是空实现,新版本具备真正的 EIS/DS 类型判定)

**注意**: `Datacheck.check5` 返回字符串 `'EIS'` / `'DS'` / `'UNKNOWN'`,而原 `Filter.check5` 返回 `None`。如外部代码依赖 `None`,需另行处理。

---

## 2. 修复 `KeyError: 'Rs[ohm]'` 错误

**起因**: `plot_filter_comparison_charts` 与 `calculate_multi_filter_comparison_data` 硬编码列名访问 (`original_data['Rs[ohm]']`),遇到列名变体 (`'Rs'` / `'RS[OHM]'` 等) 或 DS 数据即报 `KeyError`。

**修改**:

### 2.1 `Datacheck.py` — 新增 `resolve_column()` 工具
- 大小写、首尾空白不敏感地匹配列名
- 支持 EIS 列变体: `FREQ[Hz]` / `Rs[ohm]` / `RS[OHM]` / `X[ohm]` 等
- 失败时返回 `default` 并打印实际列名

### 2.2 `Filter.py:plot_filter_comparison_charts`
- 导入 `resolve_column`
- 8 处硬编码列访问改为 `resolve_column` 调用
- 顶部增加缺失列检查,缺列时打印实际列名后提前返回

### 2.3 `Filterfun.py:calculate_multi_filter_comparison_data`
- 导入 `resolve_column`
- 统计量 (`noise_reduction` / `correlation`) 改用 `resolve_column` 访问
- 缺列时 `raise KeyError` 打印实际列名(被外层 `except` 捕获,继续下一个滤波器)

---

## 3. 修复 `Glyph 127942 (TROPHY)` 字体警告

**起因**: [Filter.py:693](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/FilterFile/Filter.py#L693) 子图 10 标题含 `🏆` emoji,DejaVu Serif 字体不含此字符。

**修改**: 标题改为 ASCII 字符 `"[*] Recommended Filter"`,保留视觉提示且 100% 兼容所有字体。

---

## 4. 支持 DS(介电谱)数据类型

**起因**: DS 数据列名(`epsRE[-]`、`epsIM[-]`、`sigmaRE[S/m]`、`sigmaIM[S/m]`)与 EIS 不同,即使列名已容差,统计计算与子图绘制仍按 EIS 语义处理。

**修改**:

### 4.1 `Filterfun.py:calculate_multi_filter_comparison_data`
- 引入 `check5` 自动识别 `data_type` (`'EIS'` / `'DS'`)
- 根据 `data_type` 切换列候选列表:
  - **EIS**: `real=Rs*`, `imag=X*`, `third=PHASE*`
  - **DS**: `real=epsRE*`, `imag=epsIM*`, `third=sigmaRE*`
- 统计量统一用 `real/imag/third` 计算后映射到 `Rs/X/Phase` 键,保持下游兼容
- 引入 `_safe_pct` 工具,处理 `np.std(orig) == 0` 时除零
- 返回值新增 `data_type` 与 `column_map`,透传给绘图层

### 4.2 `Filter.py:plot_filter_comparison_charts`
- 优先使用 `comparison_data['column_map']`;缺失时按 `data_type` 本地再解析
- 标签与标题按 `data_type` 切换:
  - **EIS**: `Rs [Ohm]` / `X [Ohm]` / `Phase [deg]`,子图标题为 `Nyquist Plot` 等
  - **DS**: `ε'` / `ε"` / `σ' [S/m]`,子图标题为 `Cole-Cole Plot` 等
- DS 数据不执行 `ax.invert_yaxis()` (Cole-Cole 习惯 Y 轴正向)
- 子图 4 在 third 列缺失时跳过原曲线绘制,避免空图

---

## 5. 修复图表标题与图例重叠

**起因**: 5 列子图布局下,标题与图例相互覆盖。

**修改**:

### 5.1 总标题与子图区域冲突
| 参数 | 原值 | 新值 | 作用 |
|---|---|---|---|
| `suptitle y` | 0.98 | **0.995** | 标题上移,交由 `top` 调整子图区域避让 |
| `subplots_adjust top` | 0.94 | **0.90** | 子图区域上界下移,留 10% 高度 |
| `subplots_adjust hspace` | 0.4 | **0.55** | 三行子图垂直间距增大 |
| `subplots_adjust bottom` | (默认) | **0.06** | 显式底部边距 |

### 5.2 子图标题过长 → 两行布局 + 缩小字号
- "Real Part vs Frequency" → "Real Part\nvs Frequency" (类似处理所有 10 个标题)
- 所有 `ax.set_title` 添加 `fontsize=10, pad=4`

### 5.3 图例溢出 → 子图内部
- 原: `bbox_to_anchor=(1.05, 1), loc='upper left'` (在子图外部,延伸到相邻子图)
- 改: `loc='lower left', fontsize=8, framealpha=0.85` (子图内部左下角,半透明背景)

---

## 6. Filter Compare 对话框 — 可配置多方法对比 (核心新增功能)

**起因**: 原 `filters_config` 在 `Filterfun.py:517` 硬编码 5 个方法,UI 中下拉框却可选 14 个,无法让用户从全部方法中选 5 个做对比。

**修改分 4 步,经过 3 轮迭代**:

### 6.1 `Filterfun.py` — 函数接受自定义配置
```python
def calculate_multi_filter_comparison_data(prodata, prodataname, custom_filters_config=None):
    # ...
    if custom_filters_config is not None and len(custom_filters_config) > 0:
        filters_config = custom_filters_config
    else:
        filters_config = { 'Savitzky-Golay': ..., 'Median': ..., ... }  # 默认 5 个
```
- 向后兼容:`custom_filters_config=None` 时保留原默认行为
- 打印 `Using N user-selected filters: [...]` 提示

### 6.2 `Filter.py` 顶部 — 新增注册表与工具
- `METHOD_REGISTRY`: 全部 13 种方法 (含 `name` / `func` / `default` / `color`)
- `DEFAULT_SELECTED`: 默认勾选的 5 个 (向后兼容)
- `MAX_COMPARE_METHODS = 5`
- `_parse_param_str()`: 解析 `key=value, key=value` 字符串

### 6.3 UI 演化

**第 1 版** — 列表 + 共享参数编辑框 (失败)
- `QListWidget` 多选 + 共享 `QLineEdit`
- 问题: 选中多个方法时无法编辑参数 (单选才能编辑)

**第 2 版** — 自定义行 (QListWidget + setItemWidget)
- 每行 = `[复选框] [方法名] [参数编辑框] [Reset]`
- 问题: 列表被压扁,只显示 2 个方法,横向留白多

**第 3 版 (最终)** — QGridLayout 5 列 × 3 行
- 每个 cell = `[复选框(方法名)] [参数编辑框] [Reset]` 紧凑水平布局
- `methods_grid` 用 `addWidget(methods_grid, 1)` 占满控制区剩余宽度
- 网格下方独立按钮行: Generate / Save / Save As / Close
- 计数标签 `Selected N/5` 右侧,蓝色 (≤ 5) / 红色 (> 5)

```python
# Filter.py:530-552
control_layout = QHBoxLayout()
_methods_label = QLabel("Methods:")
_methods_label.setStyleSheet("font-weight: 700; font-size: 13px;")
control_layout.addWidget(_methods_label)
control_layout.addWidget(methods_grid, 1)  # stretch=1 让网格占满
control_layout.addWidget(_count_label)
```

### 6.4 字号调整
| 控件 | 字号 | 最小/最大宽 |
|---|---|---|
| `QCheckBox` (方法名) | 11px | 110/140 |
| `QLineEdit` (参数) | 11px | 120/180 |
| `Reset` 按钮 | 10px + padding 2px 4px | max 46 |
| `QLabel "Methods:"` | 13px bold | — |
| `QLabel "Selected N/5"` | 700 (粗体) | min 110 |

---

## 7. 中英文本地化

**起因**: `Filter.py:439-452` 计数标签使用中文 (`已选 0/5`),要求改为英文。

**修改**:
- `# 计数标签` → `# Counter label`
- `已选 0/{MAX}` → `Selected 0/{MAX}`
- `已选 {n}/{MAX}` → `Selected {n}/{MAX}`

---

## 8. Processing → Figure 数据类型自动同步 (本轮新增)

**起因**: `EIS/ProcessingFile/Processing.py:322` 的 `processing()` 函数会根据 `processmethodComboBox` 选择的方法,把输入的 EIS 数据换算为 DS 数据 (Paraplate / DieMat / Three-Solution / TLcalculateEPS) 或反之 (System Calibration / RF Impedance Calibration 仍输出 EIS)。但 Figure 页面的 `datatypeComboBox` 是手动的,用户必须自己切到与计算结果匹配的图表类型,否则会出现"数据到了但图是空"或"图表类型与数据列不匹配"的错误。

### 8.1 `Datacheck.py` — 新增 `detect_data_type_from_columns()`

复用已有的 `resolve_column` 做列名匹配,与 `check5` / Filter 模块保持一致的容差策略 (大小写、首尾空白不敏感),避免在两个文件里维护两份列名清单。

- 入参: `plotdata` (DataFrame 列表) + `message` (dataInfo,可省略)
- 检测优先级:
  1. 奇数索引 + `process_applied=True` 的条目 — 代表 Processing 计算的真实输出类型
  2. 任何可用条目 — 回退路径,覆盖未处理的 Input / Simulation 原始数据
- 返回: `'EIS'` | `'DS'` | `'UNKNOWN'` (无法判定时返回 `'UNKNOWN'`,由调用方决定是否切换)

### 8.2 `Figure.py` — `getsignal` 后自动切 ComboBox

- 顶部新增 import: `from EIS.Other.Datacheck import detect_data_type_from_columns`
- `getsignal()` 存储完 `outputlist / plotdataname / plotdata / message` 后立即调用 `_auto_set_datatype_combobox()`
- 新增方法 `_auto_set_datatype_combobox()`:
  ```python
  type_to_combo = {
      'EIS': 'f-Z,Phase,Re(Z),Im(Z)',
      'DS':  'f-Epsilon,Sigma',
  }
  detected = detect_data_type_from_columns(self.plotdata, self.message)
  new_type = type_to_combo.get(detected)
  ```
- 仅在当前选项不匹配时通过 `setCurrentIndex` 切换 — 该操作会触发已有的 `currentIndexChanged → selectionchange()` 信号,自动联动更新 Nyquist / Bode Re / Im / Phy 按钮的标签和勾选状态

### 8.3 覆盖的处理方法 → 输出类型映射

| Processing 方法 | 输出列 | 自动切换为 |
|---|---|---|
| Parallel Plate Capacitor | `EpsRE[-]` / `SigmaRE[S/m]` 等 | `f-Epsilon,Sigma` |
| Dielectric Material Method | `EpsRE[-]` / `SigmaRE[S/m]` 等 | `f-Epsilon,Sigma` |
| Three-Solution Method | `EpsRE[-]` / `SigmaRE[S/m]` 等 | `f-Epsilon,Sigma` |
| RF Dielectric Calculation | `EpsRE[-]` / `SigmaRE[S/m]` 等 | `f-Epsilon,Sigma` |
| K-K for EIS | `EpsRE[-]` / `SigmaRE[S/m]` 等 | `f-Epsilon,Sigma` |
| System Calibration | `Rs[ohm]` / `X[ohm]` / `Z[ohm]` | `f-Z,Phase,Re(Z),Im(Z)` |
| RF Impedance Calibration | `Rs[ohm]` / `X[ohm]` / `Z[ohm]` | `f-Z,Phase,Re(Z),Im(Z)` |
| RF Impedance Calculation | `Rs[ohm]` / `X[ohm]` / `Z[ohm]` | `f-Z,Phase,Re(Z),Im(Z)` |

### 8.4 回归验证

冒烟测试 7/7 通过 (临时脚本,验证后已删除):
- 原始 EIS / DS 数据识别正确
- 配对数据 + `process_applied=True` (Paraplate、Calibrate) 优先级生效
- 空数据返回 `'UNKNOWN'`,ComboBox 不切换 (保留用户手动选择)
- Input 页面 (仅有 `synthetic` 无 `process_applied`) 走 fallback 扫描,识别正确
- 列名大小写变体 (`rs[OHM]`) 也能识别

### 8.5 二次迭代:跟随 Original/Processed 复选框动态切换 (本轮新增)

**起因**: 8.1–8.3 只在新数据到达 (`getsignal`) 时切换 ComboBox。但 Processing 模式中 Original (EIS) 和 Processed (DS) 是**不同类型**的两份数据,用户通过 Original/Processed 复选框决定显示哪一份。第一版只盯着 Processed → 选了 "只显示 Original" 时图表仍是 DS 布局,曲线画在错位的坐标轴上。

**修改**: `_auto_set_datatype_combobox` 改为检测**当前可见**的子集 (而非全部 plotdata),并把检查点也接到 `_on_processing_state_changed` 上,使复选框切换也能即时同步图表类型。

- 可见性判定与 `_filter_synthetic_for_display` 保持一致 (三个分支):
  1. `_display_synthetic=False` (Input/Simulation) → 只看 Original
  2. `_display_synthetic=True` (Filter/Processing/Fitting) → 按 Original/Processed 复选框
  3. `message` 缺失/长度不匹配 → 兜底全保留
- 复选框切换时 (`_on_processing_state_changed`) 先调用 `_auto_set_datatype_combobox` 再 `drawfigure`,与原 "重绘以反映新选择" 行为兼容

**可见性 → 图表类型对应关系 (以 Paraplate 为例, Original=EIS, Processed=DS)**:

| Original 勾选 | Processed 勾选 | 可见子集 | 检测结果 | ComboBox |
|---|---|---|---|---|
| ✓ | ✓ | 两份都看 | Processed 优先 (含 `process_applied`) | `f-Epsilon,Sigma` |
| ✓ | ✗ | 仅 Original | 仅 EIS 列 | `f-Z,Phase,Re(Z),Im(Z)` |
| ✗ | ✓ | 仅 Processed | 仅 DS 列 | `f-Epsilon,Sigma` |
| ✗ | ✗ | 无 | (提前 return) | 保持当前值 |

---

## 9. Original/Processed 互斥 + 默认 Processed (本轮新增)

**起因**: 在 Processing 模式中 Original 和 Processed 是不同类型的两份数据,如果用户把它们都勾选,`datatypeComboBox` 只能选一种 (Nyquist 或 Cole-Cole),另一份会被画在错位的坐标轴上。需要:
1. 强制两者不可同时勾选
2. 当两者都勾选时,自动默认到 Processed (与 Processing "输出是结果" 的语义一致)

**修改**:

### 9.1 `Figure.py` — `clicked` 互斥处理器
- `__init__` 新增 `clicked` 信号连接 (与 `stateChanged` 并行):
  ```python
  self.figuregui.origindataCheckBox.clicked.connect(self._on_orig_checkbox_clicked)
  self.figuregui.processeddataCheckBox.clicked.connect(self._on_proc_checkbox_clicked)
  ```
  `clicked` 只对用户点击触发,`setChecked()` 不会触发,可避免与 `stateChanged` 互相递归。
- 新增 `_on_orig_checkbox_clicked(checked)` / `_on_proc_checkbox_clicked(checked)`:
  - 用户点击启用一方时,若另一方也已勾选 → `blockSignals` 抑制其 `stateChanged` 后取消
  - 调整后手动触发一次 `_auto_set_datatype_combobox` + `drawfigure` (因为 `blockSignals` 抑制了自动重绘)
- `_on_processing_state_changed` 在 "两者都勾选" 时直接 return (瞬时态) — click handler 会在最终单选状态下重绘

### 9.2 `Figure.py` — `_apply_default_checkbox_state`
- `getsignal` 末尾调用,仅在 Original 和 Processed **类型不同** 且 **两者都勾选** 时取消 Original
- 类型相同时 (Filter / Fitting 不改类型) 保留用户的单选偏好
- 内部再次调用 `detect_data_type_from_columns` (一次给 Original,一次给 Processed)

### 9.3 行为矩阵 (此版尚未分场景,统一为"互斥 + 默认 Processed")

| 触发 | Original 终态 | Processed 终态 |
|---|---|---|
| getsignal (类型不同, 两者都勾) | ✗ | ✓ |
| getsignal (类型相同) | 不动 | 不动 |
| 用户点击 Original (Proc 已勾) | ✓ | ✗ |
| 用户点击 Processed (Orig 已勾) | ✗ | ✓ |
| 用户点击 Original (Proc 未勾) | ✓ (toggle) | 不动 |
| 用户点击 Processed (Orig 未勾) | 不动 | ✓ (toggle) |

**冒烟测试 7/7 通过**: Paraplate (类型不同) / Fitting (类型相同) / 单条目 / 用户覆盖 / 默认不动等场景全部命中。

---

## 10. 互斥规则条件化 — 由 processCheckBox 控制 (本轮新增,最终版)

**起因**: 9.x 把互斥写死为 "永远 ON",但实际只有 Processing 模式才需要 (Filter / Fitting 数据类型不变,允许两者同时勾选用于对比)。统一为强制单选会破坏 Filter / Fitting 用户的对比习惯。

**修改**: 把互斥拆为可配置的开关,由页面控制器在 `processCheckBox` 状态变化时设置。

### 10.1 `Figure.py` — `set_mutual_exclusion_enabled(enabled)`
- 新增 `self._mutual_exclusion_enabled = False` (默认 OFF, 兼容 Filter / Fitting / Plotting / Simulation)
- 新增 setter 方法:
  - 启用时若两者都已勾选 → 取消 Original (保留 Processed, 与图表类型一致)
  - 关闭时不影响当前状态
- `_on_processing_state_changed` / `_on_orig_checkbox_clicked` / `_on_proc_checkbox_clicked` 三个处理器开头加 `if not self._mutual_exclusion_enabled: return`,OFF 时完全放行 (Filter 模式两种勾选都允许)

### 10.2 `ui_page_processing.py` — 页面控制器 wiring

```python
# 页面控制器拥有所有 widget 引用,无需跨模块传引用
self.dataprocessWg.processui.processCheckBox.stateChanged.connect(
    lambda state: self.figureWg.set_mutual_exclusion_enabled(bool(state))
)
```
- `bool(state)` 把 Qt 的 `0/1/2` 整数转成 Python `False/True`
- 初始状态 (Process 未勾) → mutual exclusion OFF, 默认行为兼容 Filter
- 用户勾 Process → mutual exclusion ON, 强制单选

### 10.3 跨页面行为表 (最终)

| 页面 | filterCheckBox | processCheckBox | mutual exclusion | Orig + Proc 关系 |
|---|---|---|---|---|
| Plotting | — (无) | — (无) | OFF (默认) | N/A (复选框被 `set_processing_state_enabled(False)` 禁用) |
| Simulation | — (无) | — (无) | OFF (默认) | N/A (同上) |
| Filter | ✓ | ✗ | OFF | 允许同时勾选用于对比 |
| Processing (未启动 Process) | ✓ | ✗ | OFF | 允许同时勾选 |
| Processing (Process 启动) | ✓ | ✓ | **ON** | **强制单选** |
| Fitting | ✓ | ✗ | OFF | 允许同时勾选 |

### 10.4 冒烟测试 16/16 通过

| 场景 | 期望 | 结果 |
|---|---|---|
| Filter-only (互斥 OFF) Orig✓ Proc✓ | 两者都勾选 (允许) | ✓ |
| Filter-only 用户点击 Orig (Proc 仍勾) | 两者都勾选 (不互斥) | ✓ |
| Process 激活时 Orig✓ Proc✓ | Orig 自动取消 | ✓ |
| Process 激活用户点击 Orig (Proc 仍勾) | Proc 自动取消 | ✓ |
| Process 激活用户点击 Proc (Orig 仍勾) | Orig 自动取消 | ✓ |
| Process 激活已单选时点击 | 不动 | ✓ |

---

## 文件清单

| 文件 | 主要改动 |
|---|---|
| `EIS/FilterFile/Filter.py` | check 方法委托、`resolve_column` 使用、DS 支持、标题布局、Generate Compare 网格 UI |
| `EIS/FilterFile/Filterfun.py` | `calculate_multi_filter_comparison_data` 接受 `custom_filters_config`、DS 数据类型支持 |
| `EIS/Other/Datacheck.py` | `resolve_column` 工具函数、`detect_data_type_from_columns` 数据类型自动识别 |
| `EIS/FigureFile/Figure.py` | `getsignal` 后自动同步 `datatypeComboBox` 到处理输出类型 (`_auto_set_datatype_combobox`) + 跟随复选框动态切换 + Original/Processed 互斥 (`clicked` 处理器 + `blockSignals`) + 默认 Processed (`_apply_default_checkbox_state`) + 互斥规则条件化 (`set_mutual_exclusion_enabled`) |
| `EIS/ProcessingFile/Processing.py` | (无直接改动) — 业务侧受益于 Figure 的自动同步,`databasecreat` 输出 `process_applied: True` 标记即被新逻辑识别 |
| `GUI/pages/ui_page_processing.py` | 新增 `processCheckBox.stateChanged → figureWg.set_mutual_exclusion_enabled` 接线,作为"Process 激活"信号 |

---

## 关键设计决策

1. **方法选择与参数编辑解耦** — 每个方法的复选框和参数编辑框独立,不再依赖"先点列表 → 再编辑参数"
2. **网格布局 5 列** — 横向空间最大化利用,所有 13 个方法一目了然
3. **MAX_COMPARE_METHODS = 5** — 与原 3×5 子图布局保持兼容
4. **`resolve_column` 列名容差** — 兼容 EIS/DS 的多种列名变体 (大小写、空格、单位)
5. **`data_type` 自动识别** — 通过列名特征自动判定 EIS/DS,避免用户手动切换

6. **跨模块数据类型自动同步** — Processing 计算改变数据类型后,Figure 的 `datatypeComboBox` 立即跟随切换,无需用户手动操作;`detect_data_type_from_columns` 优先取已处理条目 (奇数索引 + `process_applied=True`),保证与"用户实际想看的输出"一致

7. **检测范围跟随可见性** — `_auto_set_datatype_combobox` 不再扫描全部 plotdata,而是按 `_display_synthetic` + Original/Processed 复选框过滤出**当前可见**的子集,只对该子集做类型识别,避免"勾选只显示 Original 时图表却是 DS 布局"的错位

8. **互斥规则条件化 (而非全局强制)** — Original/Processed 互斥仅在 Process 激活时启用,Filter / Fitting 仍允许两者同时勾选用于对比;通过 `_mutual_exclusion_enabled` 标志 + 页面控制器 wiring 实现,Fitting / Plotting / Simulation 页面零改动即可保持原行为

9. **clicked + stateChanged 双信号协同** — `clicked` 仅响应用户点击,用于互斥调整 (避免与程序化 `setChecked` 递归);`stateChanged` 响应任何状态变化,用于自动重绘;`blockSignals` 抑制被取消方的 `stateChanged`,让"瞬时同时勾选"状态不触发错误重绘

10. **blockSignals 抑制 + 手动重绘** — 互斥时取消另一方必须用 `blockSignals`,否则 `_on_processing_state_changed` 会看到"两者都勾选"的瞬时态画一次错图;取消后由 click handler 手动 `_auto_set_datatype_combobox` + `drawfigure` 用最终单选状态重绘

---

## 11. 代码评审与重构建议 (本轮新增)

> 本节是**评审性内容**,记录当前实现的优点、问题、改进方向及对应风险。
> 未对代码做任何修改,仅作为下一轮重构的参考。
> 详见后续 12 (风险) 与 13 (实施顺序) 章节。

### 11.1 整体评估

实现**功能完整**,5 个场景 (Input / Simulation / Filter / Processing 未启动 / Processing 启动 / Fitting) 都正确分流,冒烟测试 16+7+7 全过。但**内部机制偏"叠加式"** — 3 轮迭代每次新增一层规则,没有回头把 1.x 改成更优雅的方案,最终产生了 3 个独立的"自动"机制 (`_auto_set_datatype_combobox` / `_apply_default_checkbox_state` / `set_mutual_exclusion_enabled`) 和 4 套状态标志 (`_processing_state_enabled` / `_display_synthetic` / `_mutual_exclusion_enabled` / `_syncing_display` 隐含)。

### 11.2 优点 (保留)

1. **Datacheck.py 集中列名容差** — `detect_data_type_from_columns` 与 `check5` / `resolve_column` 复用同一份列名清单,没有在两个文件里维护双份
2. **DataInfo 携带 `process_applied` 标记** — 类型识别无需新建一套通信协议,复用现有 `message` 字段
3. **`clicked` + `stateChanged` 双信号** — Qt 处理"用户交互 vs 程序化"分离的标准做法
4. **条件化互斥 (默认 OFF)** — 让 Plotting / Simulation / Fitting 页面零改动即保持原行为,扩展性好
5. **可逆式默认** — `_apply_default_checkbox_state` 只在"两者都勾"时改 Original,不动用户的单选偏好

### 11.3 改进建议 (8 条)

#### 改进 1:抽 `_compute_visible_indices()` 公共方法

**问题**: 3 处实现同一段 3 分支可见性过滤逻辑 (`_auto_set_datatype_combobox` / `_filter_synthetic_for_display` / `_apply_default_checkbox_state` 间接通过 detect_data_type_from_columns),共 30+ 行重复代码。

**建议**: 抽一个公共方法统一返回 `visible_data` / `visible_info`,3 处调用即可。

```python
def _compute_visible_indices(self, mode='plot'):
    """
    mode='plot'   → (visible_data, visible_info),用于绘图
    mode='detect' → (visible_data,),用于类型识别
    mode='pair'   → (orig_data, proc_data),用于成对类型比较
    """
    if mode not in ('plot', 'detect', 'pair'):
        raise ValueError(f"Invalid mode: {mode}")
    # 单点实现 3 分支 (_display_synthetic / 复选框 / message 兜底)
```

**收益**: 消除 30+ 行重复代码,修改可见性规则时只需改一处。

---

#### 改进 2:`detect_paired_types()` 合并成对类型检测

**问题**: `_apply_default_checkbox_state` 对 Original 和 Processed 各调一次 `detect_data_type_from_columns`,等于扫描两次。意图 ("判断一对数据的类型") 不够明确。

**建议**: Datacheck.py 新增 `detect_paired_types(plotdata, message) → (orig_type, proc_type, differ)`,一次调用返回。

```python
def detect_paired_types(plotdata, message=None):
    """返回 (orig_type, proc_type, differ):
    - differ 仅在 orig_type != proc_type 且都不为 UNKNOWN 时为 True
    """
    if not plotdata:
        return (None, None, False)
    if len(plotdata) >= 2:
        o_type = detect_data_type_from_columns([plotdata[0]], message[:1] if message else None)
        p_type = detect_data_type_from_columns([plotdata[1]], message[1:2] if message else None)
    else:
        o_type = detect_data_type_from_columns(plotdata, message)
        p_type = None
    differ = (o_type not in (None, 'UNKNOWN')
              and p_type not in (None, 'UNKNOWN')
              and o_type != p_type)
    return (o_type, p_type, differ)
```

**关键约束**: `differ` 必须要求**两者都识别成功**才算"类型不同",否则任何 UNKNOWN 都触发默认 Processed 会破坏 Fitting 页面"两者都勾选对比"行为。

**收益**: 避免重复 IO 与列名查找,意图更明确。

---

#### 改进 3:合并 3 auto → `_sync_display_to_data()`

**问题**: 当前有 3 个独立 auto:
- `_auto_set_datatype_combobox` (图表类型跟随可见数据)
- `_apply_default_checkbox_state` (类型不同时默认 Processed)
- `set_mutual_exclusion_enabled` (强制单选)

调用顺序敏感 (先切 ComboBox 才能画图),但分散在 3 个方法里,debug 时要追 3 处。

**建议**: 合并为单一 `_sync_display_to_data()`,按"数据 → 复选框默认 → 图表类型 → 重绘"的顺序执行一次。

```python
def __init__(self):
    self._syncing_display = False  # 递归防护

def _sync_display_to_data(self):
    if self._syncing_display:
        return  # 防止递归
    self._syncing_display = True
    try:
        # Step 1: 可见性
        visible = self._compute_visible_indices()
        # Step 2: 类型识别
        orig_t, proc_t, differ = detect_paired_types(visible.data, visible.info)
        # Step 3: 互斥 (改 checkbox)
        if self._mutual_exclusion_enabled and both_checked:
            self.origindataCheckBox.setChecked(False)  # blockSignals 已内置
        # Step 4: 切 ComboBox (触发 selectionchange → Nyquist/Bode 更新)
        new_type = type_to_combo.get(visible_type)
        if new_type and current != new_type:
            self.datatypeComboBox.setCurrentIndex(...)
        # Step 5: 画图 (此时 ComboBox 已切好)
        self.drawfigure()
    finally:
        self._syncing_display = False
```

**收益**: 单一入口,状态变更只在一处发生,debug 时不用追 3 个方法的调用顺序。

---

#### 改进 4:用 `QButtonGroup.setExclusive(True)` 取代手动互斥

**问题**: `_on_orig/proc_checkbox_clicked` 里 `blockSignals` + `try/finally` + 手动重绘,每次写 6 行,共 30+ 行手动互斥代码。

**建议**: Qt 的 `QButtonGroup.setExclusive(True)` 是处理"互斥勾选"的标准方案。

```python
# __init__ 中创建 group,但默认 exclusive=False
self._orig_proc_group = QButtonGroup(self)
self._orig_proc_group.setExclusive(False)  # 默认
self._orig_proc_group.addButton(self.figuregui.origindataCheckBox, id=1)
self._orig_proc_group.addButton(self.figuregui.processeddataCheckBox, id=2)

def set_mutual_exclusion_enabled(self, enabled):
    self._mutual_exclusion_enabled = bool(enabled)
    self._orig_proc_group.setExclusive(enabled)  # Qt 自动互斥
    if enabled and both_checked:
        self.origindataCheckBox.blockSignals(True)
        try:
            self.origindataCheckBox.setChecked(False)
        finally:
            self.origindataCheckBox.blockSignals(False)
```

**收益**: click handler 缩到 3-4 行,Qt 原生行为可靠。

---

#### 改进 5:数据驱动互斥 (不推荐,仅作记录)

**思路**: 不靠页面控制器 wiring,而是让 Figure 主动从 `dataInfo.process_method` 字段反推"是否 Process 模式"。

```python
PROCESSING_METHODS = {
    'Paraplate', 'DieMat', 'Three-Solution', 'TLcalculateEPS',
    'KKforEIS', 'CalibrateSystem', 'CalibrateRFImpedance',
    'CalcRFImpedance'
}

def _infer_origin_from_message(self, message):
    if not message:
        return 'unknown'
    last_method = message[-1].get('process_method', '')
    return 'process' if last_method in PROCESSING_METHODS else 'unknown'
```

**为什么不推荐**: silent failure 风险高 — 若新方法忘记设 `process_method` 或更新白名单,**不报错**但行为变样。

---

#### 改进 6:合并为 `set_data_origin()` 单一 API

**问题**: 4 个 setter (`set_processing_state_enabled` / `set_display_synthetic` / `set_mutual_exclusion_enabled` / `set_data_origin` (新建)) 含义相近但分散,新增页面要记 4 件事。

**建议**: 用枚举 `origin ∈ {'input', 'simulation', 'filter', 'process', 'fit'}` 统一入口,内部按 origin 自动决定 4 套状态。

```python
def set_data_origin(self, origin):
    if origin not in ('input', 'simulation', 'filter', 'process', 'fit'):
        raise ValueError(f"Invalid origin: {origin}")
    if origin in ('input', 'simulation'):
        self.set_processing_state_enabled(False)
        self.set_display_synthetic(False)
        self.set_mutual_exclusion_enabled(False)
    elif origin == 'process':
        self.set_processing_state_enabled(True)
        self.set_display_synthetic(True)
        self.set_mutual_exclusion_enabled(True)
    else:  # 'filter' or 'fit'
        self.set_processing_state_enabled(True)
        self.set_display_synthetic(True)
        self.set_mutual_exclusion_enabled(False)
```

**注意**: 必须先**全量 grep 现有 setter 调用点**再替换,避免遗漏导致 silent regression。

---

#### 改进 7:集成测试覆盖"渲染"而不只是"状态"

**问题**: 当前 16+7+7 冒烟测试只验证复选框/ComboBox 状态,没验证画布最终渲染是否正确。理论上 `_auto_set_datatype_combobox` 切到 DS 布局,但 `drawfigure` 拿到错的 data 仍会画错图。

**建议**: 增加集成测试,模拟 Paraplate 数据到达,断言 matplotlib 的 `ax.lines` 中只含 DS 列、没 EIS 列残留。

```python
@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')

def test_paraplate_draws_ds():
    figure.getsignal(plotdata_eis, plotdata_ds_paraplate, message_with_process_applied)
    # 验证 ComboBox
    assert figure.figuregui.datatypeComboBox.currentText() == 'f-Epsilon,Sigma'
    # 验证 visible data 是 DS 列
    visible = figure._compute_visible_indices()
    assert 'EpsRE[-]' in visible.data[0].columns
```

**关键**: 不断言 `ax.lines` 数量 (脆弱),断言"包含期望的列名"。

---

#### 改进 8:文档加架构总览章节

**问题**: 文档 370 行,按时间顺序记录 10 章节。读者想找"互斥规则怎么工作"得读 9 + 10 两节,章节之间有上下文依赖。

**建议**: 开头加一个"架构总览"章节,列出 5 个自动机制 + 4 个状态标志 + 1 个图类型检测的关系图,新人 5 分钟能定位。

---

### 11.4 备选方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|---|---|---|---|
| **当前实现** | 已工作,测试覆盖 | 3 处可见性重复 / 4 套状态标志 / wiring 脆弱 | ⭐⭐ |
| **改进 1+2+3:合并 auto** | 代码量减半,意图清晰 | 一次性大改 | ⭐⭐⭐⭐ |
| **改进 4B:用 QButtonGroup** | 互斥逻辑 0 行手动代码 | 需添加 group 初始化 | ⭐⭐⭐⭐⭐ |
| **改进 6:枚举 data_origin** | API 1 个而非 4 个 | 需改 4 个页面的 wiring | ⭐⭐⭐ |

**最推荐组合**: 改进 4B (QButtonGroup) + 改进 6 (合并为 set_data_origin) — 把 4 套状态标志和手动互斥代码全部消掉,预计能减 50+ 行。

---

## 12. 改进方案风险与具体防范 (本轮新增)

> 本节逐条列出 11.3 中 8 条改进建议的**具体风险**和**必须做的防范措施**。
> 实施前应完整阅读本节。

### 12.1 风险矩阵

| 改进 | 改动范围 | 风险 | 必须做的防范 |
|---|---|---|---|
| 1. 抽 `_compute_visible_indices` | Figure.py 内部 3 处 | 🟡 中 | 保留外部行为不变;input 模式单 Original 路径需独立测试 |
| 2. `detect_paired_types` | Datacheck.py + Figure.py | 🟢 低 | 边界情况 (单条、message 缺失、UNKNOWN 类型) 需单元测试 |
| 3. 合并 3 auto → `_sync_display_to_data` | Figure.py 大改 | 🟠 中高 | 调用顺序契约 + 递归防护 |
| 4. QButtonGroup.setExclusive | Figure.py 中改 | 🟠 中高 | 禁用状态下 exclusive 行为 + 程序化 setChecked 兼容性 |
| 5. 数据驱动互斥 | Figure.py + 4 页面 | 🔴 高 | process_method 字段稳定契约 + 新模块行为定义 |
| 6. 合并为 `set_data_origin` | Figure.py API + 4 页面 | 🟡 中 | 现有 setter 调用点全量替换清单 |
| 7. 集成测试 | 测试目录 | 🟢 低 | mock matplotlib 抗实现变化 |
| 8. 文档重构 | 文档 | 🟢 低 | 总览 vs 详细章节一致性维护 |

---

### 12.2 改进 1:`_compute_visible_indices` 风险与防范

**风险点**:
- 3 处"可见性"语义可能不完全一致 (`_filter_synthetic_for_display` / `_auto_set_datatype_combobox` / `_apply_default_checkbox_state`)
- 边界情况: 空 message、长度不匹配、单条数据 (n=1)

**具体防范**:
```python
# 防范 1: 在 helper 中显式列出 3 种情形,任何不匹配立即报错
def _compute_visible_indices(self, mode='plot'):
    if mode not in ('plot', 'detect', 'pair'):
        raise ValueError(f"Invalid mode: {mode}")
```

```python
# 防范 2: 单元测试覆盖 5 个边界
def test_compute_visible_indices():
    # (1) _display_synthetic=False, message=[]  → 只 Original
    # (2) _display_synthetic=True,  both勾选    → 两者都返回
    # (3) _display_synthetic=True,  只 Orig     → 只 Orig
    # (4) _display_synthetic=True,  message 缺失 → 兜底全返回
    # (5) 单条数据 (n=1)                       → 仅该条
```

**对其他模块影响**: 无外部 API 变化,下游模块零改动。

---

### 12.3 改进 2:`detect_paired_types` 风险与防范

**风险点**:
- Original 是 UNKNOWN 时与 Processed 比较会误判为"类型不同"
- 单条数据时不应崩溃
- `message` 长度不匹配 plotdata 时可能越界

**具体防范**:
```python
def detect_paired_types(plotdata, message=None):
    if not plotdata:
        return (None, None, False)
    if len(plotdata) >= 2:
        o_type = detect_data_type_from_columns([plotdata[0]], message[:1] if message else None)
        p_type = detect_data_type_from_columns([plotdata[1]], message[1:2] if message else None)
    else:
        o_type = detect_data_type_from_columns(plotdata, message)
        p_type = None
    differ = (o_type not in (None, 'UNKNOWN')
              and p_type not in (None, 'UNKNOWN')
              and o_type != p_type)
    return (o_type, p_type, differ)
```

**关键**: `differ` 必须**两者都识别成功**才算"类型不同"。

**对其他模块影响**: 仅影响 `_apply_default_checkbox_state` (Figure 内部);`check5` 调用方零改动。

---

### 12.4 改进 3:合并 3 auto 风险与防范

**风险点**:
- 递归触发: `setChecked(False)` 触发 `stateChanged` → 再调 `_sync_display_to_data` → 死循环
- 调用顺序敏感: 必须先互斥检查 → 再切 ComboBox → 最后画图
- `_on_processing_state_changed` 的"both checked 早退"逻辑放哪?

**具体防范**:
```python
# 防范 1: 临时锁防递归
def __init__(self):
    self._syncing_display = False

def _sync_display_to_data(self):
    if self._syncing_display:
        return
    self._syncing_display = True
    try:
        # Step 1: 互斥/默认 (改 checkbox 状态)
        if self._mutual_exclusion_enabled and both_checked:
            self.origindataCheckBox.setChecked(False)
        # Step 2: 类型识别
        type_to_switch = self._detect_type_from_visible()
        # Step 3: 切 ComboBox
        if type_to_switch is not None and current != type_to_switch:
            self.datatypeComboBox.setCurrentIndex(...)
        # Step 4: 画图
        self.drawfigure()
    finally:
        self._syncing_display = False
```

```python
# 防范 2: 保留 _auto_set_datatype_combobox 和 _apply_default_checkbox_state 为 thin wrapper
# 先注释 (不要删),过几个迭代稳定后再删
def _auto_set_datatype_combobox(self):
    """DEPRECATED: use _sync_display_to_data()"""
    self._sync_display_to_data()
```

**对其他模块影响**: 调用点变多,所有调 `_auto_set_datatype_combobox()` 的地方 (2-3 处) 必须改,**容易漏改**。建议先 grep 列出:
```bash
grep -rn "_auto_set_datatype_combobox\|_apply_default_checkbox_state" --include="*.py"
```

---

### 12.5 改进 4:QButtonGroup.setExclusive 风险与防范

**风险点**:
- `setChecked(False)` 程序化时不触发互斥 (这是我们想要的,但要确认)
- 禁用状态下点击不响应,但 `setChecked()` 程序化设置仍会触发互斥
- PyQt5/PyQt6/PySide6 行为差异

**具体防范**:
```python
# 防范 1: 在 __init__ 中创建 group,但默认 exclusive=False
self._orig_proc_group = QButtonGroup(self)
self._orig_proc_group.setExclusive(False)
self._orig_proc_group.addButton(self.figuregui.origindataCheckBox, id=1)
self._orig_proc_group.addButton(self.figuregui.processeddataCheckBox, id=2)

def set_mutual_exclusion_enabled(self, enabled):
    self._mutual_exclusion_enabled = bool(enabled)
    self._orig_proc_group.setExclusive(enabled)
    if enabled and both_checked:
        self.origindataCheckBox.blockSignals(True)
        try:
            self.origindataCheckBox.setChecked(False)
        finally:
            self.origindataCheckBox.blockSignals(False)
```

```python
# 防范 2: 禁用 checkbox 时确保 group 不互斥
def set_processing_state_enabled(self, enabled):
    self._processing_state_enabled = enabled
    if not enabled:
        self._orig_proc_group.setExclusive(False)
    self.figuregui.origindataCheckBox.setEnabled(enabled)
    self.figuregui.processeddataCheckBox.setEnabled(enabled)
```

```python
# 防范 3: 单元测试覆盖 4 种场景
def test_qbuttongroup_exclusive():
    # (1) exclusive=True, 用户点 Orig, Proc 自动取消
    # (2) exclusive=True, 程序化 setChecked(False), 不应取消对方
    # (3) exclusive=False, 用户点 Orig, 两者都勾选 (不互斥)
    # (4) exclusive=True 但 checkbox 禁用, setChecked 程序化应不取消对方
```

**对其他模块影响**: 改动仅 Figure.py 内部,最干净的重构之一 (消掉 30+ 行 click handler 代码)。

---

### 12.6 改进 5:数据驱动互斥风险与防范

**风险点**:
- `process_method` 字段是约定,新方法忘记设 → silent failure
- Filter 与 Process 链式处理时 `message` 两种标记共存
- 第三方模块未遵循约定

**具体防范**:
```python
# 防范 1: 显式白名单
PROCESSING_METHODS = {
    'Paraplate', 'DieMat', 'Three-Solution', 'TLcalculateEPS',
    'KKforEIS', 'CalibrateSystem', 'CalibrateRFImpedance',
    'CalcRFImpedance'
}
FILTERING_METHODS = {
    'Savitzky-Golay', 'Median', 'Wiener', 'Butterworth',
    'CubicSpline', 'ArithmeticAverage', 'SlidingAverage',
    'MedianAverage', 'AmplitudeLimitingAverage',
    'FirstOrderLag', 'WeightedAverage', 'ShakeOff',
    'AmplitudeLimitingShakeOff'
}
```

```python
# 防范 2: 在 Processing / Filter / Fitting 的 databasecreat 中加一致性检查
def databasecreat(...):
    if process_method not in PROCESSING_METHODS:
        raise ValueError(
            f"process_method '{process_method}' not in known Processing methods. "
            f"Add to PROCESSING_METHODS in Datacheck.py to enable mutual exclusion."
        )
```

**对其他模块影响**: 重大 — 3 个模块的 `databasecreat` 必须保证 `process_method` 字段;白名单维护成本高。

**结论**: 不推荐采用 (silent failure + 白名单维护成本)。

---

### 12.7 改进 6:`set_data_origin` 风险与防范

**风险点**:
- 'input' vs 'simulation' 当前同一行为,未来可能区分
- 'filter' vs 'fit' 当前同一行为,未来可能区分
- 现有 setter 调用点必须全量搜索

**具体防范**:
```bash
# 防范 1: 重构前先全量搜索
grep -rn "set_processing_state_enabled\|set_display_synthetic\|set_mutual_exclusion_enabled" --include="*.py"
```

预期输出 (已确认):
- `set_processing_state_enabled` → `ui_page_plotting.py`, `ui_page_simulation.py`
- `set_display_synthetic` → 同上
- `set_mutual_exclusion_enabled` → `ui_page_processing.py`

```python
# 防范 2: 保留原 setter 为 thin wrapper
def set_processing_state_enabled(self, enabled):
    self._processing_state_enabled = enabled
    if not enabled:
        self._orig_proc_group.setExclusive(False)
    self.figuregui.origindataCheckBox.setEnabled(enabled)
    self.figuregui.processeddataCheckBox.setEnabled(enabled)
```

**对其他模块影响**: 改动页面控制器 4 个文件;如果遗漏调用点,silent regression (行为不报错但变样)。

---

### 12.8 改进 7:集成测试风险与防范

**风险点**:
- 断言 `ax.lines` 数量脆弱 (实现细节变化就挂)
- matplotlib 状态跨测试污染

**具体防范**:
```python
# 防范 1: 用 matplotlib.testing 隔离
import matplotlib
matplotlib.use('Agg')  # 无头后端

import pytest
@pytest.fixture(autouse=True)
def close_figures():
    yield
    import matplotlib.pyplot as plt
    plt.close('all')
```

```python
# 防范 2: 不断言 ax.lines 数量,断言"包含期望的列名"
def test_paraplate_draws_ds():
    figure.getsignal(plotdata_eis, plotdata_ds_paraplate, message_with_process_applied)
    assert figure.figuregui.datatypeComboBox.currentText() == 'f-Epsilon,Sigma'
    visible = figure._compute_visible_indices()
    assert 'EpsRE[-]' in visible.data[0].columns
```

**对其他模块影响**: 纯测试代码,零影响;CI 环境需保证 matplotlib 可用。

---

### 12.9 改进 8:文档重构风险与防范

**风险点**:
- 总览 vs 详细章节不一致 (新加总览后,原 1-10 章节更新时总览可能忘同步)

**具体防范**:
```markdown
# 在文档开头加 "Convention" 章节
## 文档维护约定
- 第 0 章 (总览): 手动维护,重大重构时更新
- 第 1-13 章: 每次具体改动时增量更新
- 改动 → 同步两处是 reviewer 必检项
```

**对其他模块影响**: 零代码影响。

---

## 13. 跨改进依赖与实施顺序 (本轮新增)

### 13.1 跨改进的依赖关系

```
   改进 1 ─┐
           ├─→ 改进 3 ─→ 改进 6 (合并 API)
   改进 2 ─┘
   
   改进 4 (QButtonGroup) ─→ 改进 6 (合并 API,消掉 set_mutual_exclusion_enabled)
   
   改进 5 (数据驱动) ←→ 改进 6 (冲突:都改 API)
```

### 13.2 推荐实施顺序

| 步骤 | 改进 | 风险 | 工作量 | 依赖 |
|---|---|---|---|---|
| ① | 改进 7 (集成测试) | 🟢 低 | 小 | 无 |
| ② | 改进 1 (抽 visible helper) | 🟡 中 | 中 | 无 |
| ③ | 改进 2 (paired types) | 🟢 低 | 小 | 无 |
| ④ | 改进 4 (QButtonGroup) | 🟠 中 | 中 | ② |
| ⑤ | 改进 3 (合并 auto) | 🟠 中 | 中 | ①②④ |
| ⑥ | 改进 6 (set_data_origin) | 🟡 中 | 大 | ⑤ |
| ⑦ | 改进 8 (文档总览) | 🟢 低 | 小 | ⑥ |
| **跳过** | **改进 5 (数据驱动)** | 🔴 高 | — | 不推荐 |

### 13.3 总体结论

- **当前实现是"演进式正确"** — 每轮迭代都修对了前一版的问题,但 3 轮叠加后内部机制偏复杂
- **建议下一轮做一次"减法重构"**:
  1. 抽 `_compute_visible_indices` 公共方法 (消除 3 处重复)
  2. 用 `QButtonGroup.setExclusive(True)` 取代手动 `blockSignals` 互斥
  3. 把 4 个 setter 合并为 `set_data_origin`
- **这三步可在不改变外部行为的前提下**,把 `_on_orig/proc_checkbox_clicked` 和 `set_mutual_exclusion_enabled` 一起消掉,预期减 60-80 行代码,认知负担大幅降低

### 13.4 实施前必须做的准备工作

1. **全量 grep 列出所有 setter 调用点** (防范 改进 6)
   ```bash
   grep -rn "set_processing_state_enabled\|set_display_synthetic\|set_mutual_exclusion_enabled" --include="*.py"
   ```
2. **集成测试覆盖当前 16+7+7 行为** (建立 baseline,出问题能立即发现)
3. **在主分支建一个 `refactor/` 分支独立演进**,不与功能改动混在一起

### 13.5 评审时机

- 当前评审为"功能完成后的一次性回顾",**不是最终结论**
- 实施任何改进前应再 review 一遍本节,确认风险评估与具体代码上下文一致
- 改进 1-4 风险低、可独立 ship;改进 5-6 是"组合拳",建议等 1-4 稳定后再做

---

## 14. 后续小修复 + 集成测试落地 (本轮新增)

> 本章记录 11-13 章评审后**已实施**的小幅修复、批判性回退,以及 11.3 改进 7
> (集成测试) 的完整落地。

### 14.1 E 系列 — 简单修复与回退

**起因**: 11 章评审列出 5 个 E 级简单问题 (E1-E5),从易到难逐个验证必要性与安全性。

#### 已实施(必要)

| ID | 文件:行 | 修改 | 验证 |
|---|---|---|---|
| **E1** | `Filter.py:516` | 中英混合提示统一为英文 `f'[filtercompare] At most {MAX} methods allowed, truncated to the first {MAX}'` | 提示文本一致 |
| **E2** | `Figure.py:432-436` | General 模式下 Nyquist / BodeRe / BodeIm / BodePhy 按钮标签改为 `"(Disabled)"` | 与 selectionchange 其他分支标签格式统一 |
| **E4** | `Filter.py:45-61` `_parse_param_str` | 无效片段 (缺 `=`) 打印警告 `Skipping invalid parameter fragment: "X" (missing "=")` | 解析失败不再静默 |

#### 已回退(过度工程或破坏现有契约)

| ID | 原方案 | 回退原因 |
|---|---|---|
| **E3** | `set_mutual_exclusion_enabled` 启用时在 `setChecked(False)` 外加 `blockSignals` 抑制 `stateChanged` | ⚠️ **已重新评估** — 当时判断"重绘是必要"只对"画布已有数据"成立。在 processCheckBox 阶段画布可能仍空,触发重绘是用户没期望的行为(用户没点 Draw 按钮)。**修正**: 改为 E3 **应实施**,见 14.7 节完整 bug fix 记录。回退决定错。 |
| **E5** | `Datacheck.detect_data_type_from_columns` 改全索引扫描 `for i in range(len(data))` | 现有"奇数索引 = processed,偶数索引 = original"是**约定的文档化** (与 8.1 节"奇数索引 + process_applied=True"配对),改全扫描会失去约定文档化且无具体 bug 驱动,属于过度设计。回退后加注释强化"奇数位代表 Processed"约定 |

**教训 (修正版)**: "重绘必要" 判断必须先明确**画布当前状态** — 在画布仍空时,任何非用户主动触发的重绘都是错误行为;但在画布已有数据时,状态变化触发的重绘是正确的。E3 的回退没有区分这两种情况,被推翻。**M6 需补"是否触发 drawfigure"专项断言,而不是只测状态变化**。

---

### 14.2 F 系列 — UI 微调

#### F1 标签笔误 🟢 5min
[Figure.py:414](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/FigureFile/Figure.py#L414) — `'BodePhyOption': {'text': "Bode\n f-theta", ...}` 前面多一个空格,与其他三个标签 `"Bode\nf-Sigma"` 等不一致。

**修改**:
```python
# 改前
'BodePhyOption': {'text': "Bode\n f-theta", 'enabled': True, 'checked': True},
# 改后
'BodePhyOption': {'text': "Bode\nf-theta", 'enabled': True, 'checked': True},
```

---

#### F2 + M8 合并实施 🟢 15min

[Figure.py:663-680](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/FigureFile/Figure.py#L663-L680) `on_all_option_clicked` 重构 — 一并解决 F2 (4 行重复) 和 M8 (stateChanged 风暴)。

**改前** (10 行):
```python
def on_all_option_clicked(self):
    if self.figuregui.AllOption.isChecked():
        self.figuregui.NyquistOption.setChecked(True)
        self.figuregui.BodeReOption.setChecked(True)
        self.figuregui.BodeImOption.setChecked(True)
        self.figuregui.BodePhyOption.setChecked(True)
    else:
        # ... 4 行对称代码
```

**改后** (18 行,含注释):
```python
def on_all_option_clicked(self):
    state = self.figuregui.AllOption.isChecked()
    # 4 个 chart 按钮一次性同步,只触发一次重绘
    for btn in (
        self.figuregui.NyquistOption,
        self.figuregui.BodeReOption,
        self.figuregui.BodeImOption,
        self.figuregui.BodePhyOption,
    ):
        btn.blockSignals(True)
        try:
            btn.setChecked(state)
        finally:
            btn.blockSignals(False)
    # 主动重绘一次(替代 4 次 stateChanged 触发的 4 次重绘)
    if getattr(self, '_processing_state_enabled', True) and self.plotdata:
        self._auto_set_datatype_combobox()
        self.drawfigure()
```

**收益**:
- 4 次重绘 → 1 次(性能 + 行为更稳定)
- `blockSignals` 模式与 `_on_proc_checkbox_clicked` (line 245-249) 一致,**已 M6 验证安全**
- 不破坏 H2 计划(将来用 `QButtonGroup.setExclusive` 时可整体删掉这段)

---

### 14.3 M6 集成测试落地 🟡 2h — 11.3 改进 7 实施

> 11.3 改进 7 建议"集成测试覆盖渲染而非只是状态",本节记录完整实施。

**新增 2 个文件**(零修改任何已有源代码):

#### `EIS/FigureFile/Funtest/conftest.py` (55 行)
- 修复 `sys.path` 让 `import EIS.FigureFile.Figure` 可用(项目根 3 层上)
- `session-scoped` `qapp` fixture(Qt 禁止多实例,所有测试共享)
- `function-scoped` `fig_widget` fixture(每测试 fresh widget,tearDown 关闭)

#### `EIS/FigureFile/Funtest/test_figure_render.py` (12 tests, 5 组)

| 组 | 测试数 | 覆盖 |
|---|---|---|
| A: 类型自动切换 | 3 | Paraplate (EIS→DS) / Filter (EIS→EIS) / Input (无 process) 三场景 ComboBox 行为 |
| B: 互斥 | 2 | `set_mutual_exclusion_enabled(True/False)` 对 Original/Processed 复选框的影响 |
| C: 显示合成 | 2 | `set_display_synthetic(True/False)` 对 `_filter_synthetic_for_display` 的影响 |
| D: 过滤 helper | 2 | checkbox 状态过滤可见索引 (2-checkbox 状态空间) |
| E: 实际渲染 | 3 | `drawfigure` 后 matplotlib `fig.axes` 有 `Line2D` + xdata 与 `log10(freq)` 匹配 + 空数据不崩 |

**关键发现(M6 实战)**:
1. **UI 初始两 checkbox 都勾** (`ui_Figure.py:145,163` 实际验证) — 测试预期必须从这点出发
2. **Plotfun.py 硬编码列索引** 是隐式约定(写死 `colname[0..4]`),EIS 测试数据需 5 列 (FREQ, Rs, X, Phase, Z),DS 测试数据需 5 列 (因 `plotColeCole` 在 DS 模式也访问 `colname[4]`)
3. **`dataname` 含 "Fit"/"Simul"/"Filt" 走 `ax.plot` 分支**,否则走 `ax.scatter` (创建 `PathCollection` 而非 `Line2D`) — 测试 `total_lines > 0` 需用含 "Filt" 的 dataname
4. **Bode 图 `ax.get_xscale()=='log'` 但 `get_xdata()` 仍返回原始频率** — matplotlib 在 `set_xscale('log')` 后才在渲染时转换,内部 xdata 不变

**测试结果**: 12/12 passed in 11.21s

---

### 14.4 M6 后续补充 — AllOption 回归测试 🟢 5min

**新增文件**: `EIS/FigureFile/Funtest/test_all_option.py` (2 tests, 1 组)

> F2+M8 实施后,新增专项测试覆盖 `on_all_option_clicked` 重构路径。

| 测试 | 验证 |
|---|---|
| `test_all_option_true_checks_all_four_chart_buttons` | AllOption True → 4 个 chart 按钮同步勾上 |
| `test_all_option_false_unchecks_all_four_chart_buttons` | AllOption False → 4 个 chart 按钮同步取消 |

**意外发现** 🟠:
测试首次跑时(4 列 EIS 数据)触发 `IndexError: list index out of range` —
`plotX` 访问 `colname[4]`,但 4 列 DataFrame 只有 `colname[0..3]`。这正是 **M7 描述的列索引问题在生产场景的真实复现**:

```
用户操作: 4 列 EIS 数据 + 点 AllOption
  → plotZall → plotX → data[i][colname[4]] ❌ IndexError
```

测试用 5 列数据(与 `test_figure_render.py` 一致)规避,聚焦 F2+M8 行为而非渲染列数。**M7 价值进一步确认**,按既定计划暂不实施,留待 H1 一起做。

**测试结果**: 2/2 passed

---

### 14.5 测试套件总览

```
$ pytest EIS/FigureFile/Funtest/ -v
============================= 14 passed in 12.36s =============================
```

| 文件 | 测试数 |
|---|---|
| `test_figure_render.py` | 12 |
| `test_all_option.py` | 2 |
| **总计** | **14** |

---

### 14.6 11.3 改进 7 状态更新

| 改进 | 状态 | 备注 |
|---|---|---|
| 7. 集成测试覆盖渲染 | ✅ **已实施** | 见 14.3-14.5;M6 落地 + AllOption 补充 |
| 7.1 互斥切换不应触发 drawfigure | ✅ **已实施** | 见 14.7;回归 4 个测试,纠错 14.1 E3 回退 |

---

### 14.7 processCheckBox 勾选立即出图 — Bug Fix 🟠 中 30min

> **用户反馈**: 导入数据后还没选择任何处理方法,勾选 `processCheckBox` 立即看到图表。
> 期望流程: 选处理方法 → 点 Process 计算 → 点 Draw 绘图。processCheckBox 只是"激活 Process 模块",不应触发绘图。

#### 根因链

```
1. 导入数据
   → origindataCheckBox=True, processeddataCheckBox=True (M6 已验证)

2. 用户勾选 processCheckBox (还没选处理方法,没点 Process 按钮)
   → stateChanged 信号
   → lambda 调 set_mutual_exclusion_enabled(True)
   [GUI/pages/ui_page_processing.py:90-92]

3. set_mutual_exclusion_enabled 内部检查到"两都勾选"
   → origindataCheckBox.setChecked(False)  ← 强制单选
   [Figure.py:195]

4. origindataCheckBox 的 stateChanged 信号触发
   [Figure.py:122 已 connect 到 _on_processing_state_changed]

5. _on_processing_state_changed 槽执行 [Figure.py:198-217]
   → 检查 line 210-214 "互斥瞬时态": orig=False, proc=True
   → 不 return (因为不是"两都勾"的瞬时态)
   → line 215-217: _auto_set_datatype_combobox() + drawfigure()
   ❌ 立即出图
```

#### 14.1 E3 回退的判断错误

**原回退理由**: "重绘是必要的,block 掉会停留在旧状态"。
**错误原因**: 该判断只对**画布已有数据**场景成立。在 `processCheckBox` 切换阶段,用户还没点过 Draw 按钮,画布仍空,"必要重绘" 在这里实际是错误行为。

| 场景 | 画布状态 | 期望 | 旧行为 | 应有行为 |
|---|---|---|---|---|
| 切互斥 | 有数据 | 重绘(反映新单选) | ✅ 重绘 | ✅ 重绘 |
| 切互斥 | **空** | **不重绘** | ❌ 错重绘 | ✅ blockSignals 抑制 |

**E3 实际应实施**,原回退决定错。

#### 修复方案

[Figure.py:188-202](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/FigureFile/Figure.py#L188-L202) `set_mutual_exclusion_enabled` 内部 `setChecked(False)` 用 `blockSignals` 包围。

```python
# 改前
self._mutual_exclusion_enabled = bool(enabled)
if enabled:
    if (self.figuregui.origindataCheckBox.isChecked() and
            self.figuregui.processeddataCheckBox.isChecked()):
        # 注意:此处不要 blockSignals — ...
        self.figuregui.origindataCheckBox.setChecked(False)
        print('[Figure] mutual exclusion ON; ...')

# 改后
self._mutual_exclusion_enabled = bool(enabled)
if enabled:
    if (self.figuregui.origindataCheckBox.isChecked() and
            self.figuregui.processeddataCheckBox.isChecked()):
        # 用 blockSignals 抑制 stateChanged → _on_processing_state_changed → drawfigure。
        # 互斥规则切换是状态调整而非用户主动触发绘图,
        # 用户期望的流程是:选处理方法 → 点 Process 计算 → 点 Draw 绘图,
        # 切互斥只是"准备好"互斥规则,不应在此过程中重绘。
        # (这与 _on_proc_checkbox_clicked 内部 setChecked 的处理模式一致,见 line 244-252)
        self.figuregui.origindataCheckBox.blockSignals(True)
        try:
            self.figuregui.origindataCheckBox.setChecked(False)
        finally:
            self.figuregui.origindataCheckBox.blockSignals(False)
        print('[Figure] mutual exclusion ON; ...')
```

**关键设计**:
- `blockSignals` 模式与 `_on_proc_checkbox_clicked` (line 244-252) 内部完全一致,**已 M6 验证安全**
- 不影响:
  - 用户点 Original/Processed 复选框的互斥(click handler 内部已显式重绘)
  - 用户点 Draw 按钮的正常流程
  - getsignal 接收新数据后的自动重绘

#### 回归测试

**新增文件**: [EIS/FigureFile/Funtest/test_mutual_exclusion_redraw.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/FigureFile/Funtest/test_mutual_exclusion_redraw.py) (4 tests)

| 测试 | 验证 |
|---|---|
| `test_set_mutual_exclusion_true_does_not_trigger_drawfigure` | **核心 bug fix** — 勾选 processCheckBox 不再出图 |
| `test_set_mutual_exclusion_false_does_not_trigger_drawfigure` | 关闭互斥也不出图 |
| `test_mutual_exclusion_keeps_processed_checkbox_state` | 互斥契约仍生效(orig 取消,proc 保留) |
| `test_mutual_exclusion_no_op_when_already_single` | 单选时启用互斥无副作用 |

**测试设计要点**:
- 用 monkey-patch spy `widget.drawfigure` 计数,**不修改源代码**
- 复用 conftest.py 已有的 `fig_widget` fixture
- 不测试"用户真实点击"路径(`PyCheckBox2` 自定义控件无标准 `clicked` 信号,需 GUI 框架支持,超出本测试范围)
- 4 个测试已覆盖核心契约: 状态变化、状态保留、空操作

**测试结果**: 4/4 passed in 4.23s

---

### 14.8 测试套件总览(更新)

```
$ pytest EIS/FigureFile/Funtest/ -v
============================= 18 passed in ~13s =============================
```

| 文件 | 测试数 | 用途 |
|---|---|---|
| `test_figure_render.py` | 12 | M6 集成测试 (类型切换 / 互斥状态 / 显示合成 / 过滤 / 渲染) |
| `test_all_option.py` | 2 | F2+M8 重构后的 AllOption 回归 |
| `test_mutual_exclusion_redraw.py` | 4 | 14.7 互斥切换不重绘回归 |
| **总计** | **18** | |

---

### 14.9 TLcalibrate 列名变体支持 + 缺列友好诊断 (F4 + M9) 🟢 低 25min

**起因**: 用户数据列名变体(如 `'Rs'` 而非 `'Rs[ohm]'`)导致 `TLcalibrate` 报 `KeyError`;缺列时直接崩溃无任何提示。

**修改**:

#### `EIS/ProcessingFile/Processingfun.py` (TLcalibrate, line ~748-822)
- 顶部新增 `from EIS.Other.Datacheck import resolve_column`
- TLcalibrate 内 8 处硬编码列访问改用 `resolve_column`:
  - **refdata** 支持变体: `Rs[ohm]` / `RS[OHM]` / `Rs[Ω]` / `Rs` / `R`(5 种)
  - **refdata** 支持变体: `X[ohm]` / `X[OHM]` / `X[Ω]` / `X`(4 种)
  - **prodata** 同上
- 缺列时打印诊断信息(实际列名 + 期望列名)后 `continue`/`return`,**不抛 KeyError**

**关键设计**:
- 列名查找复用 Filter 模块已落地的 `resolve_column` 工具(F2 已验证鲁棒)
- 缺列 graceful degradation 而非 raise:与 TLcalibrate 的"循环每条 refdata"语义匹配(单条缺列跳过,其他继续)

**回归测试** (新建): [EIS/ProcessingFile/Funtest/test_tlcalibrate_columns.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/test_tlcalibrate_columns.py) (7 tests)

| 测试组 | 验证 |
|---|---|
| `TestTLcalibrateColumnVariants` (2) | 标准列名 + 变体列名都跑通 |
| `TestTLcalibrateMissingColumns` (3) | prodata 缺 X / refdata 缺 Rs / DS prodata 不崩 |
| `TestCheck5M10EntryCheck` (2) | check5 识别变体为 EIS、识别 DS |

---

### 14.10 Processing.py 入口弹 QMessageBox (M10 升级) 🟠 中 20min

**起因**: 14.9 修复了 KeyError,但用户反馈:`print` 警告不够友好,需要明确弹窗告诉用户"为什么失败 + 应该用什么方法"。

**修改** ([EIS/ProcessingFile/Processing.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processing.py) line 380-404):
- `RF Impedance Calibration` 入口 `check5(prodata) == 'DS'` 时:
  - 旧: 仅 `print("Need EIS data")` + return
  - 新: `QMessageBox.critical(self, "Data type error", "Need EIS data\nIf you have dielectric data, use 'RF Dielectric Calculation'")` + return
- `print` 保留为兜底(无 GUI 环境仍能查日志)
- 同步升级 `Reference data error` 分支为 `QMessageBox.warning`(类型不匹配时)

**关键设计**:
- 弹窗文本明确引导用户用正确方法(`RF Dielectric Calculation` for DS),降低"我数据是对的为什么失败"的疑惑
- `critical` 而非 `warning`:数据完全错配,不是配置问题,应阻止继续

---

### 14.11 数据检查重构 — 统一入口校验 (Phase 1+2+3) 🟠 中 1h

**起因**: 14.10 后用户问出关键问题:**"是否存在检查过多,重复提示的问题"**。审查发现:
- 8 个方法每个分支都嵌 `if/elif` 数据检查(check1/2/3/4/5/6)
- 数据要求散落:`TLcalibrate` 自己查、其它方法分散在 `Processingfun` 各函数
- 重复提示:refdata 类型错可能被多处拦截,每个提示一次

**目标**:
1. **每种方法只做一次数据检查**
2. **统一弹窗**(不再 critical/warning 混用、一次性报所有错)
3. **充分测试**(新校验器 + 入口 dispatcher)

**修改**:

#### Phase 1: `EIS/Other/Datacheck.py` 新增数据驱动校验器

新增 `METHOD_DATA_SPECS` 字典(line 363-398)集中描述 8 个方法的数据要求:
```python
METHOD_DATA_SPECS = {
    'Parallel Plate Capacitor': {'prodata_types': ['EIS', 'DS']},
    'System Calibration':       {'refdata_types': ['EIS']},
    'Dielectric Material Method': {'refdata_types': ['EIS'], 'freq_consistency': True},
    'Three-Solution Method':    {'refdata_types': ['EIS']},
    'RF Impedance Calibration': {'refdata_types': ['EIS'], 'prodata_types': ['EIS']},
    'RF Dielectric Calculation': {'prodata_types': ['EIS']},
    'RF Impedance Calculation': {'prodata_types': ['DS']},
    'K-K for EIS':              {'required_params': ['validation_parameter']},
}
```

新增 `validate_method_prereq(method_name, refdata, refdataname, prodata, params_info)` 函数:
- 返回 `(is_valid: bool, errors: list[str])`
- 一次报告所有问题(不识别的方法返回 `(True, [])` 向后兼容)
- 调用方负责把 errors 展示给用户(放在 `Processing.py` 入口)

#### Phase 2: `EIS/ProcessingFile/Processing.py` 重构 processing() (line 321-385)

```python
def processing(self):
    currentmethod = self.processui.processmethodComboBox.currentText()
    params_info = self.get_parameters_info()
    is_valid, errors = validate_method_prereq(
        currentmethod, self.refdata, self.refdataname, self.prodata, params_info
    )
    if not is_valid:
        QMessageBox.warning(
            self,
            f"{currentmethod}: Prerequisites not met",
            "Cannot start processing:\n\n" + "\n".join(f"  • {e}" for e in errors)
        )
        return
    # 业务逻辑:不再嵌校验
    if currentmethod == 'Parallel Plate Capacitor': ...
    elif currentmethod == 'RF Impedance Calibration': ...
```

**关键改进**:
- 8 个 if/elif 分支不再嵌任何 `check*()` 调用
- 校验失败:统一 `QMessageBox.warning` + errors 列表(支持"一次报所有错"的目标)
- 弹窗标题含方法名(便于用户定位)
- 14.10 的 `critical` 升级 → 14.11 改回 `warning`(更准确:数据问题应引导而非阻止)
- 不识别的方法静默 `return`(向后兼容)

#### Phase 3: 新建回归测试

**`EIS/ProcessingFile/Funtest/test_validate_method_prereq.py`** (25 tests)
- `TestValidPrereq` (9 parametrize) — 8 个有效方法 + K-K 参数齐
- `TestInvalidPrereq` (8) — 各方法数据不匹配场景
- `TestEdgeCases` (5) — 未知方法 / 多错一次报 / 无 refdata 跳过 ref 检查
- `TestProcessingDispatcher` (3) — Processing.processing() 集成

**`EIS/ProcessingFile/Funtest/test_processing_dialog.py`** (7 tests, 重写)
- `TestUnifiedEntryDialog` (4):
  - DS prodata → 统一 warning + errors 含 "DS" "EIS"
  - DS refdata → 统一 warning + errors 含 "Reference data type"
  - EIS 配齐 → 不弹窗,TLcalibrate 调用
  - 双错(ref+pro)→ 恰好 1 个 warning,errors ≥ 2 bullet
- `TestUnifiedEntryStaticCheck` (3):
  - Processing.py 含 "Cannot start processing" / "Prerequisites not met" / `validate_method_prereq` / `QMessageBox.warning`
  - Datacheck.py 导出 `METHOD_DATA_SPECS`(8 个方法全覆盖)
  - Datacheck.py 导出 `validate_method_prereq`(签名检查)

**测试设计要点**:
- `__new__` 绕过 QWidget `__init__`,构造最小可用实例
- `MagicMock` 完整模拟 `processui.processmethodComboBox`
- mock `TLcalibrate` 验证业务逻辑**不**被执行
- 静态检查防回退:关键字符串 / 数据驱动表必须存在

---

### 14.12 测试套件总览(更新)

```
$ pytest EIS/ProcessingFile/Funtest/ EIS/FigureFile/Funtest/ -v
============================= 43 passed in 4.53s =============================
```

| 文件 | 测试数 | 用途 |
|---|---|---|
| `test_processing_dialog.py` | 7 | 14.11 统一入口校验回归 (4 行为 + 3 静态) |
| `test_tlcalibrate_columns.py` | 7 | 14.9 TLcalibrate 列名变体 + 缺列诊断回归 |
| `test_validate_method_prereq.py` | 25 | 14.11 校验器单测(8 有效 + 8 无效 + 5 边界 + 3 dispatcher) |
| `test_mutual_exclusion_redraw.py` | 4 | 14.7 互斥切换不重绘 bug fix |
| `test_figure_render.py` | 12 | M6 集成测试 (类型切换 / 互斥 / 显示合成 / 过滤 / 渲染) |
| `test_all_option.py` | 2 | F2+M8 重构后的 AllOption 回归 |
| **总计** | **57** | |

---

## 文件清单(更新)

| 文件 | 主要改动 |
|---|---|
| `EIS/FilterFile/Filter.py` | check 方法委托、`resolve_column` 使用、DS 支持、标题布局、Generate Compare 网格 UI、**E1 (英文提示) + E4 (参数解析警告) + M4 (MAX_COMPARE_METHODS 截断, 6.2 节中)** |
| `EIS/FilterFile/Filterfun.py` | `calculate_multi_filter_comparison_data` 接受 `custom_filters_config`、DS 数据类型支持 |
| `EIS/Other/Datacheck.py` | `resolve_column` 工具函数、`detect_data_type_from_columns` 数据类型自动识别、**14.11 `METHOD_DATA_SPECS` + `validate_method_prereq` 统一校验器** |
| `EIS/FigureFile/Figure.py` | `getsignal` 后自动同步 `datatypeComboBox` 到处理输出类型 (`_auto_set_datatype_combobox`) + 跟随复选框动态切换 + Original/Processed 互斥 (`clicked` 处理器 + `blockSignals`) + 默认 Processed (`_apply_default_checkbox_state`) + 互斥规则条件化 (`set_mutual_exclusion_enabled`) + **E2 (General 按钮 Disabled 标签) + F1 (标签空格笔误) + F2+M8 (on_all_option_clicked 重构) + 14.7 (set_mutual_exclusion_enabled blockSignals bug fix)** |
| `EIS/FigureFile/ui_Figure.py` | (无逻辑改动) — 仅作为初始 checkbox 状态的事实源 |
| `EIS/ProcessingFile/Processing.py` | (无直接改动) — 业务侧受益于 Figure 的自动同步,`databasecreat` 输出 `process_applied: True` 标记即被新逻辑识别、**14.10 M10 升级(DS 数据 QMessageBox.critical) + 14.11 processing() 重构(统一 validate_method_prereq 入口 + QMessageBox.warning)** |
| `EIS/ProcessingFile/Processingfun.py` | (无直接改动)、**14.9 TLcalibrate 列名变体支持 + 缺列友好诊断(resolve_column 替换硬编码列名)** |
| `GUI/pages/ui_page_processing.py` | 新增 `processCheckBox.stateChanged → figureWg.set_mutual_exclusion_enabled` 接线,作为"Process 激活"信号 |
| `EIS/FigureFile/Funtest/conftest.py` | **(新增)** M6 集成测试基础设施 (sys.path + QApplication + FigWidget fixtures) |
| `EIS/FigureFile/Funtest/test_figure_render.py` | **(新增)** M6 集成测试 12 个用例 (类型切换 / 互斥 / 显示合成 / 过滤 / 渲染) |
| `EIS/FigureFile/Funtest/test_all_option.py` | **(新增)** F2+M8 重构后的 AllOption 回归测试 2 个用例 |
| `EIS/FigureFile/Funtest/test_mutual_exclusion_redraw.py` | **(新增)** 14.7 bug fix 的回归测试 4 个用例 (互斥切换不重绘) |
| `EIS/ProcessingFile/Funtest/test_tlcalibrate_columns.py` | **(新增)** 14.9 列名变体 + 缺列诊断回归 7 个用例 |
| `EIS/ProcessingFile/Funtest/test_validate_method_prereq.py` | **(新增)** 14.11 校验器单测 25 个用例 (8 有效 + 8 无效 + 5 边界 + 3 dispatcher) |
| `EIS/ProcessingFile/Funtest/test_processing_dialog.py` | **(新增/重写)** 14.11 统一入口 dispatcher 回归 7 个用例 (4 行为 + 3 静态) |
| `FILTER_COMPARE_UI_CHANGELOG.md` | (本文件) 11-13 章代码评审与重构建议 + **14 章后续小修复 + M6 集成测试 + 14.9 TLcalibrate + 14.10 M10 升级 + 14.11 统一入口重构** |

---

## 关键设计决策(更新)

(原 1-10 项保留,新增 11-14)

11. **简单修改需批判性评估** — E5 (全索引扫描) 因无 bug 驱动被回退是正确的;E3 (blockSignals) 原被回退是**错误**的,14.7 用户反馈证明当时判断漏了"画布可能为空"这一关键场景。"先做后验"比"防御性编程"更安全;但**"必要重绘"判断必须先明确画布当前状态**。

12. **集成测试的实战价值** — M6 在测试 `on_all_option_clicked` 路径时,当场复现了 `colname[4]` IndexError 崩溃(用 4 列 EIS 数据);14.7 互斥切换不重绘测试当场捕获 processCheckBox 勾选立即出图 bug。这都不是纸面问题,是真实可触发的生产 bug。**集成测试的价值在"早期发现 + 复现容易"**,不只是覆盖率数字。

13. **测试聚焦而非万能** — `test_all_option.py` 不验证渲染(由 `test_figure_render.py` 负责),只验证 AllOption 行为契约。`test_mutual_exclusion_redraw.py` 不验证具体绘图内容,只验证"drawfigure 调用次数"。聚焦测试让失败信息更明确,debug 时不需翻看整条 plot 链路。

14. **bug fix 反向驱动回退重新评估** — 14.7 用户反馈暴露了 14.1 E3 的回退决定错。**回退决定本身也应该作为"可被推翻的假设"**保留在文档中,而不是简单删除。当新证据出现,优先恢复 + 补回归测试,而不是固执于"已结案"。

15. **数据驱动的校验器优于硬编码分支** — 14.11 用 `METHOD_DATA_SPECS` 字典集中描述 8 个方法的数据要求(类型 / 频率一致性 / 必需参数),`validate_method_prereq` 通用函数复用。**新增方法只需在 dict 加 1 个 entry**,不用改校验代码;**改数据要求只改 dict 1 行**,不用改 8 个分支。硬编码 if/elif 校验器在第 3 个方法时就已经开始"哪个方法没测过"的疑问,数据驱动在第 8 个方法时仍然清晰。

16. **errors 列表"一次报所有错"优于"按一次发现一个"** — 14.11 重构后,用户双错(refdata + prodata 都不对)只看到 1 个弹窗,errors 列表含 2 条 bullet。**用户体验更友好**;**代码更简单**(不用写"先 refdata 错就 return,prodata 错永远看不到");**测试更易覆盖**(测 validate_method_prereq 时测 1 个函数 vs 测 8 个分支的"哪个先 return")。

17. **`critical` vs `warning` 的语义边界** — 14.10 升级时用 `critical` 弹"数据类型错"(我判断:"数据完全错配,应阻止")。14.11 改回 `warning`(理由:"数据问题应引导而非阻止")。**最终判断:`warning` 更准确**——`critical` 用于"用户操作可能导致数据丢失/不可逆后果"(如覆盖文件),数据错配只需告知用户正确路径,不构成 critical。这与 14.10 的 `print` 升级到 `critical` 的方向相反,**说明在用户问题(是否存在重复提示)的驱动下,critical 升级是过度反应**。

18. **静态检查防回退** — 14.11 测试中 `TestUnifiedEntryStaticCheck` 强制源码中必须含 "Cannot start processing" / "Prerequisites not met" / `validate_method_prereq` / `QMessageBox.warning` / `METHOD_DATA_SPECS` 等。**比单纯行为测试更鲁棒**:如果有人未来重构时删了 warning 改回 print,行为测试可能仍过(因为不弹窗也算"通过校验的数据不弹窗"的子集),但静态检查立刻挂。
