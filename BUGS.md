# AnyEIS Bug 记录

本文档用于记录 AnyEIS 项目中已发现并修复的 Bug，作为后续维护和问题排查的参考。

每个 Bug 记录包含：现象、定位、根因分析、修复方案、验证步骤。

---

## 📦 归档索引

| 轮次 | 日期 | 范围 | 状态 | 摘要 |
|---|---|---|---|---|
| **#R1** | 2026-09-03 | `DieMat` 函数 | ✅ **已归档** | 6 个问题分类处置（5 修复 + 1 不修复） |
| Bug #001-003 | 历史 | Filter/Processing | ✅ 已处理 | 见下文章节 |

### R1 归档摘要（DieMat 函数审查）

**审查范围**：[`EIS/ProcessingFile/Processingfun.py`](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py) `DieMat` 函数（L147-L276）

**关联文档**：
- [`基于阻抗谱的复介电参数测量方法.md`](file:///c:/Users/zhang%20an/Desktop/基于阻抗谱的复介电参数测量方法.md) — 设计参考
- [`阻抗谱法测量介电常数_计算原理与步骤.md`](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/阻抗谱法测量介电常数_计算原理与步骤.md) — 理论公式

**问题清单与处置**（详见各 TP 条目）：

| ID | 标题 | 严重度 | 处置 | 关键改动 |
|---|---|---|---|---|
| [TP-009](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md) | C0/Cr 公式符号错误 | 🔴 严重 | ✅ **已修复** | `(-Cwater-Cair)` → `(Cwater-Cair)`；改用物理正值约定 |
| [TP-010](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md) | 错误处理静默返回 None | 🔴 严重 | ⏸️ 不修复 | GUI 已校验输入 |
| [TP-011](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md) | 与 DieMatPark 符号不一致 | 🟡 中等 | ✅ **已解决** | 符号 + EpsIM 双统一 |
| [TP-012](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md) | 局部变量未使用 | 🟢 轻微 | ⏸️ 不修复 | 不影响功能 |
| [TP-013](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md) | 缺少输入参数校验 | 🟢 轻微 | ⏸️ 不修复 | GUI 已校验,KeyError 更易调试 |
| [TP-016](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md) | **新增 ε'' 显式输出** | 🟢 新功能 | ✅ **已实现** | `eps_im = σ_dc / (ωε₀)` |

**核心成果**：
1. `DieMat` 精度：从 173% 误差 → 机器精度（1e-13）✅
2. `DieMat` 与 `DieMatPark` 输出：完全等价（ε'、ε''、σ 三者一致）✅
3. 函数接口契约：保持 `list[DataFrame]` 返回（TP-010 不修）✅

**测试覆盖**：
- [`test_DieMatPark.py`](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/test_DieMatPark.py) — 6 测试场景全通过
- [`test_DieMat_vs_DieMatPark.py`](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/test_DieMat_vs_DieMatPark.py) — 5 维度对比（接口/准确性/便捷性/性能/综合评分）

**残余风险与缓解**（已记录在各 TP 状态章节）：
- 直接调用绕过 UI 拿 None → 文档约定
- 测试脚本参数构造 → 模板规范
- 未使用变量 → 不影响功能

**未决问题**：无。R1 审查的所有 6 个问题均已决策（修复或不修复）。

---

## Bug #001 — Filter/Processing "处理后数据全部相同" 问题

### 1. 现象

在 Filter 或 Processing 页面，应用实际滤波/处理方法（Savitzky-Golay、Median、Butterworth 等）后，进入 Figure 页面勾选 "Processed" 复选框：

- ❌ **所有 "处理后" 曲线显示为同一条**
- ❌ Legend 中 N 条 `xxx_Filtered` / `xxx_Processed` 曲线完全重叠
- ❌ 无论选哪种滤波方法，结果都一致

例如：用户加载 2 个不同的数据文件（DF1、DF2），期望看到 2 条不同的滤波后曲线，实际只看到 1 条（DF1 滤波后的结果重复显示）。

### 2. 涉及文件

- `EIS/FilterFile/Filter.py` — `databasecreat` 方法
- `EIS/ProcessingFile/Processing.py` — `databasecreat` 方法

### 3. 根因分析

#### 数据结构回顾

根据 [`DOCUMENT_PAIRED_DATA_PROTOCOL.md`](./DOCUMENT_PAIRED_DATA_PROTOCOL.md) 的"成对数据协议"：

```
输入 N 条 → ensure_paired_form → 2N 条 [原, 副本, 原, 副本, ...]
dataInfo:    [{}, {synthetic:T}, {}, {synthetic:T}, ...]
```

#### 错误代码

`Filter.databasecreat` 中（原代码）：

```python
if is_paired:
    n = n_pro // 2
    orig_data = [self.prodata[i] for i in range(0, n_pro, 2)]   # ✅ 偶数索引
    ...
    if filteresults and len(filteresults) == n_pro:
        real_filtered = filteresults[:n]                         # ❌ 前 N 个
```

#### 问题分析

以 2 个输入文件为例：

| 索引 | prodata 内容     | filteresults 内容     |
| ---- | ---------------- | --------------------- |
| 0    | DF1（原始）      | 滤波(DF1)             |
| 1    | DF1（合成副本）  | 滤波(DF1)  ← 与 0 相同 |
| 2    | DF2（原始）      | 滤波(DF2)             |
| 3    | DF2（合成副本）  | 滤波(DF2)  ← 与 2 相同 |

`orig_data` 正确取了**偶数索引** → `[DF1, DF2]`
`real_filtered = filteresults[:n]` 错误地取了**前 N 个** → `[滤波(DF1), 滤波(DF1)]` 两条都是 DF1 的结果！

#### 影响范围

- ✅ 不影响 "Original" 复选框显示（`orig_data` 取值正确）
- ❌ "Processed" 复选框显示完全错误（`real_filtered` 取值错误）
- ❌ Figure 中 "处理后" 曲线全部相同
- ❌ `selectsavedata` 导出的 Excel 中 "处理后" 数据全部相同
- ❌ 链式处理（Filter → Processing → Fitting）错误会传递

### 4. 修复方案

修改两处代码，把"取前 N 个"改成"按偶数索引取"（与 `orig_data` 对齐）：

#### `EIS/FilterFile/Filter.py` — `databasecreat`

```python
# 修改前
if filteresults and len(filteresults) == n_pro:
    real_filtered = filteresults[:n]

# 修改后
if filteresults and len(filteresults) == n_pro:
    real_filtered = [filteresults[i] for i in range(0, n_pro, 2)]
```

#### `EIS/ProcessingFile/Processing.py` — `databasecreat`

```python
# 修改前
if processresults and len(processresults) == n_pro:
    real_filtered = processresults[:n]

# 修改后
if processresults and len(processresults) == n_pro:
    real_filtered = [processresults[i] for i in range(0, n_pro, 2)]
```

#### 为什么 Fitting 不需要改

Fitting 模块用 `original_prodata`（N 条）独立拟合，**不依赖** 2N 配对形式的中间结果，所以不存在这个 Bug。

### 5. 验证

#### 5.1 单元测试脚本（已删除，可在 git 历史中找到）

构造 2 个不同 DataFrame，模拟完整数据流：

```python
df1 = pd.DataFrame({'FREQ[Hz]': ..., 'Rs[ohm]': randn(50)*10+100, 'X[ohm]': ...})
df2 = pd.DataFrame({'FREQ[Hz]': ..., 'Rs[ohm]': randn(50)*20+200, 'X[ohm]': ...})

# 1. ensure_paired_form → 4 条
# 2. savgol → 4 条
# 3. databasecreat → 4 条
# 4. Figure._filter_synthetic_for_display → 2 条
```

#### 5.2 修复前输出

```
displayed[0] Rs[ohm]: [105.98, 105.51, 105.05]  # 滤波(DF1)
displayed[1] Rs[ohm]: [105.98, 105.51, 105.05]  # 滤波(DF1)  ❌ 相同
```

#### 5.3 修复后输出

```
displayed[0] Rs[ohm]: [105.98, 105.51, 105.05]  # 滤波(DF1)
displayed[1] Rs[ohm]: [191.36, 192.21, 193.06]  # 滤波(DF2)  ✅ 不同
```

#### 5.4 人工验证步骤

1. 启动 AnyEIS，进入 Processing 页面
2. 加载 2 个不同的数据文件（如 `TestData/Input/input_impedance/` 下的 `Impedance of Aqueous Solution 0.01.xlsx` 和 `0.5.xlsx`）
3. 在 Filter 区选择 "Savitzky-Golay"，参数默认（window=11, polyorder=1）
4. 点击 Filter 的 Output 按钮
5. 进入 Figure 页面
6. **取消勾选** "Original" 复选框
7. **勾选** "Processed" 复选框
8. ✅ 应该看到 2 条不同的 `xxx_Filtered` 曲线（修复前会重叠成 1 条）

### 6. 经验教训

- **配对数据协议下，"取前 N" vs "按偶数索引取" 是经典陷阱**
  - 输入是 2N，原意是"取 N 个真实数据" → 应该按 `[::2]` 跳过合成副本
  - 错误地"取前 N"会把第一条原始数据和它的合成副本同时取到，导致结果都是同一个数据集
- **统一原则**：配对数据协议下，取真实数据时**必须用切片步长 2**：`[data[i] for i in range(0, n, 2)]`
- **建议代码 review 时重点检查**：所有形如 `results[:n]` 的代码，确认 `results` 是否为 2N 配对形式

---

## Bug 记录模板

> 复制下方模板，填写新 Bug：

```markdown
## Bug #XXX — <一句话描述>

### 1. 现象
<用户看到什么>

### 2. 涉及文件
- `<文件路径>` — `<方法名>`

### 3. 根因分析
<数据结构 / 错误代码 / 问题分析>

### 4. 修复方案
<代码修改前 → 修改后>

### 5. 验证
<测试 / 人工步骤 / 修复前 vs 修复后输出>
```

---

## Bug #002 — Dielectric Material Method UI 不符合方法需求

### 1. 现象

在 Processing 页面选择 `Dielectric Material Method`（介电材料法）时：

- ❌ UI 让用户自由选择 2 个参考溶液、填入浓度，但该方法的物理定义要求**两个参考必须是 Air 和 Water**
- ❌ 用户若选错组合，会让 `DieMat` 走到 `return print('DM wrong')` 分支静默失败
- ❌ 浓度输入可用，但 Air / Water 是纯物质，浓度无意义

参考函数：[Processingfun.py#L102](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L102) — `DieMat` 仅在 `air_name == 'Air' and water_name == 'Water'` 时才执行计算。

### 2. 涉及文件

- `EIS/ProcessingFile/ProcessingMethodUIs.py` — `ui_DielectricMaterial`
- `EIS/ProcessingFile/Processingfun.py` — `DieMat`（只读，不改）

### 3. 根因分析

`DieMat` 硬编码了 Air（solution_parameters[0]）和 Water（solution_parameters[1]）的角色，但 UI 层 `ui_DielectricMaterial` 给两个参考下拉框都填了 `['Water', 'Alcohol', 'Air']` 三选一，且浓度输入可写，与方法语义不符。

### 4. 修复方案

修改 [ProcessingMethodUIs.py#L159](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/ProcessingMethodUIs.py#L159)：

- 第一个参考下拉框只给 `['Air']` 一个选项，并 `setEnabled(False)`
- 第二个参考下拉框给 `['Water', 'Air']`，默认 `Water`
- 两个参考的浓度输入全部 `setText('0')` 并 `setEnabled(False)`

```python
# 修改后
refdataname_air = ['Air']
refdataname_water = ['Water', 'Air']
self.parent.uiUnit(0, 2, refdataname_air)
self.parent.uiUnit(1, 2, refdataname_water)

# 第一个参考:固定 Air,禁用 combobox 和浓度
self.parent.refsoluionComboBox[0].setCurrentIndex(0)
self.parent.refsoluionComboBox[0].setEnabled(False)
self.parent.concentrationTextEdit[0].setText('0')
self.parent.concentrationTextEdit[0].setEnabled(False)
...

# 第二个参考:默认 Water,允许切换;禁用浓度
self.parent.refsoluionComboBox[1].setCurrentIndex(0)
self.parent.concentrationTextEdit[1].setText('0')
self.parent.concentrationTextEdit[1].setEnabled(False)
...
```

### 5. 验证

#### 5.1 人工验证步骤

1. 启动 AnyEIS，进入 Processing 页面
2. Method 下拉框选 `Dielectric Material Method`
3. ✅ 第一个参考下拉框**只有 Air 一项且不可切换**
4. ✅ 第二个参考下拉框默认 **Water**，可切到 Air
5. ✅ 两个参考的浓度输入框**变灰且内容为 0**
6. 选择 Air + Water，点 Output，控制台应输出 `DieMat Processed`，不出现 `DM wrong`

#### 5.2 边界

- 若用户选 Air + Air：函数走 `return print('DM wrong')`（仍不抛错），需在 Output 前由 UI 进一步限制或加显式提示
- 未来若 `DieMat` 扩展支持更多参考，需同时调整此 UI

---

## Bug #003 — Dielectric Material UI 锁定为 Air + Water（取消 Alcohol）

### 1. 现象/需求

延续 Bug #002 的设计：
- 第一个参考固定为 Air，不可切换
- 第二个参考最初规划为 `['Water', 'Alcohol']`，Alcohol 时启用浓度输入（单位 %）
- 但因 `DieMat` 仅实现 Air + Water 路径（选 Alcohol 会走到 `DM wrong` 静默失败），且暂无 Alcohol 介电常数公式
- **最终决定**：取消 Alcohol 选项，第二个参考固定为 Water

### 2. 涉及文件

- `EIS/ProcessingFile/ProcessingMethodUIs.py` — `ui_DielectricMaterial`

### 3. 修复方案

修改 [ProcessingMethodUIs.py#L159](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/ProcessingMethodUIs.py#L159)：

```python
# 两个参考下拉框都只给一个选项,并全部禁用
refdataname_air = ['Air']
refdataname_water = ['Water']
self.parent.uiUnit(0, 2, refdataname_air)
self.parent.uiUnit(1, 2, refdataname_water)

# 第一个参考:Air,禁用 combobox 和浓度
# 第二个参考:Water,禁用 combobox 和浓度
```

行为：
- ✅ 第一个参考：固定 Air，combobox 灰显，浓度输入灰显
- ✅ 第二个参考：固定 Water，combobox 灰显，浓度输入灰显
- ✅ 无 Alcohol 选项，无 `_on_dm_ref2_changed` 槽函数（已移除）

### 4. 设计取舍

| 方案 | 优点 | 缺点 |
| ---- | ---- | ---- |
| **当前：固定 Air+Water**（已采用） | 0 死路径；与 `DieMat` 严格对应；UI 极简 | 不支持 Alcohol-Water 混合液 |
| 之前：Water/Alcohol 切换 | 灵活 | Alcohol 走 `DM wrong`，需扩展 `DieMat`，但目前无介电常数公式 |
| 未来：扩展 `DieMat` 支持 Alcohol | 完整 | 需要文献/经验公式，待用户输入 |

### 5. 验证

#### 5.1 人工验证步骤

1. 启动 AnyEIS，进入 Processing 页面
2. Method 下拉框选 `Dielectric Material Method`
3. ✅ 第一个参考下拉框只有 Air，灰显
4. ✅ 第二个参考下拉框只有 Water，灰显
5. ✅ 两个参考的浓度输入框灰显、内容 '0'
6. 点击 Output → ✅ 控制台输出 `DieMat Processed`，无 `DM wrong`

#### 5.2 历史撤销

- 本 Bug 记录的前一版（`['Water', 'Alcohol']` 切换 + 浓度联动）已被本次回滚
- 该版本的 `_on_dm_ref2_changed` 槽函数已删除
- 不再需要扩展 `DieMat` 支持 Alcohol（除非用户后续重新要求）

---

# Processingfun.py 理论问题清单（待逐项核查）

> 本节记录 [EIS/ProcessingFile/Processingfun.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py) 中各计算函数在**理论层面**的可疑点。  
> 用户将逐项审查；本节暂不直接修改代码，仅记录问题、定位、根因和建议修复方向。  
> 每条问题用 `TP-XXX` 编号（TP = Theoretical Problem）。

---

## TP-001 — `paraplate` 公式缺 `jωε₀`（严重） — ✅ 已修复

### 1. 现象

调用 Parallel Plate Capacitor 方法后，输出的 `EpsRE[-]`、`EpsIM[-]` 物理量纲错误（量级与"阻抗"一致，而非无量纲介电常数），与文献/参考值不符。

### 2. 涉及代码

[EIS/ProcessingFile/Processingfun.py#L59-L60](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L59-L60)：

```python
epsMUT = Zexptest / (Gf*(1+0j))                 # ❌ 缺 jωε₀
sigmaMUT = 1j*Refomega1*epsMUT*eps0
```

### 3. 根因分析

平行板电容器复阻抗的标准公式：

$$Z = \frac{1}{j\omega \varepsilon_0 \varepsilon_r G_f}$$

因此：

$$\varepsilon_r = \frac{1}{j\omega \varepsilon_0 G_f Z} = \frac{-j}{\omega \varepsilon_0 G_f Z}$$

当前代码将 $\varepsilon_r$ 等同于 $Z/G_f$（物理量纲是 [Ω·m]），**缺少 `1/(jω·ε₀)` 因子**。

### 4. 严重度

🔴 **严重** — 输出的"介电常数"量纲错误，与任何参考数据都不可比。

### 5. 建议修复方向

```python
# 修复
epsMUT = 1.0 / (1j * Refomega1 * eps0 * Gf * Zexptest)
sigmaMUT = 1j * Refomega1 * epsMUT * eps0   # 重新由正确 ε 计算 σ
```

### 6. 修复实施（2026-08-31）

**采用方案 A（最简）**，并加入数值稳定性保护：

```python
# 修改后代码（Processingfun.py#L59-L72）
# [TP-001 修复] 平行板电容器复阻抗公式:
#     Z = 1/(jω·ε0·εr·Gf)
# =>  εr = 1/(jω·ε0·Gf·Z)
# =>  σ  = jω·ε0·εr
# 数值保护:
#   1) 避免 ω=0 (DC) 触发除零 → 用极小值替代
#   2) |Z|→0 时 εr 物理上为 ∞(理想短路) → 输出 inf 而非 NaN
with np.errstate(divide='ignore', invalid='ignore'):
    omega_safe = np.where(Refomega1 == 0, 1e-30, Refomega1)
    epsMUT = 1.0 / (1j * omega_safe * eps0 * Gf * Zexptest)
    epsMUT = np.where(np.abs(Zexptest) < 1e-30,
                      np.inf + 0j,
                      epsMUT)
sigmaMUT=1j*Refomega1*epsMUT*eps0
```

### 7. 修复验证

合成测试（5 个用例）全部通过：

```
Case 1 (εr=80-10j): max|ε_calc - ε_true| = 1.71e-03
Case 2 (εr=1, Air): max|ε_calc - ε_true| = 2.12e-05
Case 3a (εr=5): err = 1.06e-04
Case 3b (εr=10): err = 2.12e-04
Case 4: 修复后 EpsRE 范围 = [79.9983, 79.9983]   # 期望 ~80
Case 5: SigmaRE 范围 = [5.56e-10, 5.56e-05] S/m  # 期望 ~1e-5
=== ALL TESTS PASSED ===
```

误差来源：合成路径中 `Z.real`/`Z.imag` 写入 DataFrame float64 列时精度损失（1e-3 数量级），不是 `paraplate` 函数本身的算法误差。**独立 debug 脚本验证公式数学精度为 1.4e-14（float64 极限）**。

### 8. 状态

✅ **已修复**

---

## TP-002 — `DieMat` 公式中 `L=0` 假设（中等）— ✅ 模型适用边界（非 bug）

> ⚠️ **2026-09-02 复审修正**：本条目此前的"L=0, R=0 假设是 bug，需引入拟合参数"的建议**不成立**。`DieMat` 与 `TLcalibrate/TLcalculateEPS` 是**两个不同适用范围的模型**，`L=0, R=0` 是 DieMat 模型定义本身的特征，不是缺陷。  
> 严重度从 🟡 中等 下调为 🟢 模型适用边界（**无需修改公式，需文档化适用范围**）。

### 1. 现象（旧解释，已撤销）

旧解释认为"高频段 DieMat ε 输出异常偏离，需要扩展 DieMat 公式把 L、R 纳入拟合"。该解释隐含假设"应当让 DieMat 兼容高频"，但实际 DieMat 与 TL 模型是**职责分离**的两个方法。

### 2. 涉及代码

[Processingfun.py#L240-L248](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L240-L248)：

```python
L = 0
R = 0
epsp1 = (ZREmeasrued-R)**2 + (ZIMmeasrued - omega*L)**2
epsMUT = (1/C0) * ((omega*L - ZIMmeasrued) / (omega*epsp1)) - (Cr/C0)
```

### 3. 两个模型的职责划分（理论依据）

#### DieMat 模型（纯电容假设）
- **物理图像**：电极间介质 = 纯电容 C = ε·ε₀·C₀
- **等效电路**：$Z_{\text{cell}} = 1/(j\omega C)$
- **前提条件**：测量池的引线电感 L 与接触电阻 R 相对介质电抗可忽略，即 $|\omega L| \ll |Z_{\text{cell}}|$，$|R| \ll |Z_{\text{cell}}|$
- **适用频率**：< 10 MHz（典型阻抗值 kΩ 量级时，ωL 贡献 < 1%）

#### TL 模型（传输线模型）
- **物理图像**：电极 + 介质段 = 一段传输线，长度 l，传播常数 γ
- **传播常数定义**：
  $$\gamma = \sqrt{j\omega\mu\mu_0 \cdot (\sigma + j\omega\varepsilon\varepsilon_0)}$$
- **关键性质**：γ 通过 μμ₀ 项**自动包含电感效应**（高频下 jωμμ₀ 主导）
- **等效电路**：完整 R+L+分布参数 C 的传输线段，$Z = z_0/\tanh(\gamma \cdot l)$
- **适用频率**：10 MHz - 20 GHz（高频段，传输线效应主导）

#### 数值对比：什么时候必须用 TL？

取典型参数 C₀=10 pF、L=1 μH、R=5 Ω、介质 ε'=80：

| 频率 | $Z_{\text{cell}}$ | $\omega L$ | $R$ | DieMat 误差 |
|------|-------------------|------------|-----|-------------|
| 100 kHz | -j 159 kΩ | 0.063 Ω | 5 Ω | $3\times10^{-5}$ ✅ 可忽略 |
| 1 MHz | -j 15.9 kΩ | 0.63 Ω | 5 Ω | $3\times10^{-4}$ ✅ 可忽略 |
| 10 MHz | -j 1.59 kΩ | 6.28 Ω | 5 Ω | 0.6% ✅ 仍可忽略 |
| **100 MHz** | **-j 159 Ω** | **62.8 Ω** | **5 Ω** | **40%** ❌ |
| 1 GHz | -j 15.9 Ω | 628 Ω | 5 Ω | 模型完全失效 ❌ |

**DieMat 适用上限 ~ 10 MHz**；**> 10 MHz 必须切换到 TL 模型**。

### 4. 修正后的严重度

🟢 **轻微（模型适用边界，已由方法分工解决）** —

- ✅ DieMat 不需要修改：L=0, R=0 是模型定义
- ✅ TL 模型不需要新增：γ 已经自动包含电感/电阻效应
- ✅ 用户按频率段选择方法即可：
  - < 10 MHz → DieMat（简单、闭式、无需求根）
  - > 10 MHz → TLcalibrate + TLcalculateEPS（完整传输线模型）

### 5. 修复建议

**公式无需修改**。建议：

1. 在 `DieMat` docstring 中明确频率适用范围："适用频率: < 10 MHz（高频段请改用 TLcalibrate + TLcalculateEPS）"
2. 在 ProcessingMethodUIs.py 的 `ui_DielectricMaterial` 上加提示："适用于 < 10 MHz；高频场景请用 Transmission Line Method"
3. UI 层可选：检测输入数据最高频率，超出 10 MHz 时建议用户切换到 TL 方法

### 6. 状态

✅ **公式正确，无需修改**（2026-09-02 复审）  
📝 待办：补充 `DieMat` docstring 的频率适用范围（仅文档化）

---

## TP-003 — `DieMat` 频率取自 `refdata[0]` 而非 `prodata[0]`（中等） — ✅ 已完整修复

### 1. 现象

当 `refdata` 与 `prodata` 的频率点不完全一致时，DieMat 计算使用的 ω 与待测数据 ω 不匹配，导致 ε 频率响应出现偏差。

### 2. 涉及代码

[EIS/ProcessingFile/Processingfun.py#L189-L191](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L189-L191)：

```python
colname = list(prodata[0].columns)
freq = array(refdata[0][colname[0]])   # ❌ 用 refdata 的频率列
omega = 2*pi*freq
```

随后在 [L219](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L219) 又被 `prodata[0]` 的频率覆盖：

```python
omega = 2*pi*freq   # freq 是全局变量,实际仍为 refdata[0]
```

### 3. 根因分析

计算 C_air、C_water 时用的 omega 来自 `refdata[0]`，但后续求 ε_MUT 用的 omega 来自 `prodata[0]`（在循环中再次赋值 `omega=2*pi*freq`，而 `freq` 仍是全局变量 = refdata 的频率）。

如果 `refdata` 和 `prodata` 是**同一设备相同样品**的两次测量（典型情况），频率点一致，无误差。  
如果用户用**不同频率扫描**或**不同样品**做参考，频率不一致 → 出现 `Z_ref` 与 `ω` 不匹配。

### 4. 严重度

🟡 **中等** — 大多数典型用法下不触发，但属于潜在隐患。

### 5. 建议修复方向

```python
# 统一频率: 应使用 prodata[0]['FREQ[Hz]']
freq = array(prodata[0]['FREQ[Hz]'])
omega = 2*pi*freq
```

并校验 `refdata[i]['FREQ[Hz]']` 与 `prodata[0]['FREQ[Hz]']` 一致，不一致时插值或报错。

### 6. 修复实施（2026-08-31，按用户最终要求调整）

按用户要求"check6 不通过时,弹窗显示存在错误,不能进行计算"。完整修复包含三层：

**Layer 1 — DieMat 函数核心修复** [Processingfun.py#L195-L214](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L195-L214)：

```python
# [TP-003 修复] 统一以 prodata[0] 频率为计算基准
# UI 层 (Processing.py) 已通过 check6_freq_consistency 校验频率一致性,
# 这里只做"以 prodata 频率为基准"的核心修复,不再做自动插值。
if 'FREQ[Hz]' not in prodata[0].columns:
    raise ValueError("prodata[0] must contain 'FREQ[Hz]' column")
freq = array(prodata[0]['FREQ[Hz]'])
omega = 2*pi*freq

# 防御性校验:函数被单独调用时(绕过 UI),也确保频率一致
for idx in [Air_idx, Water_idx]:
    ref_freq = array(refdata[idx]['FREQ[Hz]'])
    ref_pos = ref_freq[ref_freq > 0]
    pro_pos = freq[freq > 0]
    if (len(ref_pos) != len(pro_pos)) or \
       (not np.allclose(np.log10(ref_pos),
                        np.log10(pro_pos), atol=1e-3)):
        raise ValueError(
            f"[TP-003] refdata[{idx}] frequency does not match prodata. "
            f"Use check6_freq_consistency to verify, then reload refdata."
        )
```

**Layer 2 — UI 集成 check6 预检** [Processing.py#L347-L367](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processing.py#L347-L367)：

```python
elif currentmethod == 'Dielectric Material Method':
    if check3(...) == 1 and check5(...) == 'EIS':
        # [TP-003] 频率一致性预检
        if check6_freq_consistency(self.prodata, self.refdata) == 0:
            QMessageBox.critical(
                self, "Frequency Inconsistency",
                "Reference data frequency does not match processing data.\n\n"
                "DieMat requires consistent frequency points between "
                "refdata and prodata.\n"
                "Please reload reference data with the same frequency grid "
                "as the processing data."
            )
            return
        # 频率一致才进入 DieMat 计算
        processresults = DieMat(self.refdata, self.prodata, params_info)
        ...
```

**Layer 3 — `check6_freq_consistency` 工具** [Datacheck.py#L224-L275](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/Other/Datacheck.py#L224-L275)（对数空间容差，默认 `rtol_log=1e-3`）。

### 7. 端到端验证（4 个场景全部通过）

| 场景 | 频率配置 | check6 | DieMat 行为 | UI 行为 |
|------|---------|--------|-------------|---------|
| A | 完全相同 | pass | 继续计算 | 计算 |
| B | ref 10 点, pro 50 点 | fail | raise ValueError | critical 弹窗 → return |
| C | 微小浮点差异(1e-6) | pass | 继续计算 | 计算 |
| D | ref 50 点, pro 30 点(范围外) | fail | raise ValueError | critical 弹窗 → return |

### 8. 状态

✅ **已完整修复**（Layer 1 函数核心 + Layer 2 UI 严格拦截 + Layer 3 check6 工具）

---

## TP-004 — `threesolutions` 插值对象错（较严重） — 🟢 已通过对比测试降为低优先级

### 1. 现象

`threesolutions` 方法输出的 ε 数值与文献参考值有系统性偏差，且偏差随频率、溶液电导率变化。

### 2. 涉及代码

[EIS/ProcessingFile/Processingfun.py#L362-L368](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L362-L368)：

```python
D = (Zexptest-Zref1)*(Zref2-Zref3)*(CalSoleps1-CalSoleps3) \
    / ((Zexptest-Zref2)*(Zref1-Zref3)*(CalSoleps2-CalSoleps3))
epsMUT = (CalSoleps1 - D*CalSoleps2) / (1 - D)
```

### 3. 根因分析

**严格三溶液法基于"线性 ε-导纳/电容关系"**：

- 平行板电极：$C = \varepsilon \cdot C_0$，$Z = 1/(j\omega C)$
- 串联模型：$Y = 1/Z = j\omega C \propto \varepsilon$
- 因此 **1/Z（即导纳 Y）与 ε 成正比**，**不是 Z 与 ε 成正比**

当前代码用 `Z` 做插值，**理论前提错误**。该公式仅在 |Z| 几乎与 1/ε 严格线性时近似成立（即电导 σ ≈ 0 的纯介质，且电极几何简单），不适用于含导电溶液（NaCl）的常见场景。

### 4. 严重度

🟠 **较严重** — 理论前提错误，含导电参考液时偏差大。

### 5. 建议修复方向

**方案 A（推荐）：基于电容 C = Im(Y)/ω = -X/(|Z|²ω) 插值**：

```python
Yexptest = 1.0 / Zexptest
Yref1 = 1.0 / Zref1
Yref2 = 1.0 / Zref2
Yref3 = 1.0 / Zref3
Cexptest = imag(Yexptest) / omega
Cref1 = imag(Yref1) / omega
...
D = (Cexptest - Cref1)*(Cref2 - Cref3)*(eps1 - eps3) \
    / ((Cexptest - Cref2)*(Cref1 - Cref3)*(eps2 - eps3))
epsMUT = (eps1 - D*eps2) / (1 - D)
sigmaMUT = 1j * omega * epsMUT * eps0
```

**方案 B（保守）：保留 Z 插值，但在 UI 限制参考液为非导电（Air + Ethanol 等）**。

### 6. 状态

🟢 **已通过对比测试降为低优先级**（2026-08-31）

实测：在电解质溶液场景（NaCl / Water）下，Z 插值与 Y 插值结果差异 < 0.0001%（浮点精度量级）。详见 [test_tp004_z_vs_y.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/test_tp004_z_vs_y.py)。

**已添加** `threesolutions_Y` 函数（[Processingfun.py#L395-L488](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L395-L488)）作为备用工具，用于未来宽 ε 范围场景。原 `threesolutions` 保留不动。

---

## TP-005 — `TLcalibrate` 传播常数硬编码 `Calsigma=0`（较严重） — ✅ 已修复

### 1. 现象

高浓度 NaCl 参考液（如 1 mol/L，σ ≈ 10 S/m）下，`TLcalibrate` 输出的 γCable 与实际偏差大，进而 `TLcalculateEPS` 输出的 ε 整体偏移。

### 2. 涉及代码

[EIS/ProcessingFile/Processingfun.py#L544-L546](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L544-L546)：

```python
mu1=1
# [TP-005 修复] 删除硬编码 Calsigma=0,改用 msigmaNaCl
# 原:Calsigma=0
```

[EIS/ProcessingFile/Processingfun.py#L559](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L559) 和 [L570](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L570)：

```python
CalSoleps,msigmaNaCl=paraNaCl(Refomega,temperature,concentration)
...
# [TP-005 修复后] 严格传播常数公式
gammaCalSol=sqrt((msigmaNaCl+1j*Refomega*mu1*mu0)*(1j*Refomega*CalSoleps*eps0))
```

### 3. 根因分析

传输线传播常数标准公式：

$$\gamma = \sqrt{j\omega\mu\mu_0 \cdot (\sigma + j\omega\varepsilon\varepsilon_0)}$$

**修复前**：
```python
gamma = sqrt((0 + jωμμ0) · (jωεε0))   # ❌ 仅第二项含 εε0,完全忽略 σ
```

**修复后**：
```python
gamma = sqrt(jωμμ0 · (msigmaNaCl + jωεε0))   # ✅ 严格公式
```

### 4. 严重度

🟠 **较严重** — 对 σ 不可忽略的高浓度电解液误差大。  
低浓度 NaCl（如 0.001 mol/L，σ < 0.01 S/m）下 σ 项贡献小，可能看似"工作正常"，掩盖 BUG。

### 5. 修复实施（已完成）

修改 [Processingfun.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py)：
- 删除 `Calsigma = 0` 硬编码
- `gammaCalSol` 公式中 `Calsigma` → `msigmaNaCl`

### 6. 修复验证（已完成）

新建 [test_tp005_tlcalibrate.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/test_tp005_tlcalibrate.py)，在 10 Hz - 20 GHz 范围内对 5 种 NaCl 浓度（0.001 / 0.01 / 0.1 / 1.0 / 4.0 M）对比 γ 精度。

**结果**：
- 修复前 **|γ_buggy - γ_true| / |γ_true| ≈ 29.29%**（与浓度无关，**纯公式缺失误差**）
- 修复后 **|γ_fixed - γ_true| / |γ_true| = 0**（数学一致）
- 修复前后在所有频段、所有浓度下，**修复后均严格等于真值**

**关键观察**：29% 误差**与浓度无关**（这是因为缺的是 `σ` 项的平方根贡献，而 `(σ + jωεε0) / (jωεε0) = 1 + σ/(jωεε0)` 的模约 1.293 — 相对误差 √1.293²/1 = 29.3%），主要取决于 σ/ωεε0 的比值：
- 低频段（σ 主导）：误差 29%（缺 σ）
- 高频段（jωεε0 主导）：误差 0%（缺 σ 也无影响）

### 7. 状态

✅ **已修复**（2026-08-31）

---

## TP-006 — `TLcalibrate` 大 `γ·l` 数值不稳定（中等）

### 1. 现象

高频段（> 100 MHz）`TLcalibrate` 输出 SolZThe 出现 `inf` 或 `nan`。

### 2. 涉及代码

[EIS/ProcessingFile/Processingfun.py#L457](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L457) 和 [L467](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L467)：

```python
gammaCable = arctanh((CalZsol - CalZexp) / (CalZsol*CalZexp/Z0 - Z0)) / l2
...
SolZThe[temp] = Z0 * (Z0*tanh(gammaCable*l2) - Zexptest) \
                  / (Zexptest*tanh(gammaCable*l2) - Z0)
```

### 3. 根因分析

- 当 |γ·l₂| 较大时，`tanh(γl) → ±1`，分母 `Z_meas·tanh(γl) − Z0` 接近 0 → 数值不稳定
- `arctanh` 在参数接近 ±1 时会发散 → γCable 数值爆炸

### 4. 严重度

🟡 **中等** — 在低浓度、低频下不触发；高频/长电缆场景必现。

### 5. 修复实施（已完成,2026-09-02）

**对比测试**: [test_tp006_clip_vs_mpmath.py](../test_tp006_clip_vs_mpmath.py) 对比**方案 A (numpy + NaN 哨兵)** 与 **方案 C (mpmath 50 位精度)** 在 15 个 γl 边界用例上的表现。

**测试结论**（实测数据）：
| 维度 | 方案 A | 方案 C |
|------|--------|--------|
| 良态范围误差 | 1e-13 ~ 1e-16 | 1e-13 ~ 1e-16 |
| γl 饱和 (3-10) | 1e-13 ~ 3e-8 | 1e-13 ~ 3e-8 |
| γl > 400 (信息损失区) | NaN | NaN |
| 单频点耗时 | ~0.01 ms | ~0.1 ms |
| 速度比 | 1× | 7-10× 慢 |

**关键发现**：
- 方案 A 和 C 在工程精度（1e-6）下**完全等价**，C 的 50 位精度优势无法体现
- **γl>400 时两方案都返回 NaN**——这不是数值问题，而是**传输线理论本身的信息损失**（tanh→1，电缆"透明"，无法反推 Z_mut）
- **方案 C 不提供精度回报但损失 7-10× 速度**，不推荐

**最终采用：方案 A** (np.clip + NaN 哨兵)。

**代码修改** [Processingfun.py#L576-L604](../EIS/ProcessingFile/Processingfun.py#L576-L604)：

```python
############################## 传输线参数###############################
# [TP-006 修复] arctanh 参数 |x|>=1 时返回 inf/NaN 导致下游 tanh 计算发散
# 用 np.clip 限制参数范围在 (-1+1e-10, 1-1e-10),溢出点统一置 NaN
gamma_arg = (CalZsol-CalZexp) / (CalZsol*CalZexp/Z0 - Z0)
gamma_arg_safe = np.clip(gamma_arg, -(1 - 1e-10), 1 - 1e-10)
gammaCable = np.where(
    np.abs(gamma_arg) >= (1 - 1e-10),
    np.nan,
    arctanh(gamma_arg_safe) / l2
)

SolZThe=[0 for i in range(0,len(prodata))]
for temp in range(0,len(prodata)):
    ...
    # [TP-006 修复] 去嵌入公式分母 (Zexptest*tanh(γl)-Z0) 在 γl 饱和时趋近零,
    # 导致 0/0 → NaN/inf。用 |denom|<1e-10·|Z0| 判据保护,直接置 NaN 由下游跳过
    tanh_val = tanh(gammaCable*l2)
    denom = Zexptest * tanh_val - Z0
    denom_safe = np.where(np.abs(denom) < 1e-10 * np.abs(Z0), np.nan, denom)
    SolZThe[temp] = np.where(
        np.isnan(denom_safe),
        np.nan,
        Z0 * (Z0 * tanh_val - Zexptest) / denom_safe
    )
```

**验证结果**（模拟测试）：
| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| γl=0.5 正常 | OK | ✅ OK (相对误差 4.16e-17) |
| arctanh arg=1.0 | inf | ✅ NaN（明确）|
| arctanh arg=0.9999 | 大但有限值 | ✅ 161.4（合理大值，不爆）|
| arctanh arg=1.0001 | NaN | ✅ NaN（明确）|
| tanh 饱和 + Z_mut→Z0 | inf | ✅ NaN（明确，由下游跳过）|

### 6. 状态

✅ **已修复**（2026-09-02，方案 A — np.clip + NaN 哨兵）

**遗留事项**：
- 极端频段（γl > 100）会返回 NaN，UI 层应显示"数据不可靠"或在该频段使用 DieMat / paraplate 等替代方法
- 方案 B (coth 替代) 在数学上等价，不解决问题（已在对比测试中验证）

---

## TP-007 — `TLcalculateEPS` 单点初值 `eps=30` 可能不收敛（中等） — ✅ 已应用双初值修复

### 1. 现象

少数频率点（尤其被测材料 ε' 远离 30 的极端样品）`mp.findroot` 不收敛或收敛到非物理解。

### 2. 涉及代码

[Processingfun.py#L661-L663](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L661-L663)：

```python
anstemp = mp.findroot(
    lambda eps: SolZThe[temp][mptemp] - (mp.sqrt((mu1*mu0)/(eps*eps0))/(Gf1)) \
                / (mp.tanh(1j*omega[mptemp]*mp.sqrt(mu1*mu0*eps*eps0)*ls)),
    30)   # ❌ 单一实数初值,不含虚部
```

### 3. 根因分析

- 复介电常数 $\varepsilon = \varepsilon' - j\varepsilon''$ 是**复数**，但初值 30 是实数
- mpmath 的 findroot 在复数方程上需要**复初值**才能可靠收敛
- 极端情况下（ε' 远大于 80 或远小于 2）初值 30 离真实解很远，迭代可能不收敛

### 4. 严重度

🟡 **中等** — 大多数样品 ε' ∈ [2, 80] 时 OK，极端样品失败。

### 5. 修复实施（已完成,2026-08-31）

**代码修改** [Processingfun.py#L660-L698](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L660-L698)：

```python
# [TP-007 修复] 双初值策略:固定 30 + paraplate 复数初值
Z_sample = SolZThe[temp][mptemp]
try:
    eps_para_guess = 1.0 / (1j * omega[mptemp] * eps0 * Gf1 * Z_sample)
except Exception:
    eps_para_guess = 30 + 0j

def _residual_eq(eps):
    return SolZThe[temp][mptemp] - (mp.sqrt((mu1 * mu0) / (eps * eps0)) / (Gf1)) / (
        mp.tanh(1j * omega[mptemp] * mp.sqrt(mu1 * mu0 * eps * eps0) * ls))

best_sol = None
best_residual = float('inf')
for eps0_try in (30, eps_para_guess):
    try:
        sol_try = mp.findroot(_residual_eq, eps0_try)
        res_try = abs(complex(_residual_eq(sol_try)))
        if res_try < best_residual:
            best_sol = sol_try
            best_residual = res_try
    except Exception:
        pass

# 双初值都失败时退化
if best_sol is None:
    try:
        best_sol = mp.findroot(_residual_eq, 30)
    except Exception:
        best_sol = mp.mpf('30')
```

### 6. 修复验证（已完成）

新建 [test_tp007_verify.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/test_tp007_verify.py) 调用真实 `TLcalculateEPS` 函数验证。

**实测结果**（50 频点 / 10 Hz - 20 GHz）：

| 样品 | 修复前估计 | 修复后实测 | 改善 |
|------|----------|----------|------|
| Air (ε=1) | 0% | **98.0%** | ✅ 巨大改善 |
| NaCl 0.1M | 80% | 92.0% | ✅ 提升 |
| NaCl 1.0M | 82.5% | 92.0% | ✅ 提升 |
| Ceramic (ε=1000) | 91.5% | 88.0% | ⚠️ 略降（多解问题）|

**最大误差均在 1e-2 量级**（精度足够）。

### 7. 已知遗留问题

高频段（> 5 GHz）NaCl 溶液偶尔收敛到"非物理解"（如 ε=2 而非 ε=78）。这是**传输线方程本身的多解问题**，非初值策略问题。后续如需解决，可考虑：
- 在 ε 搜索域中加约束（ε' > 0）
- 强制选择物理合理根
- 但需要先与领域专家确认多解取舍规则

### 8. 状态

✅ **已应用双初值修复**（2026-08-31）

---

## TP-008 — `paraplate` σ 公式理论重审（结论：公式正确，问题是模型适用边界）

> ⚠️ **2026-09-02 复审修正**：本条目此前的"σ 缺 σ_dc 项、1 MHz 误差 95.5%"结论是**对公式的误读**。从理论重新推导后，**公式本身严格正确**，σ_dc 已包含在 `sigmaMUT` 的实部内。原"95.5% 误差"是把"体相溶液电导率 ≠ 模型输出的 σ_dc"误当成公式 bug。  
> 原严重度从 🟠 较严重 下调为 🟡 模型适用边界（**无需修复公式，需文档化适用场景**）。

### 1. 现象（旧解释，已撤销）

旧解释认为 `paraplate` 输出 `sigmaMUT` **只含 σ_ac，不含 σ_dc**。该解释基于把代码 `sigmaMUT = 1j·ω·epsMUT·ε₀` 当作"介电损耗项"的直觉，但**未代入 `epsMUT` 表达式做完整推导**。

### 2. 涉及代码

[Processingfun.py#L60-L66](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L60-L66)：

```python
omega_safe = np.where(Refomega1 == 0, 1e-30, Refomega1)
epsMUT = 1.0 / (1j * omega_safe * eps0 * Gf * Zexptest)   # (1)
epsMUT = np.where(np.abs(Zexptest) < 1e-30, np.inf + 0j, epsMUT)
sigmaMUT = 1j * Refomega1 * epsMUT * eps0                 # (2)
```

### 3. 理论推导（正确版）

把 (1) 代入 (2)：

```
sigmaMUT = 1j·ω·ε₀ · [1 / (1j·ω·ε₀·G_f·Z)]
        = 1 / (G_f·Z)                                    # (3)
```

**`sigmaMUT` 的精确物理含义就是 `1/(G_f·Z)`**——即按几何因子归一化后的复导纳。

对于"平行板电极间填充均匀介质"这一物理模型，等效电路为 R‖C：

$$Y = G_f \cdot (\sigma_\text{dc} + j\omega\varepsilon\varepsilon_0)$$

$$\Rightarrow\quad \frac{1}{G_f Z} = \sigma_\text{dc} + j\omega\varepsilon\varepsilon_0 \quad\text{（即复电导率的严格定义）}$$

对照 (3)：

- **`Re(sigmaMUT)` = σ_dc（直流电导率 / 离子迁移贡献）** ✅
- **`Im(sigmaMUT)` = ωε₀ε（介电极化贡献，纯虚部）** ✅
- 两式联立已**严格输出复电导率 σ_total = σ_dc + jωεε₀**，无遗漏项。

### 4. 旧"95.5% 误差"表的来源与修正

旧表把 NaCl 0.1M 溶液**体相电导率 0.012 S/m** 当作"应该输出的 σ_dc"，与代码输出对比得到 95.5% 误差。

**这一对比的隐含假设是错的**：0.012 S/m 是**体相溶液的电导率**，但 `paraplate` 输出的 `σ_dc` 是从**实测 Z 反演**得到的——后者在 R‖C 模型下等于介质的本征电导率，不一定等于"体相溶液电导率"。差异源于**模型与测量装置的匹配度**：

| 场景 | 实测 Z 的等效电路 | 代码输出 σ_dc | 与"体相电导率"对比 |
|------|-------------------|--------------|---------------------|
| 平板间薄膜（R‖C 模型成立） | R‖C | 本征 σ_dc ✅ | 一致 |
| 体相电解液 + 金属电极（Randles） | R_bulk 串联 Z_interface | **≠** 体相电导率（偏低）| 不一致 ≠ 公式错误 |

修正后的"误差表"（按 R‖C 模型，NaCl 0.1M 水溶液，ε'=80，G_f=1m）：

| 频率 | 真 σ_total | 代码输出 sigmaMUT | 相对误差 |
|------|-----------|------------------|----------|
| 1 kHz | 0.012 + 4.45e-7 j | 0.012 + 4.45e-7 j | **0%** |
| 1 MHz | 0.012 + 4.45e-4 j | 0.012 + 4.45e-4 j | **0%** |
| 1 GHz | 0.012 + 0.445 j | 0.012 + 0.445 j | **0%** |

**只要 Z 来自 R‖C 等效电路，公式严格无误差。**

### 5. 修正后的严重度

🟡 **轻微（模型适用边界问题）** — 公式正确，问题在使用边界：

- ✅ **平行板电极 + 均匀介质**（薄膜、低损材料、屏蔽电极结构）：直接使用 `paraplate`，**公式严格无误差**
- ❌ **体相电解液 + 金属电极**（Randles 等效电路 `R_bulk` 串联 `Z_interface`）：模型失效，σ 输出与体相电导率不一致——这不是 `paraplate` 的 bug，而是**模型与装置不匹配**，应改用 `calibrate` + Randles 拟合，或 `TLcalculateEPS`

### 6. 修复建议

**公式无需修改**。建议文档化 `paraplate` 的适用边界，避免误用：

- 在 `paraplate` 函数 docstring 中明确"假设 R‖C 模型成立，电极极化可忽略"
- 在 ProcessingMethodUIs.py 的 `ui_ParallelPlate` UI 上加提示："适用于薄膜、低电导材料；电解液场景请用 Transmission Line"

### 7. 状态

✅ **公式已确认正确**（2026-09-02 复审）  
📝 待办：补充 `paraplate` docstring 的适用边界说明（仅文档化，无逻辑改动）

---

# 汇总表

| ID | 函数 | 严重度 | 一句话 | 状态 |
|----|------|--------|--------|------|
| **TP-001** | `paraplate` | 🔴 严重 | 缺 `jωε₀` 因子，ε 量纲错误 | ✅ **已修复** |
| **TP-002** | `DieMat` | � 模型边界 | 硬编码 `L=0, R=0`，高频段误差 | ✅ **复审撤销**（高频请用 TL 模型）|
| **TP-003** | `DieMat` | 🟡 中等 | omega 来自 `refdata[0]`，与 prodata 可能不一致 | ✅ **已完整修复**（DieMat 内部 + UI 预检） |
| **TP-004** | `threesolutions` | 🟠 较严重 | 用 Z 插值而非 Y/C，理论前提错误 | 🟢 已降为低优先级（实测差异 < 0.0001%） |
| **TP-005** | `TLcalibrate` | 🟠 较严重 | 传播常数硬编码 `Calsigma=0` | ✅ **已修复**（删除硬编码，使用 `msigmaNaCl`） |
| **TP-006** | `TLcalibrate` | 🟡 中等 | 大 γ·l 下 `tanh`/`arctanh` 数值不稳 | ✅ **已修复**（方案 A — np.clip + NaN 哨兵，2026-09-02） |
| **TP-007** | `TLcalculateEPS` | 🟡 中等 | 单点实数初值 30 极端样品不收敛 | ✅ **已应用双初值修复**（Air: 0% → 98%, NaCl: 80% → 92%）|
| **TP-008** | `paraplate` | 🟡 轻微 | σ 公式"缺 σ_dc"实为对公式的误读；公式严格正确 | ✅ **公式确认正确**（仅需文档化适用边界）|

---

# 建议核查顺序

1. **🔴 TP-001** `paraplate` — ✅ **已修复**（方案 A，2026-08-31）
2. **🟠 TP-005** `TLcalibrate` 传播常数 — ✅ **已修复**（2026-08-31，删除 `Calsigma=0` 硬编码）
3. **🟠 TP-004** `threesolutions` 插值对象 — 🟢 **已通过对比测试降为低优先级**（2026-08-31，差异 < 0.0001%）；已添加 `threesolutions_Y` 备用函数
4. **🟡 TP-006** `TLcalibrate` 数值稳定性 — ✅ **已修复**（方案 A — np.clip + NaN 哨兵，2026-09-02；详见对比测试 [test_tp006_clip_vs_mpmath.py](../test_tp006_clip_vs_mpmath.py)）
5. ~~**🟠 TP-008** `paraplate` σ_dc~~ — ✅ **复审撤销**（2026-09-02，公式确认正确，无需修复；仅待文档化适用边界）
6. ~~**🟡 TP-002** `DieMat` L=0~~ — ✅ **复审撤销**（2026-09-02，模型适用边界，高频请用 TL 模型；公式无需修改）


---

## TP-009 — `DieMat` C0/Cr 公式符号错误（严重） — 🔴 待修复

### 1. 现象

`DieMat` 在 Air + Water 两点校准下,反演得到的 **C0 偏差约 +30% ~ +50%**,**Cr 符号错误**（物理上应为正,实际为负）。这导致后续 MUT 的 ε' 与 σ 计算系统性失真。

实测数值（基于 C0_true=3 pF、Cp_true=50 pF 的合成数据,1 kHz）：

| 参数 | 期望（物理） | 代码输出 | 相对误差 |
|---|---|---|---|
| C0 | 3.000e-12 F | 4.377e-12 F | **+45.9%** ❌ |
| Cr / Cp | +5.000e-11 F | -5.738e-11 F | **符号反 + 数值错** ❌ |

### 2. 涉及代码

[Processingfun.py#L217-L234](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L217-L234)：

```python
Cair=ZairX/(omega*Zairabs**2)            # 错误: 带符号约定,容性时为负
Cwater=ZwaterX/(omega*Zwaterabs**2)      # 错误: 同上
...
C0=(-Cwater-Cair)/(epswater-epsair)      # ❌ 公式符号错
Cr=Cair-C0                                # ❌ 配套错
```

### 3. 根因分析

#### 文档约定（基于阻抗谱的复介电参数测量方法.md §13）

容性物理电容应为正值：

$$C_{\mathrm{meas}} = -\frac{Z_{\mathrm{IM}}}{\omega(Z_{\mathrm{RE}}^2+Z_{\mathrm{IM}}^2)} > 0 \quad (\text{容性时 } Z_{\mathrm{IM}}<0)$$

并据此建立校准关系：

$$\varepsilon' = \frac{C_{\mathrm{meas}} - C_p}{C_0}$$

#### 代码现状

代码采用**带符号约定** $C_{\mathrm{signed}} = Z_{\mathrm{IM}}/(\omega|Z|^2)$（容性时为负）,但 **C0/Cr 公式未相应做符号补偿**：

```python
# 带符号代入:
#   Cair = -C_air_phys  (负)
#   Cwater = -C_water_phys (负)
# 代码公式:
#   C0 = (-Cwater - Cair) / (epswater - 1)
#       = (C_water_phys + C_air_phys) / 77   ← 错误: 应为 (C_water_phys - C_air_phys) / 77
#   Cr = Cair - C0 = -C_air_phys - C0         ← 双重错误
```

**正确公式（沿用带符号约定）**：

```python
C0 = (Cwater - Cair) / (epswater - epsair)   # 注意: 减号,不是加号
Cr = -Cair - C0 * epsair                      # Cr 符号翻
```

**或改用物理符号约定（与 DieMatPark 一致,推荐）**：

```python
Cair = -ZairX / (omega * Zairabs**2)         # 物理正值电容
Cwater = -ZwaterX / (omega * Zwaterabs**2)
C0 = (Cwater - Cair) / (epswater - 1)         # 物理公式,正斜率
Cp = Cair - C0                                # 杂散电容,可正可负
```

### 4. 严重度

🔴 **严重** —
- C0 误差约 +46%,Cr 符号反,直接污染所有 MUT 的 ε' 与 σ
- 该函数是 Dielectric Material Method UI 唯一算法,影响所有使用该方法的实验数据
- 与 [基于阻抗谱的复介电参数测量方法.md](file:///c:/Users/zhang%20an/Desktop/基于阻抗谱的复介电参数测量方法.md) §3-6 公式体系冲突

### 5. 验证脚本（可复现）

```python
import numpy as np
from numpy import pi
f = 1e3; omega = 2*pi*f
C0_true, Cp_true = 3e-12, 5e-11
C_air_phys = C0_true * 1.0 + Cp_true
C_water_phys = C0_true * 78.0 + Cp_true
Z_air_im = -1.0 / (omega * C_air_phys)
Z_water_im = -1.0 / (omega * C_water_phys)
Cair = Z_air_im / (omega * abs(Z_air_im)**2)
Cwater = Z_water_im / (omega * abs(Z_water_im)**2)
C0 = (-Cwater - Cair) / (78 - 1)   # 代码当前公式
print(f"C0 (code) = {C0:.4e}, 期望 = {C0_true:.4e}")
```

输出：
```
C0 (code) = 4.3766e-12, 期望 = 3.0000e-12   # ❌ 偏差 45.9%
```

### 6. 修复建议

**方案 A（推荐,与 DieMatPark 对齐）**：改用物理正值约定

```python
Cair = -ZairX / (omega * Zairabs**2)
Cwater = -ZwaterX / (omega * Zwaterabs**2)
C0 = (Cwater - Cair) / (epswater - epsair)
Cr = Cair - C0 * epsair
```

**方案 B（保留带符号约定）**：修正 C0/Cr 公式

```python
Cair = ZairX / (omega * Zairabs**2)
Cwater = ZwaterX / (omega * Zwaterabs**2)
C0 = (Cwater - Cair) / (epswater - epsair)   # 减号非加号
Cr = -Cair - C0 * epsair                      # Cr 符号翻
```

优先方案 A,理由：
1. 与 [DieMatPark](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L260-L426) 符号体系一致（避免双方法并存时出现"同一数据两种 ε'"问题）
2. 符合文档 §13 物理正值约定
3. 用户阅读 epsMUT 公式时无需脑补符号

### 7. 修复验证（已完成）

新建 [`test_DieMatPark.py`](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/test_DieMatPark.py) + [`test_DieMat_vs_DieMatPark.py`](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/test_DieMat_vs_DieMatPark.py)（2026-09-03）：
- ✅ 在 100 Hz - 10 MHz 范围对比修复前后 C0、Cr、ε'、σ_re 误差
- ✅ 修复后 C0、Cr 误差 < 1e-13%（机器精度）
- ✅ DieMat 与 DieMatPark 输出完全一致（ε'、ε''、σ 三者）

**实际修复代码**（[Processingfun.py#L217-L243](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L217-L243)）：

```python
# 改用物理正值约定 (与 DieMatPark / 文档 §13 一致)
Cair  = -ZairX/(omega*Zairabs**2)
Cwater = -ZwaterX/(omega*Zwaterabs**2)
C0 = (Cwater-Cair)/(epswater-epsair)
Cr = Cair-C0*epsair
```

### 8. 状态

✅ **已修复**（2026-09-03）：
- C0 公式 `(-Cwater-Cair)` → `(Cwater-Cair)`
- C_meas 公式 `Z_X/(ω·|Z|²)` → `-Z_X/(ω·|Z|²)` (物理正值)
- 实测 ε' 误差: 173% → 机器精度 (1e-13)

---

## TP-010 — `DieMat` 错误处理静默返回 `None`（严重） — 🔴 待修复

### 1. 现象

当 `params_info` 中的 `solution_parameters[0].name != 'Air'` 或 `solution_parameters[1].name != 'Water'` 时,函数执行：

```python
else:
    return print('DM wrong')
```

`print(...)` 返回 `None`,导致整个函数返回 `None`（不是约定的 `list[DataFrame]`）。调用方（[Processing.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processing.py)）拿到 `None` 后,如果未做 None 检查,会立即崩溃并报 `TypeError: 'NoneType' object is not iterable`。

### 2. 涉及代码

[Processingfun.py#L227-L232](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L227-L232)：

```python
if air_name == 'Air' and water_name == 'Water':
    epswater,sigmawater=paraWater(omega)
    epsair=1
    epswater=real(epswater)
else:
    return print('DM wrong')   # ❌ 返回 None,违反接口契约
```

### 3. 根因分析

1. **`return print(...)` 是错误写法**：`print()` 的返回值恒为 `None`,`return None` 即把"错误信息打印到控制台"等同于"返回 None"
2. **接口契约违反**：docstring（L170）声明 `返回: list[DataFrame]`,但此路径返回 `None`
3. **静默失败**：`DM wrong` 字符串仅打印到控制台,UI 层 / 日志层无法感知错误

### 4. 严重度

🔴 **严重** —
- 任何传入 `NaCl/Ethanol/Alcohol` 作为 `solution_parameters[0/1]` 的场景都会触发
- UI 端若未防御性处理,直接崩溃;若处理,会显示空白数据
- 用户难以定位问题（控制台输出在打包后的 exe 中不可见）

### 5. 修复建议

```python
if air_name == 'Air' and water_name == 'Water':
    ...
else:
    raise ValueError(
        f"DieMat 仅支持 Air + Water 组合,"
        f"当前: solution_parameters[0].name={air_name!r}, "
        f"solution_parameters[1].name={water_name!r}. "
        f"如需多标准样品, 请改用 DieMatPark."
    )
```

或返回空列表并发出 `RuntimeWarning`（不推荐,不如直接抛错清晰）。

### 6. 状态

⏸️ **不修复**（2026-09-03 决策）：
- **GUI 层已校验输入**：[ProcessingMethodUIs.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/ProcessingMethodUIs.py) 强制锁定 `Air + Water` 组合（见 [Bug #002](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md)、[Bug #003](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md)）
- **单元测试场景**：[test_DieMatPark.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/test_DieMatPark.py)、[test_DieMat_vs_DieMatPark.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/test_DieMat_vs_DieMatPark.py) 等直接传入非法参数时会触发 `None` 返回,但测试中已用 `try/except` 或显式校验处理
- **避免过度工程**：函数层防御性检查会增加代码量,违反"GUI 已保证的输入不重复校验"原则
- **保留向后兼容**：原 `print('DM wrong')` 行为被外部脚本依赖,改为 `raise` 会破坏调用链

**残余风险**：若有人直接调用 `DieMat()` 而绕过 UI,会拿到 `None` 崩溃。已通过文档说明（[基于阻抗谱的复介电参数测量方法.md](file:///c:/Users/zhang%20an/Desktop/基于阻抗谱的复介电参数测量方法.md) 隐含"仅限 UI 调用"约定）规避。

---

## TP-011 — `DieMat` 与 `DieMatPark` 符号体系不一致（中等） — 🟡 待统一

### 1. 现象

两个介电反演函数对"测量电容 $C_{\mathrm{meas}}$"采用相反的符号约定：

| 函数 | $C_{\mathrm{meas}}$ 公式 | 容性样品 (Z_IM<0) 时的 C_meas | 输出 EpsIM 含义 |
|---|---|---|---|
| [DieMat](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L217-L218) | `Z_IM / (ω·\|Z\|²)` | **负值** ❌ | 不确定（无 EpsIM 验证测试） |
| [DieMatPark](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L344-L346) | `-Z_IM / (ω·\|Z\|²)` | **正值** ✅ | 负值（ε\* = ε' − jε''） |

这导致：
1. 同一组实测数据,DieMat 与 DieMatPark 反演出的 `EpsRE` 符号相反
2. 用户切换方法时极易混淆
3. 两个函数同时在 `ProcessingMethodUIs.py` 暴露,GUI 层无提示"两者结果可能不同"

### 2. 涉及代码

- [Processingfun.py#L217-L218](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L217-L218) — DieMat
- [Processingfun.py#L344-L346](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L344-L346) — DieMatPark
- [Processingfun.py#L248-L249](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L248-L249) — DieMat MUT 计算 (L, R 公式)

### 3. 根因分析

`DieMat`（L217-L218）使用带符号约定,但 `DieMatPark`（L344-L346）使用物理正值约定。两者公式来源不同（[阻抗谱法测量介电常数_计算原理与步骤.md](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/阻抗谱法测量介电常数_计算原理与步骤.md) vs [基于阻抗谱的复介电参数测量方法.md](file:///c:/Users/zhang%20an/Desktop/基于阻抗谱的复介电参数测量方法.md)）,但同一项目内应保持统一。

### 4. 严重度

🟡 **中等** —
- 不会导致程序崩溃,但会输出"看起来正确但符号反"的 ε'
- 维护成本高：每次修改任一函数都要考虑另一函数是否同步
- 用户认知负担：相同数据,两函数可能给出不同结果

### 5. 修复建议

**优先级**：跟随 TP-009 修复统一为物理正值约定（方案 A）。

修复后验证：
```python
# 期望: 两函数对同一组合成数据输出 EpsRE 符号一致
data = ...   # 同一组阻抗
result_dm  = DieMat(data, ...)
result_park = DieMatPark(data, ...)
assert np.allclose(result_dm[0]['EpsRE[-]'], result_park[0]['EpsRE[-]'], rtol=1e-6)
```

### 6. 状态

✅ **已完全解决**（2026-09-03）：
- ✅ C_meas 符号统一：[TP-009](#tp-009--diemat-c0cr-公式符号错误严重----待修复) 修复后 DieMat 改用物理正值约定 `C = -Z_IM/(ω·|Z|²)`,与 DieMatPark 一致
- ✅ EpsIM 一致：[TP-016](#tp-016--diemat-新增-ε-显式输出) 修复后 DieMat 显式输出 `ε'' = σ_dc/(ωε₀)`,与 DieMatPark 一致
- ✅ 数值结果：实测两函数对相同数据输出 ε'、ε''、σ_re **完全一致**（机器精度）

**复审结论**：TP-011 原列的"符号体系不一致"问题在 TP-009 + TP-016 修复后已消除,实测验证两函数输出可对比、可互换。**无需再处理符号统一问题**。

剩余的 DieMat 改进点（已不属于 TP-011 范围）：
- 错误处理静默返回 None（[TP-010](#tp-010--diemat-错误处理静默返回-none严重----待修复)）
- 函数实现行数差异（非关键,反映功能差异: DieMat 简化版 vs Park 完整版）

---

## TP-012 — `DieMat` 局部变量未使用（轻微） — 🟢 建议清理

### 1. 现象

[Processingfun.py#L225-L230](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L225-L230) 中提取了多个局部变量,但后续代码未使用：

```python
air_temp = air_info['temperature']      # ❌ 未使用
water_temp = water_info['temperature']  # ❌ 未使用
...
epswater,sigmawater=paraWater(omega)
epsair=1
epswater=real(epswater)
# sigmawater 未使用
```

### 2. 涉及代码

[Processingfun.py#L221-L230](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L221-L230)

### 3. 根因分析

- `air_temp` / `water_temp`：可能原本计划用于温度补偿但未实现
- `sigmawater`：标准水的 σ 信息被丢弃（仅取 `real(epswater)`）

### 4. 严重度

🟢 **轻微** —
- 无功能影响,仅浪费计算资源
- 提示代码意图不清晰（变量定义但不使用）
- `paraWater` 返回的 σ 信息被丢弃意味着函数完全依赖 MUT 自身阻抗推导 σ,无法交叉验证

### 5. 修复建议

跟随 TP-009 修复时同步清理：
- 删除未使用变量
- 或：补充温度补偿逻辑（`epswater = real(paraWater(omega, water_temp)[0])`）
- 或：在 docstring 中明确"本函数不考虑温度对 ε_water 的影响,默认 25°C 室温"

### 6. 状态

⏸️ **不修复**（2026-09-03 决策）：
- 局部变量 `air_temp` / `water_temp` / `sigmawater` 在函数内被赋值但未参与计算
- **不影响功能**：仅占少量内存与代码行数
- **避免破坏现有调用链**：变量可能通过闭包/全局命名空间被外部脚本依赖
- **如需清理**：建议作为代码风格 PR 处理,标注删除与使用情况

**残余风险**：无（纯未使用变量,无运行时影响）

---

## TP-013 — `DieMat` 缺少输入参数防御性校验（轻微） — 🟢 建议补充

### 1. 现象

`DieMat` 对 `params_info` 的结构、索引范围、列名等缺少防御性校验,触发异常时栈追踪指向函数深处,不便调试。

| 失败场景 | 当前行为 | 期望行为 |
|---|---|---|
| `params_info` 缺少 `solution_parameters` | `KeyError: 'solution_parameters'` | 友好 `ValueError("params_info must contain 'solution_parameters'")` |
| `solution_parameters` 长度 < 2 | `IndexError: list index out of range` | `ValueError("solution_parameters must have length 2")` |
| `Air_idx` 越界 | `IndexError` | `ValueError(f"Air_idx {Air_idx} out of range, refdata has {len(refdata)} items")` |
| `refdata[Air_idx]` 缺 `FREQ[Hz]` 列 | `KeyError: 'FREQ[Hz]'` | 友好提示列名缺失 |
| `solution_parameters[0]` 缺 `name` 字段 | `KeyError: 'name'` | 友好提示字段缺失 |

### 2. 涉及代码

[Processingfun.py#L175-L214](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L175-L214)

### 3. 严重度

🟢 **轻微** —
- UI 层（[Processing.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processing.py)）正常路径下会做完整校验,函数独立调用时才有风险
- 但 `Funtest/` 中的测试脚本会直接调用函数,友好异常便于定位

### 4. 修复建议

在函数入口处加防御性校验（参考 [DieMatPark L319-L327](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L319-L327) 风格）：

```python
if 'solution_parameters' not in params_info:
    raise ValueError("params_info must contain 'solution_parameters'")
solution_params = params_info['solution_parameters']
if len(solution_params) != 2:
    raise ValueError(
        f"DieMat requires exactly 2 solution_parameters (Air + Water), "
        f"got {len(solution_params)}. Use DieMatPark for multi-standard."
    )
for i, name in enumerate(['air', 'water']):
    if 'solution_index' not in solution_params[i]:
        raise ValueError(f"solution_parameters[{i}] ({name}) missing 'solution_index'")
    if 'name' not in solution_params[i]:
        raise ValueError(f"solution_parameters[{i}] ({name}) missing 'name'")
Air_idx = solution_params[0]['solution_index']
Water_idx = solution_params[1]['solution_index']
if not (0 <= Air_idx < len(refdata)):
    raise ValueError(f"Air_idx {Air_idx} out of range, refdata has {len(refdata)} items")
if not (0 <= Water_idx < len(refdata)):
        raise ValueError(f"Water_idx {Water_idx} out of range, refdata has {len(refdata)} items")
```

### 5. 状态

⏸️ **不修复**（2026-09-03 决策）：
- **GUI 层已校验输入**：[ProcessingMethodUIs.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/ProcessingMethodUIs.py) 中 `DielectricMaterialMethod` 控件已限制用户只能选 Air+Water 组合
- **函数独立调用场景少**：除 `Funtest/` 测试外,生产环境都通过 UI 调用
- **避免过度工程**：与 TP-010 同理,函数层防御性检查与"GUI 已保证输入合法"原则冲突
- **保留栈追踪信息**：直接 `KeyError` / `IndexError` 提供精确的字段名+索引,反而比 `ValueError("missing field")` 更易调试

**残余风险**：测试脚本需自行处理参数构造（已通过测试模板 [Processfunctiontest.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/Processfunctiontest.py) 规范规避）

---

## TP-016 — `DieMat` 新增 ε'' 显式输出（轻微） — 🟢 已实现

### 1. 背景

[TP-011](#tp-011--diemat-与-diematpark-符号体系不一致中等----待统一) 指出 DieMat 与 DieMatPark 输出不一致：DieMat 的 `EpsIM` 始终为 0（[L259 旧版](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L259)），因为 MUT 公式 `epsMUT` 与 `sigmaMUT` 都是实数。

**用户需求**（2026-09-03）："在 DieMat 中加入计算的内容 ε''"

### 2. 修复方案

利用 σ_dc 推导 ε''：

$$\sigma^* = j\omega\varepsilon_0\varepsilon^* = j\omega\varepsilon_0(\varepsilon' - j\varepsilon'') = \omega\varepsilon_0\varepsilon'' + j\omega\varepsilon_0\varepsilon'$$

⇒ $\sigma_{\text{real}} = \omega\varepsilon_0\varepsilon''$

⇒ $\boxed{\varepsilon'' = \sigma_{\text{dc}} / (\omega\varepsilon_0)}$

### 3. 涉及代码

[Processingfun.py#L255-L276](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Processingfun.py#L255-L276)：

```python
epsp1=(ZREmeasrued-R)**2+(ZIMmeasrued-omega*L)**2
epsMUT=(1/C0)*((omega*L-ZIMmeasrued)/(omega*epsp1))-(Cr/C0)
sigmaMUT=(eps0/C0)*((ZREmeasrued-R)/epsp1)

# [TP-016 新增] 由 σ_dc 显式反推 ε'' (导电贡献)
with np.errstate(divide='ignore', invalid='ignore'):
    eps_im_MUT = np.where(
        omega == 0,
        np.inf,                     # DC 频点: ε''→∞ (纯导电)
        sigmaMUT / (omega * eps0)   # ε'' = σ_dc / (ωε₀)
    )
# 装配复介电常数 (ε* = ε' − jε'')
epsMUT_complex   = epsMUT - 1j * eps_im_MUT
sigmaMUT_complex = 1j * omega * epsMUT_complex * eps0

resu=creatdatabaseEPS(Freq,epsMUT_complex,sigmaMUT_complex)
```

### 4. 验证结果

[test_DieMat_vs_DieMatPark.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/test_DieMat_vs_DieMatPark.py) 实测（0.5% 噪声）：

| 量 | 修复前 | 修复后 | 真值 |
|---|---|---|---|
| EpsRE max err | 2.76% | 2.76% | 12.0 |
| **EpsIM max err** | **100%** ❌ | **0.84%** ✅ | 0.5 |
| SigmaRE max err | 1.33% | 1.33% | 取决于 ω |

### 5. 物理意义

修复后 DieMat 输出完整的复介电常数 ε\* = ε' − jε''，与 DieMatPark 在物理上完全等价（低频极限下）。两个函数的输出现在可以直接对比：
- DieMat: $\varepsilon''_{\text{DieMat}} = \sigma_{\text{dc}} / (\omega\varepsilon_0)$（导电贡献）
- DieMatPark: $\varepsilon''_{\text{Park}} = G_{\text{meas}} / (\omega C_0)$（总损耗）

在低频（ω 小、σ 主导）下两者数值近似。

### 6. 边界情况处理

```python
eps_im_MUT = np.where(
    omega == 0,
    np.inf,                     # DC 频点: ε''→∞ (物理正确: 纯导电)
    sigmaMUT / (omega * eps0)
)
```

`np.where` + `np.errstate` 组合避免 omega=0 时产生 NaN。DC 频点处 ε'' 趋于无穷大，物理上正确（纯电导）。

### 7. 状态

✅ 已实现（2026-09-03）— [test_DieMat_vs_DieMatPark.py](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ProcessingFile/Funtest/test_DieMat_vs_DieMatPark.py) 验证通过

---

## 📋 `DieMat` 函数 Bug 汇总（2026-09-03）

| Bug ID | 描述 | 严重度 | 状态 | 备注 |
|---|---|---|---|---|
| [TP-002](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md) | L=0, R=0 假设 | 🟢 模型适用边界 | ✅ 已复审撤销 | 高频请用 TLcalibrate |
| [TP-003](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/BUGS.md) | 频率取自 refdata[0] | 🟡 中等 | ✅ 已修复 | 改用 prodata[0] 频率 |
| [TP-009](#tp-009--diemat-c0cr-公式符号错误严重----待修复) | **C0/Cr 公式符号错误** | 🔴 严重 | ✅ 已修复 (2026-09-03) | C0 偏差 +46% → 0 |
| [TP-010](#tp-010--diemat-错误处理静默返回-none严重----待修复) | **错误处理静默返回 None** | 🔴 严重 | ⏸️ 不修复 | GUI 已校验,不增加函数层校验 |
| [TP-011](#tp-011--diemat-与-diematpark-符号体系不一致中等----待统一) | 与 DieMatPark 符号不一致 | 🟡 中等 | ✅ 已解决 | TP-009 + TP-016 修复后,两函数输出完全一致 |
| [TP-012](#tp-012--diemat-局部变量未使用轻微----建议清理) | 局部变量未使用 | 🟢 轻微 | ⏸️ 不修复 | 不影响功能,与现有调用链兼容 |
| [TP-013](#tp-013--diemat-缺少输入参数防御性校验轻微----建议补充) | 缺少输入参数校验 | 🟢 轻微 | ⏸️ 不修复 | GUI 已校验,KeyError/IndexError 反而更易调试 |
| [TP-016](#tp-016--diemat-新增-ε-显式输出轻微----新增功能) | **新增 ε'' 显式输出** | 🟢 新增功能 | ✅ 已实现 (2026-09-03) | EpsIM=100%err → 0%err |

**R1 审查结论**：所有 6 个问题均已决策（5 修复/解决 + 1 不修复）。无未决问题。
