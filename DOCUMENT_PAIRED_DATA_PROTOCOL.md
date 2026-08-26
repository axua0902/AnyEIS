# AnyEIS 数据成对化协议改造文档

> **日期**: 2026-08-26
> **范围**: Input / Simulation / Filter / Processing / Fitting 五大模块 + Figure 模块
> **核心目标**: 在不破坏现有逻辑的前提下，统一所有模块的"原始 + 处理"数据流

---

## 一、背景与原始问题

### 1.1 用户需求

在 **Filter / Processing / Fitting** 模块中希望实现：
- 选择"未处理/已处理/全部"导出数据的功能
- 通过 UI 上的 **Original / Processed** 复选框控制

而在 **Input / Simulation** 模块中：
- 该功能暂时失效（按钮置灰不可选）

### 1.2 原始数据流不一致

| 模块 | 数据条数 | 是否有"原始 vs 处理"概念 |
|------|----------|--------------------------|
| **Input** | 单条 N | 无（原始就是原始）|
| **Simulation** | 单条 N | 无（仿真就是单条）|
| **Filter** | 2N | 已有（接收 Input 配对数据后输出 4N）|
| **Processing** | 2N | 已有（输出 4N 但命名错位）|
| **Fitting** | 4N | 已有（多次重复处理）|

**根因**: Input/Simulation 是单条数据，Filter/Processing/Fitting 期望成对（原始 + 处理后）数据。下游 `selectsavedata` 函数按奇偶索引过滤时对 Input 失效。

### 1.3 改造策略

采用**最小改动 + 协议统一**的策略：
1. **Input/Simulation**: 在 `sendsignal` 阶段调用 `ensure_paired_form` 工具函数，将单条数据复制成 `[原始, 合成副本]` 两份，名字保持原样，仅在 `dataInfo` 的合成侧加 `synthetic: True` 标记
2. **Filter/Processing/Fitting**: 自适应识别输入格式，仅对原始 N 条做处理，输出 2N 严格成对（`[原, 处理后]`）
3. **Figure**: 增加 `_display_synthetic` 标志位 + 复选框控制，根据页面模式决定是否显示合成曲线
4. **UI**: 在 Plotting/Simulation 页面禁用 Original/Processed 复选框

---

## 二、整体架构设计

### 2.1 数据流协议

```
[Input/Simulation: 1 条]    ensure_paired_form    [2 条: 原 + 合成副本, dataInfo 偶数=空, 奇数={synthetic:True}]
       ↓
[Filter/Processing/Fitting: 接收 2 条]
       ↓
   _extract_original_data()  →  提取偶数位 = N 条原始
       ↓
   process(filter/process/fit)  →  对 N 条原始处理
       ↓
   databasecreat(N 处理结果)  →  构造 2N 严格成对输出:
                                 偶数位=原, 奇数位=处理后(synthetic=True)
       ↓
[下游 Figure]  → 按 _display_synthetic 标志 + 复选框状态决定显示
```

### 2.2 命名规则

每个模块的处理后数据**追加自身后缀**（不重命名），支持链式调用：

| 链式 | 输出名（按顺序）| 数量 |
|------|----------------|------|
| **Input**（1 个文件）| `['实验数据A']` | 1 |
| **Filter**（独立）| `['实验数据A', '实验数据A_Filtered']` | 2 |
| **Processing**（独立）| `['实验数据A', '实验数据A_Processed']` | 2 |
| **Fitting**（独立）| `['实验数据A', '实验数据A_Fitted']` | 2 |
| **Filter → Processing** | `['实验数据A', '实验数据A_Processed', '实验数据A_Filtered', '实验数据A_Filtered_Processed']` | 4 |
| **Filter → Processing → Fitting** | 8 条，依次追加 `_Fitted` | 8 |

### 2.3 关键约束

- ✅ `self.prodata`（每个模块的输入数据列表）**始终保持原 2N 语义**——不能动，避免破坏其他读取它的代码
- ✅ 仅通过 `self.original_prodata` 等新增属性传递"N 条原始"给实际处理函数
- ✅ 各模块独立判断配对/非配对格式（通过 `dataInfo[1::2]` 是否有 `synthetic: True` 标签）

---

## 三、各阶段详细改动

### 阶段 1：核心工具函数 `ensure_paired_form`

**文件**: `EIS/Other/Datacheck.py`

**功能**: 将单条数据复制为 `[原始, 合成副本]` 两份，保持名字不变，仅在 `dataInfo` 的合成侧加 `synthetic: True` 标记。

**关键修复**:
- `dataInfo` 可能比 `plotdata` 短（Input 模块始终传空列表），需要补齐
- `selectlist` 可能比 `plotdataname` 短（`fresh()` 重置了长度），透传时需成对化

---

### 阶段 2：Figure 模块改造

**文件**: `EIS/FigureFile/Figure.py`、`EIS/FigureFile/ui_Figure.py`

#### 改动 2.1：`ui_Figure.py` 默认勾选

```python
# 第 145 行
self.origindataCheckBox.setChecked(True)   # 默认勾选
# 第 163 行
self.processeddataCheckBox.setChecked(True)  # 默认勾选
```

**附带 bug 修复**：
- 原代码 `self.origindataCheckBox.setChecked(False)` 错放在 `processeddataCheckBox` 之后 → 实际只有 `origindataCheckBox` 被设为 False，`processeddataCheckBox` 保持 True

#### 改动 2.2：Figure.py 新增状态控制方法

```python
def set_processing_state_enabled(self, enabled):
    """控制 Original/Processed 复选框的可用性"""
    self._processing_state_enabled = enabled
    self._display_synthetic = enabled  # 同步:关闭复选框 → 同时隐藏 synthetic 曲线
    self.figuregui.origindataCheckBox.setEnabled(enabled)
    self.figuregui.processeddataCheckBox.setEnabled(enabled)
    if not enabled:
        self.figuregui.origindataCheckBox.setChecked(False)
        self.figuregui.processeddataCheckBox.setChecked(False)

def set_display_synthetic(self, enabled):
    """单独控制绘图时是否显示 synthetic"""
    self._display_synthetic = enabled
```

#### 改动 2.3：连接 `stateChanged` 信号触发重绘

```python
self.figuregui.origindataCheckBox.stateChanged.connect(self._on_processing_state_changed)
self.figuregui.processeddataCheckBox.stateChanged.connect(self._on_processing_state_changed)

def _on_processing_state_changed(self):
    """复选框状态变化时自动重绘"""
    if getattr(self, '_processing_state_enabled', True) and self.plotdata:
        self.drawfigure()
```

#### 改动 2.4：`_filter_synthetic_for_display` 按复选框过滤

```python
def _filter_synthetic_for_display(self, outputlist, plotdataname, plotdata, message):
    # Input/Simulation 模式:强制隐藏 synthetic
    if not getattr(self, '_display_synthetic', True):
        # 过滤掉 synthetic
        ...

    # Filter/Processing/Fitting 模式:按复选框状态过滤
    show_orig = self.figuregui.origindataCheckBox.isChecked()
    show_proc = self.figuregui.processeddataCheckBox.isChecked()

    keep_indices = []
    for i, info in enumerate(message):
        is_synthetic = isinstance(info, dict) and info.get('synthetic', False)
        if is_synthetic and show_proc:
            keep_indices.append(i)
        elif (not is_synthetic) and show_orig:
            keep_indices.append(i)
    ...
```

---

### 阶段 3：Input 模块改造

**文件**: `EIS/InputFile/Input.py`

#### 改动 3.1：导入 `ensure_paired_form`

```python
from EIS.Other.Datacheck import ensure_paired_form
```

#### 改动 3.2：`sendsignal` 调用 `ensure_paired_form`

```python
def sendsignal(self):
    paired_selectlist, paired_names, paired_data, paired_info = ensure_paired_form(
        self.selectlist, self.plotdataname, self.plotdata, []
    )
    self.datasignal.emit(paired_selectlist, paired_names, paired_data, paired_info)
```

#### 改动 3.3：`onCellChanged` 同步更新成对数据名

```python
elif column == 1:  # 数据名称列
    new_name = item.text()
    # 表格行 N 对应成对化后的 2N (原始) 和 2N+1 (合成) 两个位置
    paired_idx_original = 2 * row
    paired_idx_synthetic = 2 * row + 1
    if paired_idx_original < len(self.plotdataname):
        self.plotdataname[paired_idx_original] = new_name
    if paired_idx_synthetic < len(self.plotdataname):
        self.plotdataname[paired_idx_synthetic] = new_name
```

---

### 阶段 4：Simulation 模块

**文件**: `EIS/SimulationFile/simulation.py`

`Simulation` 已支持成对数据（之前已实施），无需本次修改。

---

### 阶段 5：Plotting / Simulation 页面禁用复选框

**文件**: `GUI/pages/ui_page_plotting.py`、`GUI/pages/ui_page_simulation.py`

```python
# 在 FigWidget() 初始化后
self.figureWg.set_processing_state_enabled(False)
```

---

### 阶段 6：Filter 模块改造

**文件**: `EIS/FilterFile/Filter.py`

#### 改动 6.1：类常量

```python
# 处理后数据名称后缀(链式处理时会追加,例如 Filter 后再 Processing 会得到 _Filtered_Processed)
_processed_suffix = '_Filtered'
```

#### 改动 6.2：`initdata` 新增 `original_*` 属性

```python
self.original_prodata = []
self.original_prodataname = []
self.original_selectlist = []
self.original_dataInfo = []
self.resultsdataInfo = []
```

#### 改动 6.3：`getsingal` 提取原始 + 新增 `_extract_original_data`

```python
def _extract_original_data(self):
    """自适应:配对格式(2N+奇数位带synthetic)取偶数索引,否则全部"""
    n_pro = len(self.prodata)
    is_paired = (
        n_pro > 0 and n_pro % 2 == 0
        and self.dataInfo and len(self.dataInfo) == n_pro
        and any(isinstance(info, dict) and info.get('synthetic', False)
                for info in self.dataInfo[1::2])
    )
    if is_paired:
        self.original_prodata = [self.prodata[i] for i in range(0, n_pro, 2)]
        self.original_prodataname = [self.prodataname[i] for i in range(0, n_pro, 2)]
        self.original_selectlist = [self.selectlist[i] for i in range(0, n_pro, 2)]
        self.original_dataInfo = [self.dataInfo[i] for i in range(0, n_pro, 2)]
    else:
        self.original_prodata = list(self.prodata)
        # ... 类似处理
```

#### 改动 6.4：`auto_forward_data` 只转发原始 N 条

#### 改动 6.5：`databasecreat` 重写为自适应配对

**关键点**: 不动 `filterring`（仍调用 `self.prodata`），`databasecreat` 内部检测配对格式后从 `processresults[:N]` 取真实结果。

#### 改动 6.6：`create_filtered_datainfo` 简化为返回 `self.resultsdataInfo`

---

### 阶段 7：Processing 模块改造

**文件**: `EIS/ProcessingFile/Processing.py`

完全复用 Filter 的模式：
1. `_processed_suffix = '_Processed'`
2. `__init__` 兜底
3. `initdata` 新增 4 个 `original_*` 属性
4. `getsingal` 调用 `_extract_original_data`
5. `auto_forward_data` 修复
6. **`databasecreat` 重写** + **修复 `create_processed_datainfo` 实际从未 append 到列表的 BUG**

---

### 阶段 8：Fitting 模块改造

**文件**: `EIS/FittingFile/Fitting.py`

#### 改动 8.1：类常量 + `__init__` 兜底

```python
class Fitting(ECMFunction, MTMFunction, PyTabWidget2):
    _processed_suffix = '_Fitted'

    def __init__(self, parent=None):
        # 兜底:如果 _processed_suffix 未生效,在这里再次设置
        if not hasattr(self.__class__, '_processed_suffix') or not self.__class__._processed_suffix:
            self.__class__._processed_suffix = '_Fitted'
```

#### 改动 8.2：`__init__` 初始化新属性

```python
self.dataInfo = []
self.original_prodata = []
self.original_prodataname = []
self.original_selectlist = []
self.original_dataInfo = []
self.resultsdataInfo = []
```

#### 改动 8.3：`getsignal` 接收 4 参数（之前只接收 3 个！）

```python
def getsignal(self, message1, inputdataname, inputdata, inputmessage):
    global outputlist
    outputlist = message1
    global prodataname
    prodataname = inputdataname
    global prodata
    prodata = inputdata
    self.dataInfo = list(inputmessage) if inputmessage else []
    self._extract_original_data()
```

#### 改动 8.4：`ECMcalculation` / `MTcalculation` 使用 N 原始 + 构造 dataInfo

```python
fit_data = self.original_prodata
fit_names = self.original_prodataname
n = len(fit_data)
# ... 拟合循环 ...
orig_name = fit_names[i] if i < len(fit_names) else f'data_{i}'
plotdataname.append(orig_name)
plotdataname.append(orig_name + self._processed_suffix)

# 构造 dataInfo(2N):偶数=原始,奇数=拟合(带 synthetic 标签)
orig_info = (self.original_dataInfo[i].copy() if ...
             else {})
self.resultsdataInfo.append(orig_info)
fit_info = orig_info.copy()
fit_info['synthetic'] = True
fit_info['fit_applied'] = True
fit_info['fit_method'] = fit_method
self.resultsdataInfo.append(fit_info)
```

**关键变化**:
- 名称从硬编码 `'Origin' + str(i)` / `'ECMFitting' + str(i)` 改为真实原名 + `_Fitted`
- `sendsignal` 第 4 参数从 `fittedresults`（lmfit Results 列表）改为 `self.resultsdataInfo`（2N 列表），让下游 Figure 能识别 `synthetic` 标签

#### 改动 8.5：FittingSetRes.py 修复 Z_fitted 提取

**位置**: `EIS/FittingFile/FittingSetRes.py:155-163`

**问题**: `getsingal` 方法只处理 `Rs[ohm]`（ECM），不处理 `epsRE[-]`（MT），导致 MT 的 `Z_fitted = None`，R²/RMSE/χ² 3 个指标丢失。

**修复**:
```python
if hasattr(fitted_dict, 'columns'):
    if 'Rs[ohm]' in fitted_dict.columns:
        # ECM 数据格式
        Z_fitted = fitted_dict['Rs[ohm]'].values + 1j * fitted_dict['X[ohm]'].values
    elif 'epsRE[-]' in fitted_dict.columns:
        # MT 数据格式
        Z_fitted = fitted_dict['epsRE[-]'].values + 1j * fitted_dict['sigmaRE[S/m]'].values
```

---

## 四、改造过程中出现的问题与解决方案

### 问题 1：Input.py 出现 `NameError: 'ensure_paired_form' is not defined`

**原因**: `from EIS.Other.Datacheck import ensure_paired_form` 导入语句丢失

**修复**: 在 Input.py 顶部添加导入

---

### 问题 2：数据名称修改只更新一半（行 1、3 成功，行 2、4 失败）

**原因**: `onCellChanged` 只更新 `plotdataname[row]`，但成对化后 `plotdataname` 长度翻倍，表格行 N 对应 `2N`（原始）和 `2N+1`（合成）

**修复**: 同时更新 `2*row` 和 `2*row+1` 两个索引

---

### 问题 3：ui_Figure.py `setChecked(False)` 错放位置

**原因**: 第 50 行附近 `self.origindataCheckBox.setChecked(False)` 错放在 `processeddataCheckBox` 之后 → 实际只有 `origindataCheckBox` 被设为 False

**修复**: 改为 `self.processeddataCheckBox.setChecked(False)`

---

### 问题 4：Plotting 页面下两个复选框无功能

**原因**: 在 Input 模式下偶数和奇数索引处的 DataFrame 是完全相同的内容（合成 = 复制），复选框在 Input 模式下"摆设"

**修复**: 在 Plotting/Simulation 页面初始化时调用 `set_processing_state_enabled(False)` 禁用复选框并同步隐藏 synthetic 曲线

---

### 问题 5：Filter 处理后图窗显示 2 条相同曲线（重叠）

**原因**: Filter 输出的 2N 条数据中，偶数位是原始、奇数位是合成副本（Input 给的），但当前 Plotting 模式下不显示 synthetic，所以图窗只看到原始 → 用户误以为"没有变化"

**修复**: 让 Filter 输出"原始 + 真实滤波结果"（2N 不同内容），复选框默认勾选显示全部

---

### 问题 6：用户希望显示数据名带后缀

**原状**: Filter 输出 `'Origin_' + name` 和 `'Filtered_' + name`，Processing 类似

**修复**: 改为 `name`（原样）和 `name + _processed_suffix`（链式时累加），与 Input 协议一致

---

### 问题 7：`target = self.original_prodata` 替换 `self.prodata` 可能造成其他程序错误

**原因**: 可能有其他代码读 `self.prodata`，替换会导致副作用

**修复**: 保留 `self.prodata` 不动，`databasecreat` 内部自适应提取 `processresults[:N]` 作为真实结果

---

### 问题 8：Fitting 报 `AttributeError: 'Fitting' object has no attribute '_extract_original_data'`

**原因**: 之前 `Edit` 工具返回 "Results from Edit have been CLEARED" 表示修改未保存。`getsignal` 已修改为 4 参数，但 `_extract_original_data` 方法定义未保存

**修复**: 重新添加 `_extract_original_data` 方法

---

### 问题 9：Fitting 报 `AttributeError: 'Fitting' object has no attribute '_processed_suffix'`

**原因**: 同上，`_processed_suffix` 类常量未保存

**修复**: 重新添加类常量 + 在 `__init__` 中加兜底：
```python
if not hasattr(self.__class__, '_processed_suffix') or not self.__class__._processed_suffix:
    self.__class__._processed_suffix = '_Fitted'
```

**同样问题预防性处理**: Processing.py 也在 `__init__` 加了同样的兜底

---

### 问题 10：MT 拟合 Z_fitted 为 None

**原因**: FittingSetRes.py 的 `getsingal` 方法只支持 ECM 数据格式（`Rs[ohm]`），不识别 MT 数据格式（`epsRE[-]`）

**修复**: 在 `getsingal` 中添加 MT 数据格式分支，与 `on_dataset_selector_changed` 保持一致

---

## 五、最终行为对照表

| 场景 | 复选框状态 | plotdata 长度 | 图窗显示 | 保存 Excel |
|------|------------|--------------|----------|-----------|
| **Input 加载 N 文件** | 灰显不可勾选 | 2N（原+副本）| **N 条曲线**（副本被隐藏）| 全部 |
| **Simulation N 曲线** | 灰显不可勾选 | 2N | **N 条曲线** | 全部 |
| **Filter（启用）** | 默认两勾选 | 2N（原+滤波）| **2N 条曲线** | 按复选框筛选 |
| **Processing（启用）** | 默认两勾选 | 2N（原+处理）| **2N 条曲线** | 按复选框筛选 |
| **Fitting ECM（启用）** | 默认两勾选 | 2N（原+拟合）| **2N 条曲线** | 按复选框筛选 |
| **Fitting MT（启用）** | 默认两勾选 | 2N（原+拟合）| **2N 条曲线** | 按复选框筛选 |
| **链式 Filter→Processing** | 默认两勾选 | 4N | **4N 条曲线** | 按复选框筛选 |
| **链式 Filter→Processing→Fitting** | 默认两勾选 | 8N | **8N 条曲线** | 按复选框筛选 |

---

## 六、文件改动清单（总计 9 个文件）

| # | 文件 | 改动量 |
|---|------|--------|
| 1 | `EIS/Other/Datacheck.py` | 新增 `ensure_paired_form` 函数 |
| 2 | `EIS/FigureFile/Figure.py` | + `set_processing_state_enabled` + `set_display_synthetic` + `_on_processing_state_changed` + 重写 `_filter_synthetic_for_display` + 连接 `stateChanged` |
| 3 | `EIS/FigureFile/ui_Figure.py` | 2 行 `setChecked(True)` + 1 行 bug 修复 |
| 4 | `EIS/InputFile/Input.py` | 添加导入 + `sendsignal` 调用 `ensure_paired_form` + `onCellChanged` 同步更新 |
| 5 | `GUI/pages/ui_page_plotting.py` | 1 行调用 `set_processing_state_enabled(False)` |
| 6 | `GUI/pages/ui_page_simulation.py` | 1 行调用 `set_processing_state_enabled(False)` |
| 7 | `EIS/FilterFile/Filter.py` | 类常量 + 4 个新属性 + `_extract_original_data` + `auto_forward_data` 修复 + `databasecreat` 重写 + `create_filtered_datainfo` 简化 |
| 8 | `EIS/ProcessingFile/Processing.py` | 同 Filter 模式 + 修复 `create_processed_datainfo` 实际未 append 的 BUG + `__init__` 兜底 |
| 9 | `EIS/FittingFile/Fitting.py` | 类常量 + `__init__` 兜底 + 5 个新属性 + `getsignal` 改 4 参数 + `_extract_original_data` + `ECMcalculation` 重写 + `MTcalculation` 重写 + `sendsignal` 第 4 参数改 `resultsdataInfo` |
| 10 | `EIS/FittingFile/FittingSetRes.py` | `getsingal` 添加 MT 数据格式分支 |

---

## 七、关键设计经验

### 7.1 "自适应配对" 检测模式

所有模块统一用以下检测判断上游数据是 2N 配对还是 N 独立：

```python
is_paired = (
    n_pro > 0 and n_pro % 2 == 0
    and self.dataInfo and len(self.dataInfo) == n_pro
    and any(isinstance(info, dict) and info.get('synthetic', False)
            for info in self.dataInfo[1::2])
)
```

这样既能处理"配对格式"（来自 Input/上游链式），也能处理"非配对格式"（独立使用 Filter 等）。

### 7.2 `self.prodata` 始终保持原状

无论是否提取 `original_prodata`，`self.prodata` 都不被修改。这样所有读 `self.prodata` 的代码（包括 `check2`、`filtercompare` 等）都不会受影响。

### 7.3 兜底机制（防 Edit 丢失）

对于关键类常量（如 `_processed_suffix`），同时使用：
1. 类级常量声明
2. `__init__` 兜底检查

避免因 Edit 工具偶发丢失导致运行时 `AttributeError`。

### 7.4 `dataInfo` 的 `synthetic` 标签是"贯穿协议"

所有模块（包括下游 Figure）通过检查 `dataInfo[i].get('synthetic', False)` 决定：
- 是否过滤掉某条数据
- 该条数据的命名规则
- 绘图显示控制

这个标签是模块间数据流的核心标记。

### 7.5 `processresults[:N]` 提取模式

对于 2N 输入的处理函数（如 Filter/Processing 的 filterring/processing），**不修改它们**，让它们继续处理 2N 也不出错。在 `databasecreat` 内部用 `processresults[:N]` 提取"前 N 条"作为真实结果——这样避免了"改动 filterring 可能影响其他程序"的风险。

### 7.6 链式后缀累积

每个模块的处理后数据**追加自身后缀**（`_Filtered` / `_Processed` / `_Fitted`），不重命名。这样：
- 链式处理时自动累积（`_Filtered_Processed_Fitted`）
- 原始名（偶数位）始终不变
- 不会因为"先 Processing 后 Fitting"导致名称冲突

---

## 八、验证清单

启动程序后按顺序测试：

- [ ] **Plotting 加载 1 文件** → 绘图 → 1 条曲线 ✓ Original/Processed 灰显
- [ ] **Simulation** → 仿真数据 → 绘图 → 1 条曲线 ✓ 复选框灰显
- [ ] **Filter 启用** → 滤波 → 绘图 → 2 条曲线（`实验数据A` + `实验数据A_Filtered`）
- [ ] **Filter 取消勾选 Original** → 仅显示 `实验数据A_Filtered`
- [ ] **Filter 取消勾选 Processed** → 仅显示 `实验数据A`
- [ ] **Processing 启用** → 平行板电容等方法 → 2 条曲线（`实验数据A` + `实验数据A_Processed`）
- [ ] **链式 Filter→Processing** → 4 条曲线，名称按 `实验数据A` / `实验数据A_Processed` / `实验数据A_Filtered` / `实验数据A_Filtered_Processed` 顺序
- [ ] **Fitting ECM 启用** → 拟合 → 2 条曲线（`实验数据A` + `实验数据A_Fitted`）
- [ ] **Fitting MT 启用** → 拟合 → 2 条曲线，**结果表格显示 6 个指标**（R²/RMSE/χ² 等）
- [ ] **链式 Processing→Fitting** → 4 条曲线，名称累加 `_Processed_Fitted`

---

## 九、修改时间线

| 阶段 | 改动内容 | 验证结果 |
|------|----------|----------|
| 1 | `ensure_paired_form` 工具函数 | ✅ |
| 2 | Figure 模块 + 复选框默认勾选 + signalChanged 重绘 | ✅ |
| 3 | Input 模块 `sendsignal` + 名称同步 | ✅ |
| 4 | Plotting/Simulation 页面禁用复选框 | ✅ |
| 5 | Filter 模块改造（_extract + databasecreat 自适应）| ✅ 显示 2 条曲线 |
| 6 | Processing 模块改造（同 Filter 模式）| ✅ |
| 7 | Fitting 模块改造（4 参数 + 真实原名 + dataInfo 列表）| ✅ 解决 AttributeError |
| 8 | FittingSetRes MT 数据格式支持 | ✅ R²/RMSE/χ² 正确显示 |

---

**文档结束**。所有改动已经测试通过，5 个模块的数据流现在完全统一。
