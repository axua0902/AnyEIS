# AnyEIS 更新与问题跟踪

> **生成时间**: 2026-11-17
> **来源**: 由 `BUGS.md` 重组而来。历史条目的**详细分析过程**已全部归档至 git 历史
> （`BUGS.md` 提交记录 + 本文件早期版本），本文件只保留：当前活跃问题、已完成条目
> 的概要结论、待办清单与维护模板。
> **维护约定**: 已完成的条目只保留一句话结论 + 状态，不再复述现象/根因/逐行补丁/测试明细；
> 需要细节时用 `git log -p update.md` 查看历史版本。

---

## 一、当前活跃问题

> **2026-09-09**: Bug #007 Phase 1 + Phase 2 已修复（P0 × 1 + P1 × 2）。
> P0-2 多图合并按用户反馈回退为"只画第一组"。
> **2026-11-28**: P2 清理项复核并处理完毕（P2-2 判定为非问题，撤销）。

### 1.1 Bug #007 P2 清理项（2026-11-28 已处理）

| # | 内容 | 结论 | 状态 |
|---|------|------|------|
| P2-1 | `userdefine5` 中 `self.clearfigure()` 副作用（会重置 `excelnameTextEdit` 时间戳） | 两处改用 `_reset_figure_state(self)`，与 userdefine3/4 一致，不再覆盖用户填写的导出文件名 | ✅ 已修复 |
| P2-2 | `np.var/std` 用 `ddof=1` 而 `np.mean` 不指定 ddof 的语义注释 | `np.mean` 无 ddof 参数，`ddof=1` 为刻意的样本口径，注释已明确 → 非问题 | ✅ 撤销 |
| P2-3 | `selected_indices` 在 4 个函数中重复计算（可抽 helper） | `Error_stat.py` 抽出 `_selected_indices()`（3 处）；`UserDefineFun.py` 抽出 `_synthetic_selection()` 并让 `_iter_processed_synthetic()` 复用，消除第 4 处重复 | ✅ 已修复 |

### 1.2 审稿回复相关事项

CPE 支持、定量评估与可复现性材料（含 C7/P8 模型 JSON 拟合设置）均已实施并回归通过，
无未跟踪事项，实施记录见 §2.4 ~ §2.6。

---

## 二、已完成条目概要

> 详细过程见 git 历史（`BUGS.md` 提交记录 / `update.md` 早期版本）。

### 2.1 Bug 系列

| ID | 标题 | 结论 | 状态 |
|----|------|------|------|
| Bug #001 | Filter/Processing "处理后数据全部相同" | 成对化协议修正 | ✅ 已修复 |
| Bug #002 | Dielectric Material UI 锁 Air+Water | 修复 | ✅ 已修复 |
| Bug #003 | Dielectric Material UI 取消 Alcohol | 修复 | ✅ 已修复 |
| Bug #004 | Simulation/Fitting Tab 切换未联动 figure 数据类型 | 修正下拉框字符串并补 `currentChanged` 联动 | ✅ 已修复 |
| Bug #005 | 计算行 Clear 按钮孤立 / 槽实现不一致 | 拆为 `clearECCalculation` / `clearMTCalculation`（B-1 语义），connect `tab2.clearBtn` | ✅ 已修复 |
| Bug #005b | Clear 误清 Fixed 列 / Simulation 6 列错位 | 清空列收敛为 `(3, 7)`，Simulation 路径不动表 | ✅ 已修复 |
| Bug #006 | 表格列与算法匹配（4 阶段） | EC/MT 表头对称化；删除 Fixed 死列；Error [%] 无 stderr 时显示 `N/A`；simu 模式仅留 3 列 | ✅ 已修复 |
| Bug #007 | 数据统计与误差计算函数 | 补 synthetic 过滤（跳过 original 配对）；多组误差只画第一组；列对齐改按列名匹配；dtype 检查改用 `is_numeric_dtype` | ✅ Phase 1+2 已修复 |

### 2.2 TP 系列 — Processingfun.py 理论问题（已全部决策）

| ID | 函数 | 一句话 | 状态 |
|----|------|--------|------|
| TP-001 | `paraplate` | 缺 `jωε₀` 因子，ε 量纲错误 | ✅ 已修复 |
| TP-002 | `DieMat` | 硬编码 `L=0, R=0`，高频段误差 | ✅ 复审撤销（高频请用 TL） |
| TP-003 | `DieMat` | omega 来自 `refdata[0]` | ✅ 已完整修复 |
| TP-004 | `threesolutions` | 用 Z 插值而非 Y/C | 🟢 降为低优先级（差异 < 0.0001%） |
| TP-005 | `TLcalibrate` | 传播常数硬编码 `Calsigma=0` | ✅ 已修复 |
| TP-006 | `TLcalibrate` | 大 γ·l 下 `tanh`/`arctanh` 数值不稳 | ✅ 已修复（np.clip + NaN 哨兵） |
| TP-007 | `TLcalculateEPS` | 单点实数初值极端样品不收敛 | ✅ 已修复（双初值策略） |
| TP-008 | `paraplate` | σ 公式"缺 σ_dc"误读 | ✅ 公式确认正确（仅待文档化） |
| TP-009 | `DieMat` | C0/Cr 公式符号错误 | ✅ 已修复 |
| TP-010 | `DieMat` | 错误处理静默返回 `None` | ⏸️ 不修复（GUI 已校验） |
| TP-011 | `DieMat` / `DieMatPark` | 符号体系不一致 | ✅ 已解决 |
| TP-012 | `DieMat` | 局部变量未使用 | ⏸️ 不修复 |
| TP-013 | `DieMat` | 缺少输入参数防御性校验 | ⏸️ 不修复 |
| TP-014 | `check6_freq_consistency` | 未导入导致 NameError | ✅ 已修复 |
| TP-015 | `TLcalculateEIS` | 硬编码列名 `KeyError` | ✅ 已修复（`_resolve_col` 兜底） |
| TP-016 | `DieMat` | 新增 ε'' 显式输出 | ✅ 已实现 |
| TP-017 | RF 三方法 note | 缺方法功能说明 | ✅ 已补充 |
| TP-018 | `ui_ThreeSolution` / `ui_TransmissionLine` | 浓度未联动 ref 液类型 | ✅ 已修复 |

### 2.3 MT 系列 — 项目维护与一致性（全部完成）

| ID | 范围 | 一句话 | 状态 |
|----|------|--------|------|
| MT-001 | 协议声明 | 许可证 MIT → Apache 2.0（README + UI 信息） | ✅ 已完成 |
| MT-002 | UI 元数据 | 版权年份 / 发布日期更新 | ✅ 已完成 |
| MT-003 | 依赖版本 | UI/文档依赖列表与 `requirements.txt` 三位小数对齐 | ✅ 已完成 |
| MT-004 | 用户偏好 | 默认导出文件名 → `User_preferences.json` | ✅ 已完成 |
| MT-005 | 依赖清单 | 补充 `openpyxl` 声明 | ✅ 已完成 |
| MT-006 | Qt 框架 | 残留 `PyQt5` → `PySide6`，`app.exec_()` → `app.exec()` | ✅ 已完成 |

### 2.4 CPE 支持落地（2026-09 ~ 2026-11）

| 阶段 | 内容 | 状态 |
|------|------|------|
| P1 / P4 | 引擎 `elementsZ` / `expressZ` 支持 CPE 元件 | ✅ 已完成 |
| P2 / P6 | `addelement` 写入 `CPE1`(Q) 与 `alphaCPE1`(n) 两行及备注 | ✅ 已完成 |
| P3 | 撤销操作同步删除 n 行 | ✅ 已完成 |
| P5 | `Fitting.py` 中 n 的 (0.5, 1.0] 兜底 | ✅ 已完成 |
| P7 | 电路图 CPE 图元（箭头穿过的电容） | ✅ 已完成 |
| 回归 | 纯 R/C/L 算例逐位一致；CPE(Q,1) 与理想电容一致 | ✅ 通过 |
| 验证脚本 | 改为固定种子（42–49）差分进化 + LM 精修，删除运行时兼容层 | ✅ 已完成 |

### 2.5 审稿回复与测试资产（2026-11）

| 项 | 内容 | 状态 |
|---|------|------|
| 定量评估 | 合成算例（含 τ 扫描）、与 impedance.py 交叉校验、酵母实验算例 | ✅ 完成 |
| 回复稿 | `EIS/FittingFile/test/Response_to_Reviewers_R2_accuracy_and_R4_validation.md` | ✅ 完成 |
| 交叉校验脚本 | `EIS/FittingFile/test/ReferenceCrosscheck.py` | ✅ 完成 |
| 验证脚本 | `FittingValidationSynthetic.py` / `FittingValidationYeast.py` | ✅ 完成 |
| 测试资产 | `TestData/Fitting/ECM/` 下 `ECM_DualRC`、`ECM_CPE`、`ECM_DualRC_CPE`、`Impedance of yeast`（含 json + xlsx） | ✅ 完成 |

> 拟合口径（已定稿，后续不得更改）：固定随机种子（42–49）的差分进化全局搜索 +
> Levenberg–Marquardt 局部精修，残差函数用产品引擎 `fcn2min`。
> 默认 `least_squares` 局部路径（`diff_step=1e-15` + `tr_solver='lsmr'`）数值脆弱，
> 不可用于需要可复现数字的场合。

### 2.6 模型 JSON 追加拟合设置（C7 / P8，服务 R4-M2 可复现性）

**目标**：审稿人要求 "The corresponding datasets and **model settings** should be made
available to support reproducibility"。原模型 JSON 只有电路串与参数（已含 `alphaCPE1`），
缺优化器及其参数、损失函数、数据集名 → 用户存一次模型即应得到完整可发布的 model settings。

| 项 | 内容 |
|---|---|
| 改动位置 | `EIS/ModelFile/ECMFunctions.py` → `create_ecm_model_json`（+约 25 行，**仅存盘侧**） |
| 调用链 | `Fitting.saveECMModel / saveasECMModel` → `_save_ecm_model_to_file` → `create_ecm_model_json(self)`（`obj` 即 `Fitting` 实例） |
| 新增键 | `fitting_settings`：`method` / `parameters` / `loss` / `loss_policy` / `datasets` / `dataset_count` |
| 取值来源 | `obj.setting_widget.get_settings()`（优化器及其参数，**文本原样**，与 `Fitting._cast_setting()` 保持单一转换入口）+ `obj.original_prodataname`（拟合实际使用的 N 条数据集名） |
| 兜底 | `getattr(obj,'setting_widget',None)` → `getattr(sw,'get_settings',None)` → `try/except`；无设置面板时落 `least_squares` 默认值，不抛异常 |
| loss 口径 | 引擎按噪声自动选择（`FittingECM._auto_select_loss`：`<0.001→linear`、`>0.10→huber`、其余 `soft_l1`），DE/DA/AMPGO 不用 loss → 记 `"auto"` + `loss_policy`，**不写死 `soft_l1`** |
| 兼容性 | 旧 JSON（无该键）载入不受影响：加载端按固定键取值，多余键被忽略；`version` 保持 `"1.0"` |
| 验证 | 仓库内 19 个 ECM JSON 全覆盖：旧 JSON 载入 19/19 通过；新旧载入结果逐字段一致；roundtrip 正常；无 `setting_widget` 与 `get_settings()` 抛异常两条兜底路径均正常 |
| 未纳入 | 数据集文件绝对路径拿不到（上游 `dataInfo` 始终为空）→ 只记名字；`load_ecm_model_to_ui` 侧未改动；`newECMModel` 生成的仍是"旧格式"文件（无该键） |

实施代码（`create_ecm_model_json` 中 `model_data` 之前）：

```python
    # --- 拟合设置（服务 R4-M2 可复现性）---
    fitting_settings = {
        'method': 'least_squares',
        'parameters': {},
        'loss': 'auto',
        'loss_policy': ('least_squares 时由引擎按噪声水平自动选择 loss '
                        '(<0.001->linear, >0.10->huber, 其余->soft_l1); '
                        'differential_evolution/dual_annealing/ampgo 不使用 loss'),
        'datasets': list(getattr(obj, 'original_prodataname', []) or []),
        'dataset_count': len(getattr(obj, 'original_prodataname', []) or []),
    }
    sw = getattr(obj, 'setting_widget', None)
    getter = getattr(sw, 'get_settings', None) if sw is not None else None
    if callable(getter):
        try:
            _s = getter()                      # {'method': ..., <参数名>: <文本>}
            fitting_settings['method'] = _s.get('method') or 'least_squares'
            fitting_settings['parameters'] = {k: v for k, v in _s.items() if k != 'method'}
        except Exception as e:
            print(f"[create_ecm_model_json] 读取拟合设置失败: {e}")
```

并在 `model_data` 字面量末尾追加：`"parameters": [], "fitting_settings": fitting_settings`（键数 8 → 9）。

### 2.7 数据读取与列语义修复（2026-11-28）

| 项 | 内容 | 状态 |
|----|------|------|
| PHASE 单位自检 | `Datacheck.check7_phase_unit`：以 `arctan2(X,Rs)` 为基准判定度/弧度，弧度自动 ×180/π；接入 `readexcelfile` / `readcsvfile` | ✅ 已完成 |
| PHASE 数据修正 | `TestData` 下 4 个水溶液 xlsx 的 `PHASE[deg]` 列 ×180/π（0.05 两份 + 0.01 + 0.5） | ✅ 已完成 |
| Z 列口径统一 | `Z[ohm]` 统一为幅值：`simulateECM` / `FittingECM` / `Filterfun` 的 `real(Z)`→`absolute(Z)`；`Plotfun.plotRs` 取列 `colname[1]`→`colname[3]`(Rs) | ✅ 已完成 |
| Z 一致性自检 | 新增 `Datacheck.check8_z_consistency`：比较 Z 更接近幅值 `hypot(Rs,X)` 还是实部 Rs 的行占比，只告警不改数据 | ✅ 已完成 |
| Z 数据修正 | `TestData/Fitting/ECM` 下 5 个 ECM xlsx 的 `Z[ohm]` 改为 `hypot(Rs,X)` | ✅ 已完成 |
| 一般数据列名 | `readexcelfile`：无频率列时视为一般数据、不重命名（如 `Foamat 4.xlsx`）；EIS/DS 按物理列位置重命名并规整为标准列序 | ✅ 已完成 |
| CSV 列名匹配 | `readcsvfile`：子串匹配改为规范化精确匹配，缺列打印告警而非 `NameError` | ✅ 已完成 |
| 鲁棒判据 | check7 改用中位比值 + 容差内行占比；check8 改用行占比；单行坏点不再阻断换算或误报（`RC2k...csv` 可正确换算） | ✅ 已完成 |
| 回归 | `test_check7_phase_unit.py` 12/12；MT smoke 通过；`TestData` 全量 check7/check8 零告警 | ✅ 通过 |

> 未处理（按要求保持原样）：`Data/` 下旧副本仍存在 PHASE 弧度 / `Z=Rs`，加载时由 check7 自动换算、check8 告警，不改动文件本身。

### 2.8 一般/时间序列绘图轴名与测试数据（2026-11-28）

| 项 | 内容 | 状态 |
|----|------|------|
| 列名传递 | `EIS/FigureFile/Figurefun.py` → `creatanyfile`：`dataInfo` 增加 `headings` 保存实际列名 | ✅ 已完成 |
| Excel 导出图 | `EIS/FigureFile/OtherFigurefun.py` → `Generalfiguremaker` / `TIMEfiguremaker`：X 轴取 `headings[0]`、各 Y 轴取对应列名，替代硬编码 `X`/`Y{i}`、`Time`/`Data{i}`；无表头时保留原兜底 | ✅ 已完成 |
| 应用内绘图 | `EIS/FigureFile/Plotfun.py` → `_plot_normal_single`：轴名取 `colname[0]` / `colname[col_index]`，多数据集同图取首个可用表头 | ✅ 已完成 |
| 测试数据 | `TestData/Input/input_normal` 新增 4 个 General xlsx（浓度 / 温度 / I-V / SoC）；`TestData/Input/input_time order` 新增 4 个 Time order xlsx（阻抗监测 / OCP 漂移 / 温度循环 / 计时电流） | ✅ 已完成 |
| 验证 | `readfile` 读取 8 个新文件全部成功；导出图 chart XML 轴名与 `plotNormal` 轴名均为真实表头 | ✅ 通过 |

---

## 三、新问题记录模板

```markdown
## [ID] — <一句话描述>

### 1. 现象
<用户看到什么 / 报错信息 / 复现步骤>

### 2. 涉及文件
- `<文件路径>` — `<方法名 / 行号>`

### 3. 根因分析
<数据结构 / 错误代码 / 问题分析>

### 4. 修复方案
<代码修改前 → 修改后>

### 5. 验证
<单元测试 / 人工步骤 / 修复前 vs 修复后输出>

### 6. 状态
🔴 待修复 | 🟡 进行中 | ✅ 已修复 | ⏸️ 不修复 | 🟢 复审撤销
```

> 记录时请**先写结论**：已完成条目只需一句结论 + 状态 + 关键文件位置；
> 详细分析过程统一进 git 历史，不在本文档堆积。

---

## 四、归档摘要

历史条目汇总：Bug 系列 8 条（7 已修复 + Bug #007 Phase 1/2 已修复）、TP 系列 18 条
（13 已修复 / 2 已解决 / 2 复审撤销或降级 / 3 不修复）、MT 系列 6 条（全部完成）。
另：2026-11-28 数据读取与列语义系列 9 项已完成（详见 §2.7）；
2026-11-28 一般/时间序列绘图轴名与测试数据系列 1 项已完成（详见 §2.8）；
2026-11-28 Bug #007 P2 清理项 3 项已处理（详见 §1.1）。
**无未决缺陷。**

---

## 五、修改时间线

| 日期 | 轮次 | 范围 | 关键改动 |
|------|------|------|----------|
| 2026-08-26 | — | 数据成对化协议 | 12 个文件，引入 `ensure_paired_form` + 配对检测 |
| 2026-08-31 | — | `paraplate` / `TLcalibrate` 公式 | TP-001, TP-005 修复 |
| 2026-09-02 | — | 复审 / 数值稳定性 | TP-002、TP-008 复审撤销；TP-006 修复 |
| 2026-09-03 | R1 | `DieMat` 函数 | TP-009, TP-011, TP-016 修复 |
| 2026-09-04 | R2 | RF 系列 + UI 联动 | TP-014, TP-015, TP-017, TP-018 修复 |
| 2026-09-05 | — | 文档重组 / MT 系列 | BUGS.md → update.md；MT-001 ~ MT-006 全部完成 |
| 2026-09-06 | Bug #004/5/5b/6 | Tab 联动、Clear 按钮、表格列 | 详见 §2.1 概要 |
| 2026-09-09 | Bug #007 | 数据统计与误差计算 | 详见 §2.1 概要 |
| 2026-09 ~ 2026-11 | CPE | 引擎 + GUI + 电路图 CPE 支持，回归通过 | 详见 §2.4 |
| 2026-11 | 审稿回复 | 定量评估、交叉校验、酵母实验算例、回复稿与测试资产 | 详见 §2.5 |
| 2026-11-17 | 文档整理 | 压缩已完成条目细节，补充 CPE / 审稿实施记录与时间线 | |
| 2026-11-17 | R4 | 模型 JSON 追加 `fitting_settings`（`ECMFunctions.create_ecm_model_json`），旧 JSON 兼容性回归通过 | 详见 §2.6 |
| 2026-11-28 | 数据读取 | PHASE 单位自检与数据修正、Z 列口径统一、一般数据列名、CSV 精确匹配、check7/8 鲁棒化 | 详见 §2.7 |
| 2026-11-28 | 绘图 | General/Time order 导出图与应用内绘图轴名改用文件实际表头；新增 8 个一般/时间序列测试数据 | 详见 §2.8 |
| 2026-11-28 | Bug #007 P2 | 误差计算改用 `_reset_figure_state`；抽出 `_selected_indices` / `_synthetic_selection`；P2-2 撤销 | 详见 §1.1 |

---

## 六、文档结束

> 当前文件用于持续跟踪。历史 bug 详情请通过 `git log -p update.md` 与 `BUGS.md` 提交记录访问。
