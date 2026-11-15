# AnyEIS 修改计划（针对审稿意见 R2-1 / R2-3 / R4-Major）

> 本文件**只描述拟议改动，尚未修改任何已有源文件**。请审阅后再决定是否落地。
> 配套新增文件（已创建，不影响现有程序）：
> - `FittingValidationSynthetic.py`（合成算例验证）
> - `FittingValidationYeast.py`（真实 yeast cell 算例）
> - 本计划文件 `CPE_SUPPORT_MODIFICATION_PLAN.md`

---

## 0. 结论摘要

| 编号 | 修改项 | 是否必须 | 影响面 | 工作量 | 风险 |
|---|---|---|---|---|---|
| M1 | ECM 引擎 `elementsZ` 支持 CPE 元件 | **必须**（若论文声称支持 CPE） | `EIS/ModelFile/EquivCircM.py` | 5 行 | 低 |
| M2 | GUI 电路元件表支持 CPE 的两个参数(Q, n) | **必须**（配合 M1） | `EIS/ModelFile/ECMFunctions.py`、`ECUI.py` | 30~50 行 | 中 |
| M3 | 参数识别逻辑区分 CPE | 建议 | `EIS/FittingFile/FittingECM.py` | 5 行 | 低 |
| M4 | `multi_start_fit` 通用化（支持 >3 参数） | 可选 | `EIS/FittingFile/FittingECM_extreme.py` | 30 行 | 低 |
| M5 | 示例数据 + 模型设置随包发布 | **必须**（R4-M2 可复现性） | 仓库目录 | 复制文件 | 无 |
| M6 | 论文文字/图表修改 | **必须** | 稿件 | — | 无 |

**推荐路径：M1 + M2 + M3 + M5 一起做**（约半天工作量），这样论文中的 CPE 相关结论
（合成算例 2/3、yeast 实例模型）在发布的 GUI 中可以原样复现。
若本次不动产品，走第 9 节的备选方案 B。

---

## 1. 现状与证据（为什么必须改）

### 1.1 引擎按首字母判定元件类型

`EIS/ModelFile/EquivCircM.py` 的 `elementsZ()`：

```python
def elementsZ(element,pm,freq):
    if -1!=element.find('C',0,1):     # 'CPE1'[0:1] == 'C'  -> 命中电容分支
        ss=pm[element].value
        Z=C(ss,freq)
        return Z
    elif -1!=element.find('R',0,1):
        ...
```

判定依据是 **元件名首字母**，因此名为 `CPE1` 的元件会被当作**理想电容**静默处理，
用户不会收到任何报错。`CPE()` 辅助函数其实已经存在，但没有被接进 `elementsZ`：

```python
def CPE(T,P,freq):
    Z=1/(T*(1j*2*pi*freq)**P)
    return Z
```

实测验证（只读测试，不改动任何文件）：

```
elementsZ('CPE1', {CPE1: 1e-4}, [1e6])  ->  -1.5915494309189534e-05j     # 与理想电容相同
CPE(1e-4, 0.9, [1e6])                  ->  (1.386254e-05-7.707e-05j)    # 真正的 CPE
```

### 1.2 GUI 侧只暴露了界面，没有功能

- `EIS/ModelFile/ECUI.py` 的元件下拉框中已经有 `'CPE'` 项；
- 但 `ECMFunctions.addelement()` 每添加一个元件只往 `ECMtable` 写**一行、一个初值**，
  参数由元件名 + 该初值构成（`simulation.py` 等处读取表格生成 `Parameters`）。
  因此 CPE 只能有 1 个参数（Q），**指数 n 在 GUI 中根本无法输入**。

结论：GUI 目前可以选择 CPE，但得不到 CPE 的行为。这属于**会误导用户的半成品功能**，
一旦论文声称"支持非理想元件（CPE）"，审稿人按图索骥就会撞上这个问题。

---

## 2. M1：引擎增加 CPE 支持（核心改动）

**文件**：`EIS/ModelFile/EquivCircM.py`，函数 `elementsZ`（约第 80~95 行）

拟议改动（伪 diff，待批准后落地）：

```python
 def elementsZ(element,pm,freq):
-    if -1!=element.find('C',0,1):
+    if element.startswith('CPE'):          # 常相位角元件：参数 CPE<n> = Q, alphaCPE<n> = n
+        Q=pm[element].value
+        n=pm['alpha'+element].value
+        Z=CPE(Q,n,freq)
+        return Z
+    if -1!=element.find('C',0,1):
         ss=pm[element].value
         Z=C(ss,freq)
         return Z
```

约定（与测试脚本中的临时兼容层保持一致，便于结果对照）：

| 电路元件名 | 参数 | 含义 | 单位 |
|---|---|---|---|
| `CPE1` | `CPE1` | Q | F·s^(n-1) |
| `CPE1` | `alphaCPE1` | n（0.5 ≤ n ≤ 1.0） | 无量纲 |

- 兼容性：不含 CPE 的电路行为完全不变（新增分支在最前面，且只匹配 `CPE` 前缀）。
- 物理约束：n > 1 会导致元件非无源，建议在参数表中把 n 限制在 (0, 1]。

---

## 3. M2：GUI 侧支持 CPE 的两个参数

**涉及文件**：`EIS/ModelFile/ECMFunctions.py`（`addelement`）、
`EIS/ModelFile/ECUI.py`（元件表列定义）、以及读取表格生成 `Parameters` 的位置
（`EIS/SimulationFile/simulation.py`、`EIS/FittingFile` 的 ECM 拟合页）。

拟议改动要点：

1. `addelement()`：当 `elementtype == 'CPE'` 时，除了写 `CPE<n>` 行外，
   再写一行 `alphaCPE<n>`，初值建议 `0.9`；表格"元件"列显示 `CPE1 (Q)` / `alphaCPE1 (n)`。
2. 读取表格生成参数时，按现有逻辑逐行 `params[elementname] = Parameter(...)` 即可
   自动得到 `CPE1` 与 `alphaCPE1` 两个参数——**若表格里是两行，则该处无需改动**，
   这是本项改动量小的关键。
3. 参数表（`ECMparams`）与初值界面对 n 增加范围提示（0.5~1.0）。
4. 拟合完成后参数表的"元件"列需要同时展示 Q 与 n（否则用户看不到拟合出的指数）。

需要确认的实现细节：ECM 拟合页的表格与仿真页的表格是否为同一套控件；
若拟合页另有独立的表格读取函数，需同步修改（落地时逐一核对）。

---

## 4. M3：参数识别逻辑区分 CPE

`EIS/FittingFile/FittingECM.py` 的 `_identify_circuit_params()` 按名字首字母把元件分成
电阻/电容/电感三类：

- `CPE1` 会被归为"电容"（对 smart_fitting 的初值策略有影响）；
- `alphaCPE1` 不会匹配任何类别，被忽略。

拟议改动：显式识别 `CPE` 前缀，单独的 `alpha` 前缀参数不参与元件分类。
影响面小，仅影响智能初值与可辨识性诊断的分类结果。

---

## 5. M4：`multi_start_fit` 通用化（可选）

`EIS/FittingFile/FittingECM_extreme.py` 的 `multi_start_fit()` 目前固定构造 3 个参数
（`R1` / `C3` / `R6`），因此**只支持 `R1 + p(C3, R6)` 这一种电路结构**；
4~6 参数的电路（双时间常数、CPE 组合）调用它会抛 `KeyError`。

本次两个验证脚本用的是脚本内的通用多起点版本（调用同一个 `FittingECM`，
只是在初值上做对数空间采样），思路与 `multi_start_fit` 一致。

可选改动：让 `multi_start_fit` 接受 `init_params` 并按其生成参数，
当 `init_params` 为 None 时保持现有 Randles 行为（向后兼容）。

优先级：**低**。GUI 的 smart_fitting / auto_fitting 已覆盖多数场景，
但论文若要宣传"多起点全局搜索适用于任意电路"，建议做。

---

## 6. M5：可复现性交付物（R4-M2 明确要求）

Reviewer 4: *"The corresponding datasets and model settings should be made available
to support reproducibility."*

拟议交付：

1. 把 `Impedance of yeast.xlsx`（三个浓度）复制到发布包的示例目录，
   建议位置：`EIS/input_impedance/yeast/`（或新建 `examples/validation/yeast_cell/`）。
2. 模型设置文件：`results_yeast/yeast_model_settings.json` 已由脚本生成，
   内含电路、初值、权重方式、优化器与随机种子、数据预处理步骤——建议随数据一起发布。
3. 一份 `README`（英文，因为用户手册是英文）说明复现步骤：
   导入数据 → 选择电路 → 填入初值 → 权重/频段 → 拟合 → 对照 `yeast_<tag>_fit.csv`。
4. 论文中给出仓库内的相对路径与文件名。

**待确认**：该数据源自 Ref. [13]，需确认是否允许再分发；
若不允许，则改为"数据与拟合脚本一并提供、引用 [13]"的表述。

---

## 7. 论文修改清单（对应审稿意见）

| 意见 | 需要的动作 | 数据来源 |
|---|---|---|
| R2-1 精度未定量评估 | 删除 "excellent accuracy"，改为具体指标 | `results_synthetic/synthetic_metrics.json` |
| R2-3 未点名 [13] 的方法 | 逐条核对代码中实际实现的方法后再写进 3.2 节 | 代码核对（见第 10 节待决事项 5） |
| R2-2 图号/错字 | 纯文稿修正 | — |
| R4-Major-1 缺复杂电路与定量验证 | 新增 Validation 小节：1 张参数表 + 2 张图 | `results_synthetic/*` |
| R4-Major-2 缺真实应用实例 | 新增 yeast cell 实例：参数表 + 拟合图 + 可复现说明 | `results_yeast/*` |
| R4-Minor 图注互换 | 纯文稿修正 | — |

### 7.1 建议的论文表述（可直接取用的数字）

**合成算例（1% 噪声，0.1 Hz–1 MHz，121 点）**

| 算例 | 最大参数误差 | 约化卡方 | 残差 RMS(相对) | 拟合模型 vs 真值模型 |
|---|---|---|---|---|
| 双时间常数 τ₂/τ₁ = 100 | 0.38 % | 8.3e-05 | 1.27 % | 0.25 % |
| 双时间常数 τ₂/τ₁ = 30 | 0.61 % | 8.4e-05 | 1.28 % | 0.25 % |
| 双时间常数 τ₂/τ₁ = 10 | 0.41 % | 8.1e-05 | 1.26 % | 0.24 % |
| 双时间常数 τ₂/τ₁ = 5 | 157 %（多解） | 9.1e-05 | 1.33 % | **0.81 %** |
| 双时间常数 τ₂/τ₁ = 3 | 146 %（多解） | 8.6e-05 | 1.30 % | **0.34 %** |
| CPE 元件（Q, n） | 4.02 %（Q）、0.44 %（n） | 8.2e-05 | 1.27 % | 0.29 % |
| CPE 支路 + RC 支路 | 96.6 %（多解） | 3.4e-04 | 2.58 % | **3.70 %** |
| 双时间常数，单起点（对照） | 2468 % | 8.3e-03 | 12.8 % | 28.2 % |

**这组数字要讲清楚三件事：**

1. 拟合得到的**阻抗响应**与真值模型一致（偏差 < 1%，CPE 组合算例 3.7%），
   说明拟合本身是准确的；
2. 参数在 τ₂/τ₁ ≥ 10 时可唯一回收（误差 < 0.7%），在 τ 比值更小时出现
   **等效电路分解的多解性**（参数互换但响应等价）——这是逆问题的固有性质，
   建议在论文中作为"适用范围与局限"明确写出；
3. 必须使用**多起点/智能初值**策略：单起点在同样的双时间常数算例上残差 RMS
   从 1.3% 劣化到 12.8%。

**yeast cell 实例**（1 MHz–3 GHz，剔除 |Z| < 10 Ω 的噪声底点）

| 数据集 | 模型 | 约化卡方 | 残差 RMS(相对) | 最大残差 |
|---|---|---|---|---|
| 10% Living | R1 + (CPE1‖R2) + (C2‖R3) | 8.5e-04 | 4.09 % | 19.6 % |
| 20% Living | 同上 | 1.2e-03 | 4.94 % | 20.0 % |
| 30% Living | 同上 | 1.7e-03 | 5.78 % | 22.8 % |

拟合得到的 CPE 指数 n ≈ 0.51–0.54（明显压扁的圆弧），R2 随浓度升高而下降
（10%: ~1150 Ω → 30%: ~330 Ω），与悬浮体系电导随细胞浓度升高而增大一致。
残差呈系统性（随频率缓慢变化），提示该体系的弛豫是**分布式**的——
这正是 AnyEIS 的 MT/DRT 模块的适用场景。

---

## 8. 建议新增的论文图表

- Table: 合成算例的参数回收表（真值/拟合/相对误差/卡方/残差 RMS）；
- Table: yeast cell 实例的拟合参数表（三个浓度，含标准误）；
- Figure: 双时间常数算例的 Nyquist + Bode + 残差三联图；
- Figure: 参数回收误差 vs τ₂/τ₁ 曲线；
- Figure: CPE 算例三联图；
- Figure: yeast cell 三个浓度的 Nyquist 叠加 + 参数随浓度变化；
- （可选）Figure: yeast cell 的 DRT 结果（见第 10 节待决事项 4）。

---

## 9. 备选方案 B：本次不修改产品

若不落地 M1/M2，则：

1. 论文**不得**声称软件支持 CPE；只保留 R/C 电路的验证结论；
2. 合成算例 2 / 3 与 yeast 的 CPE 模型只能标注为
   "engine-level validation using a test-only compatibility shim"，
   不作为产品功能主张（脚本里已有醒目注释）；
3. yeast 模型改用纯 R/C 的 M3：把 `FittingValidationYeast.py` 中的
   `ALLOW_CPE_MODELS` 设为 `False` 即可自动切换（对应指标：
   10%: χ² 6.6e-04 / RMS 3.6%；20%: χ² 1.2e-03 / RMS 4.9%；
   30%: χ² 1.6e-03 / RMS 5.7%），GUI 可原样复现；
4. 把 CPE 支持列入 roadmap / future work。

---

## 10. 需要你决定的事项

1. **是否实施 M1 + M2（引擎 + GUI 的 CPE 支持）？** 推荐：是。
   否则论文无法主张非理想元件，且 GUI 里选 CPE 会静默给出错误结果。
2. **是否实施 M3 / M4？** M3 建议做，M4 可选。
3. **yeast 数据是否随包发布？** 需确认 [13] 的授权范围。
4. **是否为 yeast 数据增加一张 DRT/MT 结果图？**
   `EIS/FittingFile/FittingMT.py` 已有多项（Debye/HN）拟合能力，无需改代码，
   但需要平行板电容器几何参数（d/A）才能把 Z 转成介电谱；该参数不在当前数据文件中。
5. **[13] 的方法核对**：论文 3.2 节要点名 [13] 的方法，需要逐条对照代码确认
   实际实现了哪些（建议产出一张"方法名 → 代码位置 → GUI 入口"映射表后再改文稿）。
6. **是否接受把"多解性"与"多起点策略"写成论文的局限与适用范围说明？**
   建议接受——审稿人读到自曝局限通常比被追问更好。

---

## 附：本次新增文件与运行方式

| 文件 | 作用 |
|---|---|
| `FittingValidationSynthetic.py` | 合成算例：双时间常数、CPE、CPE+RC 组合、τ 比值扫描、单起点对照 |
| `FittingValidationYeast.py` | 真实算例：yeast cell 三个浓度、模型选择、参数表、残差、导出与复现材料 |
| `CPE_SUPPORT_MODIFICATION_PLAN.md` | 本文件 |

运行（解释器：`C:\ProgramData\anaconda3\python.exe`）：

```
cd EIS/FittingFile/Funtest
python FittingValidationSynthetic.py     # 产物 -> results_synthetic/
python FittingValidationYeast.py         # 产物 -> results_yeast/
```

两个脚本都不修改任何已有源文件；CPE 通过运行时兼容层生效，
待第 10 节事项 1 批准后，可删除脚本中的兼容层，改由产品原生支持。
