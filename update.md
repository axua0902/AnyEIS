# AnyEIS 更新与问题跟踪

> **生成时间**: 2026-09-05
> **来源**: 由 `BUGS.md` 重组而来,所有已修复 / 不修复 / 复审撤销的条目已归档至 git 历史,本文件仅保留当前活跃问题与新发现。
> **归档索引**: 历史条目见 `BUGS.md` 提交记录(汇总 18 条均已决策)。

---

## 一、当前活跃问题

> 暂无未决问题。发现新问题时请复制下方模板追加。

| ID | 模块 | 严重度 | 现象 | 状态 |
|----|------|--------|------|------|
| — | — | — | — | — |

---

> **本次维护记录(2026-09-05 会话)**: 已确认当前文档结构与历史归档一致,本次会话未发现新问题;所有 TP 系列与 Bug 系列条目状态保持上一归档汇总(13 已修复 / 2 已解决 / 2 复审或降级 / 3 不修复)。如后续维护中发现新缺陷,请按下方模板追加。

---

## 二、新问题记录模板

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

---

## 三、归档摘要(历史总览,详见 `BUGS.md` git 历史)

### Bug 系列(已全部处理)

| ID | 标题 | 状态 |
|----|------|------|
| Bug #001 | Filter/Processing "处理后数据全部相同" | ✅ 已修复 |
| Bug #002 | Dielectric Material UI 锁 Air+Water | ✅ 已修复 |
| Bug #003 | Dielectric Material UI 取消 Alcohol | ✅ 已修复 |

### TP 系列 — Processingfun.py 理论问题(已全部决策)

| ID | 函数 | 严重度 | 一句话 | 状态 |
|----|------|--------|--------|------|
| TP-001 | `paraplate` | 🔴 严重 | 缺 `jωε₀` 因子,ε 量纲错误 | ✅ 已修复 |
| TP-002 | `DieMat` | 🟢 模型边界 | 硬编码 `L=0, R=0`,高频段误差 | ✅ 复审撤销(高频请用 TL) |
| TP-003 | `DieMat` | 🟡 中等 | omega 来自 `refdata[0]` | ✅ 已完整修复 |
| TP-004 | `threesolutions` | 🟠 较严重 | 用 Z 插值而非 Y/C | 🟢 降为低优先级(差异 < 0.0001%) |
| TP-005 | `TLcalibrate` | 🟠 较严重 | 传播常数硬编码 `Calsigma=0` | ✅ 已修复 |
| TP-006 | `TLcalibrate` | 🟡 中等 | 大 γ·l 下 `tanh`/`arctanh` 数值不稳 | ✅ 已修复(np.clip + NaN 哨兵) |
| TP-007 | `TLcalculateEPS` | 🟡 中等 | 单点实数初值 30 极端样品不收敛 | ✅ 已修复(双初值策略) |
| TP-008 | `paraplate` | 🟡 轻微 | σ 公式"缺 σ_dc"误读 | ✅ 公式确认正确(仅待文档化) |
| TP-009 | `DieMat` | 🔴 严重 | C0/Cr 公式符号错误 | ✅ 已修复(2026-09-03) |
| TP-010 | `DieMat` | 🔴 严重 | 错误处理静默返回 `None` | ⏸️ 不修复(GUI 已校验) |
| TP-011 | `DieMat` / `DieMatPark` | 🟡 中等 | 符号体系不一致 | ✅ 已解决(随 TP-009 + TP-016) |
| TP-012 | `DieMat` | 🟢 轻微 | 局部变量未使用 | ⏸️ 不修复(不影响功能) |
| TP-013 | `DieMat` | 🟢 轻微 | 缺少输入参数防御性校验 | ⏸️ 不修复(GUI 已校验) |
| TP-014 | `check6_freq_consistency` 导入 | 🔴 严重 | 未导入导致 NameError | ✅ 已修复(2026-09-04) |
| TP-015 | `TLcalculateEIS` | 🟡 中等 | 硬编码列名 `KeyError` | ✅ 已修复(`_resolve_col` 兜底) |
| TP-016 | `DieMat` | 🟢 新增 | 新增 ε'' 显式输出 | ✅ 已实现(2026-09-03) |
| TP-017 | RF 三方法 note | 🟢 轻微 | 缺方法功能说明 | ✅ 已补充(ℹ 行) |
| TP-018 | `ui_ThreeSolution` / `ui_TransmissionLine` | 🟡 中等 | 浓度未联动 ref 液类型 | ✅ 已修复(`_apply_ref_solution_rules`) |

### MT 系列 — 项目维护与一致性(2026-09-05 会话)

| ID | 范围 | 严重度 | 一句话 | 状态 |
|----|------|--------|--------|------|
| MT-001 | 协议声明 | 🟡 中等 | `README.md` + UI 信息中许可证从 MIT 改为 Apache 2.0 | ✅ 已完成 |
| MT-002 | UI 元数据 | 🟢 轻微 | `ui_left_setting.py` `about_info` 版权年份与发布日期更新 | ✅ 已完成 |
| MT-003 | 依赖版本 | 🟡 中等 | UI/文档依赖列表与 `requirements.txt` 精度对齐(三位小数) | ✅ 已完成 |
| MT-004 | 用户偏好 | 🟡 中等 | 默认导出文件名由 `AnyEIS_preferences.json` 改为 `User_preferences.json` | ✅ 已完成 |
| MT-005 | 依赖清单 | 🔴 严重 | 主程序运行时使用 `openpyxl` 读取 xlsx,但 `requirements.txt` 未声明 | ✅ 已补充 |
| MT-006 | Qt 框架 | 🟡 中等 | 测试代码残留 `PyQt5` 引用,迁移至 `PySide6`(含 `app.exec()` 语法) | ✅ 已完成 |

**MT 详情**：

- **MT-001** — 修改 `README.md`(L84)、`GUI/columns/ui_left_column.py`(L155)、`GUI/columns/ui_left_setting.py`(L227) 三处 `MIT License` 链接/文本 → `Apache License 2.0`(`https://www.apache.org/licenses/LICENSE-2.0`)。
- **MT-002** — `ui_left_setting.py` `about_info`:版权年份 `2023-2025` → `2023-2026`(L226);发布日期 `2025-06-26` → `2026.09.01`(L235)。
- **MT-003** — `ui_left_setting.py`(L238-L242) 版本号统一为三位小数格式(`>= 6.5.0` / `>= 1.24.0` / `>= 2.0.0` / `>= 3.7.0` / `>= 1.2.0` / `>= 0.18.0` / `>= 1.10.0` / `>= 1.3.0`),HTML 中 `>` 转义为 `&gt;`;与 `requirements.txt` 内容一致。
- **MT-004** — `GUI/columns/ui_right_column.py`(L377):`default_path` 由 `AnyEIS_preferences.json` 改为 `User_preferences.json`;函数 `export_user_preferences` / `import_user_preferences` 命名已对齐。
- **MT-005** — `requirements.txt` 新增 `openpyxl>=3.1.0` 与说明注释;同步追加到 `README.md`、`ui_left_setting.py`、`ui_left_column.py` 依赖展示。
- **MT-006** — `EIS/FittingFile/FittingWarnings.py`(L57, L69) 与 `EIS/FigureFile/Funtest/Plotfuntest.py`(L10, L21, L203, L226) 全部 `PyQt5` → `PySide6`,`app.exec_()` → `app.exec()`,类名 `MyMplCanvasPyQt5` → `MyMplCanvasPySide6`;同步报告文档 `Funtest_Run_Issues_Summary.md`(L51) 引用更新。

**汇总**: Bug/TP 系列 18 个条目 — ✅ 13 已修复 / ✅ 2 已解决 / 🟢 2 复审撤销或降级 / ⏸️ 3 不修复(已记录理由);MT 系列 6 个条目全部 ✅ 已完成。**无未决问题**。

---

## 四、修改时间线(历史)

| 日期 | 轮次 | 范围 | 关键改动 |
|------|------|------|----------|
| 2026-08-26 | — | 数据成对化协议 | 12 个文件,引入 `ensure_paired_form` + 配对检测 |
| 2026-08-31 | — | `paraplate` / `TLcalibrate` 公式 | TP-001, TP-005 修复 |
| 2026-09-02 | — | 复审 | TP-002, TP-008 复审撤销(公式正确) |
| 2026-09-02 | — | `TLcalibrate` 数值稳定性 | TP-006 修复(np.clip + NaN 哨兵) |
| 2026-09-03 | R1 | `DieMat` 函数 | TP-009, TP-011, TP-016 修复(6 个问题决策) |
| 2026-09-04 | R2 | RF 系列 + UI 联动 | TP-014, TP-015, TP-017, TP-018 修复 |
| 2026-09-05 | — | 文档重组 | BUGS.md → update.md(归档已处理项) |
| 2026-09-05 | MT | 协议 / 元数据 / 依赖 / Qt 框架 | MT-001 ~ MT-006:Apache 2.0、版本号对齐、openpyxl 补充、PyQt5→PySide6 |

---

## 五、文档结束

> 当前文件用于持续跟踪。如需查阅历史 bug 详情,请通过 git 历史访问 `BUGS.md`。
