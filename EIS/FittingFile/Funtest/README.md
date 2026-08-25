# Funtest/ 测试文件夹

> **EIS 拟合模块测试与诊断文件集**
> 主程序位置: `../FittingFile/Fitting*.py`
> 整理日期: 2026-08-25

---

## 📁 文件夹结构

```
Funtest/
├── README.md                                    # 本文件
│
├── ── ECM 等效电路测试（5 个）──
├── FittingfuntestECM.py                         # 复杂电路与极限条件单元测试
├── FittingfuntestECM2.py                        # 极端条件与策略验证测试
├── FittingTest.py                               # ECMcalculation smoke test
├── test_all_methods.py                          # 全方法综合回归测试
├── test_4circuits_method_diagnosis.py           # 4 电路 × 10 算法 × 2 边界诊断
├── test_multi_algorithm_4circuits.py            # 4 电路 × 10 算法多算法对比
│
├── ── MT 介电模型测试（1 个）──
├── FittingfuntestMT.py                          # FittingMT 介电 / 多弛豫测试
│
└── ── report/ 报告目录（4 个）──
    ├── EIS_Fitting_Analysis_Summary.md          # 历史经验总结
    ├── FittingMT_Test_Report.md                 # MT 测试报告
    ├── test_4circuits_method_diagnosis_report.md # 4 电路诊断报告（含 P0/P1 实施后数据）
    └── test_multi_algorithm_4circuits_report.md  # 4 电路多算法对比报告
```

**说明**：
- 顶层 7 个 `.py` 文件：均为可用测试脚本，**无 DEPRECATED 警告**
- `report/` 子目录：所有 `*_report.md` 和 `*_Test_Report.md` 文件统一存放
- **所有测试脚本均规范化头注释**：测试目标 / 测试类型 / 运行方式

---

## 🧪 顶层测试脚本（7 个，全部可用）

### ECM 等效电路测试（6 个）

#### 1. `FittingfuntestECM.py` — 复杂电路与极限条件单元测试

| 项目 | 内容 |
|------|------|
| **测试目标** | [FittingECM.py](../FittingECM.py) |
| **测试类型** | 单元测试（复杂混合串并联 + 极限条件） |
| **测试方法** | 10 个方法（已添加 `method` 参数） |
| **运行时间** | 约 2-3 分钟 |

**测试内容**：
- 复杂混合串并联电路（元件数 > 3）
- 多并联分支电路（已知会失败）
- 参数量级悬殊电路（mΩ ~ MΩ）
- 宽频率跨度电路（> 8 数量级）
- 高噪声环境下的拟合

**运行方式**：
```bash
python EIS/FittingFile/Funtest/FittingfuntestECM.py
```

---

#### 2. `FittingfuntestECM2.py` — 极端条件与策略验证测试

| 项目 | 内容 |
|------|------|
| **测试目标** | [FittingECM.py](../FittingECM.py) + [FittingECM_extreme.py](../FittingECM_extreme.py) |
| **测试类型** | 单元测试（策略选择和决策函数验证） |
| **运行时间** | 约 1-2 分钟 |

**测试内容**：
- 决策函数验证（should_use_segmented, should_use_extreme）
- 参数可辨识性检查（check_parameter_identifiability）
- 自适应分段策略（adaptive_segmentation）
- 极端拟合策略的边界条件

**运行方式**：
```bash
python EIS/FittingFile/Funtest/FittingfuntestECM2.py
```

---

#### 3. `FittingTest.py` — ECMcalculation Smoke Test

| 项目 | 内容 |
|------|------|
| **测试目标** | [FittingECM.py](../FittingECM.py) 中的 `ECMcalculation` |
| **测试类型** | 单次 smoke test（基础流程 + ampgo 兼容性） |
| **运行时间** | 约 5-10 秒 |

**运行方式**：
```bash
python EIS/FittingFile/Funtest/FittingTest.py
```

---

#### 4. `test_all_methods.py` — 全方法综合回归测试

| 项目 | 内容 |
|------|------|
| **测试目标** | [FittingECM.py](../FittingECM.py) `_auto_fitting_core` |
| **测试类型** | 综合回归测试（7 测试组） |
| **测试方法** | 10 个优化方法 |
| **运行时间** | 约 3-5 分钟（`--quick` 模式约 1 分钟） |

**7 组测试内容**：
1. 参数类型转换（type casting）
2. 方法 smoke test
3. UI 流程（文本框 → kwargs）
4. 决策函数（should_use_segmented / should_use_extreme）
5. 极端条件测试
6. MT 路径
7. 噪声对比

**运行方式**：
```bash
# 完整 7 组
python EIS/FittingFile/Funtest/test_all_methods.py

# 只跑主流程
python EIS/FittingFile/Funtest/test_all_methods.py --quick

# 只测一个方法
python EIS/FittingFile/Funtest/test_all_methods.py --method lbfgsb
```

---

#### 5. `test_4circuits_method_diagnosis.py` — 4 电路 × 10 算法 × 2 边界诊断

| 项目 | 内容 |
|------|------|
| **测试目标** | [FittingECM.py](../FittingECM.py) `auto_fitting` |
| **测试类型** | 多算法 × 多电路 × 多边界策略 对比测试 |
| **测试方法** | 10 个方法 × 4 个电路 × 2 套边界 = 80 组合 |
| **运行时间** | 约 10-15 分钟 |

**4 个测试电路**：
1. **C1 Randles 基准** — R1 + p(C3, R6)
2. **C2 双并联多解** — R1 + p(C1, R2) + p(C3, R4)
3. **C3 4 元件树状** — R1 + p(C1, R2) + R3
4. **C4 极限量级差** — R1=1mΩ + p(C3, R6=1MΩ)

**2 个边界阶段**：
- 阶段 A: 宽边界 [1e-15, 1e15]
- 阶段 B: 紧边界 [init/100, init*100]

**运行方式**：
```bash
python EIS/FittingFile/Funtest/test_4circuits_method_diagnosis.py
```

**报告**：[report/test_4circuits_method_diagnosis_report.md](report/test_4circuits_method_diagnosis_report.md)

---

#### 6. `test_multi_algorithm_4circuits.py` — 4 电路 × 10 算法多算法对比

| 项目 | 内容 |
|------|------|
| **测试目标** | [FittingECM.py](../FittingECM.py) `auto_fitting` |
| **测试类型** | 多算法 × 多电路 对比测试（单边界） |
| **测试方法** | 10 个方法 × 4 个电路 = 40 组合 |
| **运行时间** | 约 5-8 分钟 |

**与 `test_4circuits_method_diagnosis.py` 的区别**：
- 本文件只测试单套边界（宽边界）
- `test_4circuits_method_diagnosis.py` 增加了 2 套边界策略对比
- 本文件的报告是初始版

**运行方式**：
```bash
python EIS/FittingFile/Funtest/test_multi_algorithm_4circuits.py
```

**报告**：[report/test_multi_algorithm_4circuits_report.md](report/test_multi_algorithm_4circuits_report.md)

---

### MT 介电模型测试（1 个）

#### 7. `FittingfuntestMT.py` — FittingMT 介电 / 多弛豫测试

| 项目 | 内容 |
|------|------|
| **测试目标** | [FittingMT.py](../FittingMT.py) |
| **测试类型** | 单元测试（介电 / 多弛豫模型） |
| **运行时间** | 约 1-2 分钟 |

**测试内容**：
1. 基础功能测试：fittingmodel, fcn2min, creatdatabase
2. 标准拟合测试：FittingMT (双弛豫模型)
3. 自动拟合测试：FittingMT_auto (各种场景)
4. 不同模型类型测试：Debye, Cole-Cole, Davidson-Cole, Havriliak-Negami
5. 多参数场景测试：单、双、三弛豫
6. 结果可视化

**运行方式**：
```bash
python EIS/FittingFile/Funtest/FittingfuntestMT.py
```

---

## 📊 report/ 报告目录（4 个文件）

| 文件 | 说明 | 生成源 | 大小 |
|------|------|--------|------|
| [report/EIS_Fitting_Analysis_Summary.md](report/EIS_Fitting_Analysis_Summary.md) | 历史经验总结（参考文档） | 长期积累 | 30 KB |
| [report/FittingMT_Test_Report.md](report/FittingMT_Test_Report.md) | MT 测试报告 | 2026-06-04 一次性输出 | 10 KB |
| [report/test_4circuits_method_diagnosis_report.md](report/test_4circuits_method_diagnosis_report.md) | 4 电路诊断报告（含 P0/P1 实施后数据） | `test_4circuits_method_diagnosis.py` | 28 KB |
| [report/test_multi_algorithm_4circuits_report.md](report/test_multi_algorithm_4circuits_report.md) | 4 电路多算法对比报告（旧版） | `test_multi_algorithm_4circuits.py` | 16 KB |

**报告存放规则**：
- 所有 `*_report.md` 文件保存在 `report/` 子目录
- 所有 `*_Test_Report.md` 文件保存在 `report/` 子目录
- 测试脚本通过 `os.path.join(..., 'report', '...')` 自动写入此目录

---

## 🔗 文件映射表（测试 → 主程序）

| 测试文件 | 主程序 | 类型 |
|---------|--------|------|
| `FittingfuntestECM.py` | [FittingECM.py](../FittingECM.py) | 复杂电路单元测试 |
| `FittingfuntestECM2.py` | [FittingECM.py](../FittingECM.py) + [FittingECM_extreme.py](../FittingECM_extreme.py) | 策略验证单元测试 |
| `FittingTest.py` | [FittingECM.py](../FittingECM.py) | Smoke test |
| `test_all_methods.py` | [FittingECM.py](../FittingECM.py) | 综合回归测试 |
| `test_4circuits_method_diagnosis.py` | [FittingECM.py](../FittingECM.py) | 多算法 × 多电路诊断 |
| `test_multi_algorithm_4circuits.py` | [FittingECM.py](../FittingECM.py) | 多算法 × 多电路对比 |
| `FittingfuntestMT.py` | [FittingMT.py](../FittingMT.py) | 介电 / 多弛豫测试 |

---

## 📋 测试推荐流程

| 场景 | 运行命令 | 耗时 |
|------|---------|------|
| **日常回归** | `python EIS/FittingFile/Funtest/test_all_methods.py --quick` | ~1 分钟 |
| **完整回归** | `python EIS/FittingFile/Funtest/test_all_methods.py` | ~5 分钟 |
| **算法对比诊断（含 P0/P1 数据）** | `python EIS/FittingFile/Funtest/test_4circuits_method_diagnosis.py` | ~15 分钟 |
| **多算法对比（旧版）** | `python EIS/FittingFile/Funtest/test_multi_algorithm_4circuits.py` | ~8 分钟 |
| **复杂电路 / 极限条件** | `python EIS/FittingFile/Funtest/FittingfuntestECM.py` | ~3 分钟 |
| **策略选择验证** | `python EIS/FittingFile/Funtest/FittingfuntestECM2.py` | ~2 分钟 |
| **介电模型** | `python EIS/FittingFile/Funtest/FittingfuntestMT.py` | ~2 分钟 |
| **Smoke test** | `python EIS/FittingFile/Funtest/FittingTest.py` | ~10 秒 |
| **单方法调试** | `python EIS/FittingFile/Funtest/test_all_methods.py --method differential_evolution` | ~30 秒 |

---

## 📊 当前测试状态（2026-08-25）

| 测试 | 通过率 | 备注 |
|------|--------|------|
| `test_all_methods.py --quick` | ✅ 7/7 | 综合回归 |
| `FittingfuntestECM.py` | ✅ 10/10 | 复杂电路单元测试 |
| `FittingfuntestECM2.py` | ✅ 8/8 | 策略验证单元测试 |
| `test_4circuits_method_diagnosis.py` | ✅ 80/80 | 实施 P0/P1 后全部完成 |

**P0/P1 实施记录**（在 [FittingECM.py](../FittingECM.py) 中）：
- ✅ P0-① 自适应边界（`_compute_adaptive_bounds`）
- ✅ P0-② 局部方法保留原边界
- ✅ P1 多起点 + R1_est 物理约束（`_multi_start_with_R1_constraint`）

---

## 📝 规范化要点（2026-08-25）

所有 7 个测试脚本已按以下统一格式规范化头注释：

```python
# -*- coding: utf-8 -*-
"""
<文件标题>

测试目标: <主程序文件>
测试类型: <单元测试/综合测试/诊断测试>

<测试内容说明>

运行方式:
    python EIS/FittingFile/Funtest/<文件名>

Created on <日期>
@author: takeilab
Updated on <日期>: <更新说明>
"""
```

**主要变化**：
- ✅ 移除了所有 `DEPRECATED` 警告
- ✅ 统一添加 `测试目标` / `测试类型` / `运行方式` 字段
- ✅ 所有 `*_report.md` 移入 `report/` 子目录
- ✅ 测试脚本的报告输出路径同步更新到 `report/`
- ✅ 创建本 `README.md` 反映当前结构

---

*整理人：MiniMax-M3*
*整理日期：2026-08-25（最终规范化版）*
