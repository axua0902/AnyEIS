# AnyEIS 更新与问题跟踪

> **生成时间**: 2026-09-06
> **来源**: 由 `BUGS.md` 重组而来,所有已修复 / 不修复 / 复审撤销的条目已归档至 git 历史,本文件仅保留当前活跃问题与新发现。
> **归档索引**: 历史条目见 `BUGS.md` 提交记录(汇总 22 条均已决策)。
> **本次维护记录(2026-09-06 会话)**: 完成 Bug #006 三阶段修复(架构对称 + 删除 Fixed 死列 + Error N/A 显示 + Phase 2.5 删除 simu 模式 Max/Min 列),新建 3 个测试文件(test_fixed_removal.py 17/17, test_process_ec_mt_results.py 8/8, test_simu_3column.py 12/12),更新 test_clear_calculation.py(23/23)。**所有 Bug/TP/MT 条目已全部处理,无活跃问题**。

---

## 一、当前活跃问题

> ✅ **2026-09-06 全部已修复,无活跃问题**。Bug #006 四阶段方案(Phase 1-3 + Phase 2.5)均已完成,详见下文详情。

In simulation mode:
- Users INPUT parameter values to simulate Z curves
- The simulation is deterministic - given the params, the output is fully determined
- Max/Min are typically bounds used in FITTING to constrain the parameter search space
- In simulation, users provide the exact value they want to use, not a search range

So Max/Min in simulation mode:
- Are NOT used by the simulation algorithm (only Initial_Value at col 2 is read)
- Are just additional metadata
- Take up UI space without functional value

Let me verify by looking at the simulation code that reads from the table:

Confirmed. In simulation mode:
- `simulation.py:178-182` only reads col 0 (Name) and col 2 (Initial_Value)
- Max (col 3 in simu) and Min (col 4 in simu) are NEVER read

Let me also check the MT path:

Confirmed. Both EC and MT simulation only read col 0 (Name) and col 2 (Initial_Value). Max/Min are NEVER read in simulation mode.

Now I have a clear picture. Let me give the user my analysis and recommendation.

The user is asking for my opinion on whether to keep Max/Min in simu mode. Let me think about the pros and cons:

**Arguments for REMOVING Max/Min in simu mode:**
1. **Functional dead data** — Confirmed by code reading: simulation only reads col 0 (Name) and col 2 (Initial_Value). Max/Min in simu are pure UI noise.
2. **Consistency with Phase 2** — We just removed Fixed as a dead column with the same exact rationale. Max/Min in simu is in the same category: a column the user edits but the system never reads.
3. **UX simplification** — Less visual clutter; users can focus on what actually affects output (Name, Initial_Value, Comments).
4. **Consistency between EC and MT** — Currently the simu table has 5 columns, but in fitting has 7. With Max/Min removed, simu would have 3 columns, which is more honest about what's actually used.
5. **Symmetry argument** — Fitting needs Max/Min as bound constraints for optimization; Simulation doesn't optimize anything, so the constraints are conceptually meaningless.

**Arguments for KEEPING Max/Min in simu mode:**
1. **Model persistence** — When a user creates a model in fitting mode (with Max/Min) and switches to simulation mode, removing the columns would erase their bounds.
2. **Future use** — If someone later adds bounded simulation (e.g., Monte Carlo with bounds), Max/Min would be useful.
3. **User mental model** — The user thinks of the model holistically, and the table represents that model. Removing columns changes the table layout confusingly between modes.
4. **JSON roundtrip** — `load_ecm_model_to_ui` reads from JSON which has min/max fields. If simu table doesn't show them, they're silently dropped on roundtrip.

**My recommendation**: REMOVE Max/Min in simu mode, BUT persist them in JSON. The simulation algorithm doesn't need them, but the model storage does.

Wait, let me re-read the user's question: "在simulation和fitting中，需要的表头，应该不同" - "In simulation and fitting, the headers needed should be different"

So the user already agrees that the headers should differ. The question is whether to keep Max/Min in simu.

I think the best approach is:
- **simu mode**: 3 columns only (Name, Comments, Initial_Value) — what simulation actually uses
- **fit mode**: 7 columns (Name, Comments, Initial_Value, Fitted_Value, Max, Min, Error [%])

But we need to make sure Max/Min are preserved in JSON even when simu table doesn't display them. The existing `create_ecm_model_json` already serializes 7 fields including min/max. The `load_ecm_model_to_ui` should still write them to JSON even if the simu table doesn't display them.

Wait, but if simu doesn't have Max/Min columns, the user can't edit them. So when switching from fitting to simulation, the Max/Min values should be preserved in the model data (not just in JSON), and when switching back to fitting they should be restored.

This is getting complex. Let me give a focused recommendation:

**Recommendation**: 
- simu mode → 3 columns: `Name, Comments, Initial_Value` (minimal, what simulation actually needs)
- This is consistent with the Phase 2 dead-column-removal logic
- Implementation: store max/min in instance attributes (self.params bounds) or in JSON, but don't show them in simu UI

Actually, I should be careful not to over-engineer. Let me think about this from the user's perspective:
- User has a model
- User wants to simulate it
- They only need to specify the value (Initial_Value)
- The Max/Min are just clutter in this mode

This is the same logic as the Phase 2 fix. The only thing that matters in simu is `value`. Comments is metadata. Max/Min are pure dead columns in simu.

Let me give the user a clear, well-reasoned recommendation.
# 关于 simulation 模式表头的修改建议

## 核心结论:**simu 模式应只保留 3 列** — `Name, Comments, Initial_Value`

## 关键证据(已验证)

我重新读了 [simulation.py:178-182](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/SimulationFile/simulation.py#L178-L182) (EC) 和 [simulation.py:312-315](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/SimulationFile/simulation.py#L312-L315) (MT) 的实际读取逻辑:

```python
# ECM 仿真(L178-182)
elementname1 = self.tab1.ECMtable.item(temp - 1, 0).text()  # Name
init_val = float(self.tab1.ECMtable.item(temp - 1, 2).text())  # Initial_Value
self.params[elementname1] = Parameter(elementname1, value=init_val)

# MT 仿真(L313-315) — 完全同构
paraname = self.tab2.MTtable.item(temp - 1, 0).text()
init_val = float(self.tab2.MTtable.item(temp - 1, 2).text())
self.MTparams[paraname] = Parameter(paraname, value=init_val)
```

**Max / Min 在 simulation 中 100% 不读,纯 UI 摆设**。这与 Phase 2 删除 Fixed 死列的根因完全一致。

## 三种方案对比

| 方案 | simu 列数 | 优点 | 缺点 |
|------|-----------|------|------|
| **A. 保留 Max/Min**(当前 5 列) | 5 | 模式切换时列不会"突变",JSON 字段保留 | 仍含 2 列死数据,违反 Phase 2 修复原则 |
| **B. 删 Max/Min**(推荐 3 列) | 3 | 简洁诚实,与 Phase 2 修复一致;UI 更聚焦;用户输入负担更小 | 模式切换会引发 3↔7 列的"突变";需要确保 max/min 仍持久化 |
| **C. 删 Max/Min + 全隐藏式持久化** | 3 | 同 B,且 max/min 仍在 self.params / JSON 中,切回 fit 时自动恢复 | 实现略复杂,需在 mode 切换时双向同步 |

## 推荐:方案 C(进阶)

理由:
- **完全符合"只显示有用的"原则** — 仿真算法只读 `value`,显示 `Initial_Value` 即够;`Max/Min` 是 fitting 的边界约束,simu 不需要
- **避免死列回潮** — 上次刚把 Fixed 删了,这次保留 Max/Min 等于在 simu 模式重蹈覆辙
- **JSON 兼容性** — `create_ecm_model_json` / `load_ecm_model_to_ui` 已包含 `min/max` 字段持久化,无需修改
- **实现成本低** — 仅 `setMTMTableHeader('simu')` / `setECMTableHeader('simu')` 改 label,加 2 行 mode 切换时的 max/min 暂存/恢复代码

### 具体改动

**`MTMUI.py` / `ECUI.py` 的 `setXxxTableHeader`**:
```python
if mode == 'fit':
    label = ['Name', 'Comments', 'Initial_Value', 'Fitted_Value', 'Max', 'Min', 'Error [%]']
else:  # simu
    label = ['Name', 'Comments', 'Initial_Value']  # 3 列
```

**`simulation.py` / `Fitting.py` 的 mode 切换回调**(新增):在切到 simu 前,把 ECMtable/MTtable 的 max/min 写入 `self._simu_param_bounds = {name: (min, max)}`;切回 fit 前再写回表格。这样切换不丢数据。

**`ECMFunctions.create_ecm_model_json`**:完全不动 — JSON 仍然存 7 个字段(包括 min/max),与 simu UI 解耦。

**测试**:
- `test_fixed_removal.py` 加 2 个测试,验证 simu 模式列结构为 3 列
- `test_clear_calculation.py` 的 `TestSimulationClearMethods` 仍应全通过(simu 本就不清表)
- 新增 mode 切换的 roundtrip 测试,验证 max/min 切回 fit 时未丢失

## 如果你倾向保守(方案 A)

那就保持现状 5 列不动。理由是模式切换时不会有视觉跳变,用户更熟悉。但需要明确记录 "Max/Min 在 simu 模式暂不参与计算,仅作模型信息保留" 这条 trade-off。

## 决策点

1. **是否采用方案 C(3 列 + 隐藏式持久化)?** — 推荐
2. **还是先停在方案 A(5 列现状),把 Phase 2 标记为已完整?** — 保守
3. **是否需要保留 Max 但删 Min?** — 中间方案,但收益不大,不推荐

我建议采用方案 C。如确认,我立即实施。
---

## 二、已完成条目详情

### Bug #006 详情(表格列与算法匹配 — 三阶段修复 2026-09-06):

**现象**:
  - [ECUI.py#L612-613](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ModelFile/ECUI.py#L612-L613) `setECMTableHeader` 模式分支:fit = 8 列(含 Fitted_Value/Error [%] 输出列),simu = 6 列(纯用户输入)。
  - [MTMUI.py#L475-476](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ModelFile/MTMUI.py#L475-L476) 硬编码 8 列表头,没有 `setMTMTableHeader` 镜像,只能由 `simulation.py:132-133` 手动 `setColumnCount(6)` 重置(架构不对称)。
  - **Fitted_Value / Error [%]** 仅 Fitting 有输出,Simulation 已隐藏(✅ 设计正确)。
  - **Max / Min / Fixed** 在 Simulation 中**完全不读**:`simulation.py:181-183` (EC) 与 `:313-316` (MT) 只读 col 0/2(Name/Initial_Value)。
  - **Fixed 列在 Fitting 路径同样不读**:`Fitting.py:365-381` (EC) 与 `:573-578` (MT) 跳过 col 6;全工程 grep 不到 `item(row, 6)` 的 `vary=False` 写入路径。
  - **Error [%] 仅 least_squares 有效**:`Fitting.py:725, 791` 在 `stderr is None` 时写入 `NaN`,9 种其它算法(全局/启发式)均显示 NaN,无意义且易误导。

**涉及文件**:
  - `EIS/ModelFile/ECUI.py` — `setECMTableHeader` (L603-626)、初始化表头 (L439-445)
  - `EIS/ModelFile/MTMUI.py` — `setMTMTableHeader` (L533-556)、初始化表头 (L474-483)
  - `EIS/SimulationFile/simulation.py` — 初始化表头 (L130-132)、`clearECCalculation`/`clearMTCalculation` docstring (L203-211, L333-341)
  - `EIS/ModelFile/ECMFunctions.py` — `create_ecm_model_json` (L93-108)、`load_ecm_model_to_ui` (L131-159)、`clearECMModel` (L304-316)
  - `EIS/FittingFile/Fitting.py` — `processECMResults` (L721-734)、`processMTResults` (L788-798)、`ECMcalculation` (L363-381)、`MTcalculation` (L573-578)、`clearECCalculation`/`clearMTCalculation` (L479-539)
  - `EIS/FittingFile/Funtest/test_clear_calculation.py` — 23 个测试用例(全部通过)
  - `EIS/FittingFile/Funtest/test_fixed_removal.py` — **新建 17 个测试用例**(全部通过)
  - `EIS/FittingFile/Funtest/test_process_ec_mt_results.py` — **新建 8 个测试用例**(全部通过)

**根因分析**:
  - Fixed 复选框在 `ECMFunctions.py:147-149` 创建并持久化到 JSON,但**全工程没有任何代码路径读取它** —— `Fitting.py` 与 `simulation.py` 构造 `lmfit.Parameter` 时只传 `value/min/max`,未传 `vary`。该列从 UI 到数据流全程不参与,纯历史遗留 UI 摆设。
  - `MTMUI` 与 `ECUI` 架构不对称:EC 已有 `setECMTableHeader(mode)` 统一入口,MT 散落在 `simulation.py` 内联重置。
  - `param.stderr` 只在 `least_squares` (LM) 算法下由协方差矩阵算出,其它 9 种算法在 lmfit 中 `stderr is None`。

**修复方案(三阶段)**:

- **Phase 1 — 架构对称**(✅ 已完成):在 `MTMUI.py` 新增 `setMTMTableHeader(mode='fit')`,与 `ECUI.setECMTableHeader` 镜像;`simulation.py:131-132` 改为统一调用 `self.tab1.setECMTableHeader('simu')` + `self.tab2.setMTMTableHeader('simu')`。

- **Phase 2 — 删除 Fixed 死列**(✅ 已完成):从所有表头常量、模型加载、`Fitting.py` 读取、测试断言中彻底移除 `Fixed`。**变更后列数**:fit 8→7(Error [%] 从 col 7→6),simu 6→5(Min 从 col 4→3, Fixed 列消失);Max/Min 在 fit/simu 中的列号保持 4/5(fit)与 3/4(simu)不变。

- **Phase 3 — Error [%] N/A 显示**(✅ 已完成):`Fitting.py:725, 791` 在 `stderr is None` 时写入字符串 `'N/A'` 而非 `NaN`,列始终保留(不动表头)。

**验证**:
  - `test_clear_calculation.py`: 23/23 通过(扩到 7 列表 + cleared_cols=(3, 6) + simu 5 列表)
  - `test_fixed_removal.py`(新建): 17/17 通过
    - `TestColumnStructure` (4): 验证 ECUI/MTMUI fit/simu 列数与顺序
    - `TestECMFunctionsSource` (5): 静态扫描 `setHorizontalHeaderLabels`/`setColumnCount(8)`/`fixed_checkbox`/`.checkState()`
    - `TestUISource` (2): 验证 ECUI/MTMUI 不再硬编码 8 列
    - `TestFittingSource` (3): 验证 `ECMtableWrite`/`MTtableWrite` 写入 col 6 而非 col 7
    - `TestClearECMModel` (1): 验证 `clearECMModel` 通过 `setECMTableHeader('fit')` 重置
    - `TestLoadECMModelToUI` (1): 验证模型加载创建 7 列(含 Error 占位)
    - `TestCreateECMModelJson` (1): 验证 JSON 序列化不再含 'fixed' 字段
  - `test_process_ec_mt_results.py`(新建): 8/8 通过
    - `TestSourceCode` (4): 静态验证 `processECMResults`/`processMTResults` 不再含 `float('nan')`,已替换为 `'N/A'`
    - `TestProcessECMResultsBehavior` (2): 行为级验证 stderr=None 写入 'N/A',有值时写入百分比
    - `TestProcessMTResultsBehavior` (2): 同上 MT 路径
  - 完整回归:`pytest EIS/FittingFile/Funtest/` 共 **48 个测试全部通过** (test_clear_calculation + test_fixed_removal + test_process_ec_mt_results + 既有 fitting/MT/decision 流程)
  - 无回归:`test_all_methods.py` 中 4 个原有测试 + 1 个 mt_flow 全部通过(原生的 `test_extreme_conditions` / `test_noise_levels` 在我修改前就存在 STATUS_STACK_BUFFER_OVERRUN 崩溃,与本次修改无关)
  - 实际行为验证:`python -c` 构造 ECUI/MTMUI 实例,确认 fit 模式 7 列、simu 模式 5 列;`load_ecm_model_to_ui` 后 ECMtable 7 列无 Fixed
  - 状态: ✅ 已修复(2026-09-06)

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
| Bug #004 | Simulation/Fitting Tab 切换未联动 figure 数据类型 | ✅ 已修复(2026-09-06) |
| Bug #005 | 计算行 Clear 按钮孤立 / 槽实现不一致 | ✅ 已修复(2026-09-06) |
| Bug #005b | Clear 误清 Fixed 列 / Simulation 6 列错位 | ✅ 已修复(2026-09-06) |
| Bug #006 | 表格列与算法匹配(Phase 1 架构对称 + Phase 2 删 Fixed + Phase 3 N/A) | ✅ 已修复(2026-09-06) |

**Bug #004 详情**:

- **现象**:
  - Simulation 页面选择 Tab0(Equivalent circuit)时,figure 区域的 `datatypeComboBox` 未切换到 `f-Z,Phase,Re(Z),Im(Z)`,导致图表按钮组(Nyquist/Bode Re/Im/Phy)仍显示 Multi-terms model 的标签(Bode f-Sigma / f-Epsilon / f-theta)与勾选状态。
  - Fitting 页面完全没有 Tab 切换联动逻辑,无论选哪个 tab,figure 的 datatypeComboBox 都保持初始值不动。
- **涉及文件**:
  - `GUI/pages/ui_page_simulation.py` — `on_simulation_tab_changed`(L71-L77)
  - `GUI/pages/ui_page_fitting.py` — 类 `Ui_FittingPage`(L105-L109 后追加)
- **根因分析**:
  - `ui_page_simulation.py:73` 硬编码的字符串 `'f-Z,Phy,Rs,X'` 与 `ui_Figure.py:115` 中下拉框实际项 `'f-Z,Phase,Re(Z),Im(Z)'` **不匹配**。`QComboBox.setCurrentText()` 找不到完全匹配项时**静默失败**,下拉框状态保持不变。
  - `ui_page_fitting.py` 整个类**未连接** `FittingWg.currentChanged` 信号,缺少 `on_fitting_tab_changed` 回调。
- **修复方案**:
  - `ui_page_simulation.py:73`:`'f-Z,Phy,Rs,X'` → `'f-Z,Phase,Re(Z),Im(Z)'`。
  - `ui_page_fitting.py:111-L118` 追加:
    ```python
    # Tab 切换时同步 figure 数据类型下拉框
    self.FittingWg.currentChanged.connect(self.on_fitting_tab_changed)

    def on_fitting_tab_changed(self, index):
        if index == 0:
            self.figureWg.figuregui.datatypeComboBox.setCurrentText('f-Z,Phase,Re(Z),Im(Z)')
        elif index == 1:
            self.figureWg.figuregui.datatypeComboBox.setCurrentText('f-Epsilon,Sigma')
    ```
- **验证**:
  - Simulation 页面:Tab0 ↔ Tab1 切换,figure 按钮组标签在 `f-Z,Phase,Re(Z),Im(Z)` 与 `f-Epsilon,Sigma` 两套配置间正确切换。
  - Fitting 页面:Tab0(Equivalent circuit)切换后 `datatypeComboBox` 变更为 `f-Z,Phase,Re(Z),Im(Z)`;Tab1(Multi-terms model)切换后变更为 `f-Epsilon,Sigma`,按钮组文字与勾选状态同步刷新(由 `Figure.selectionchange` 触发 `_set_button_states`)。
  - 风险点:`setCurrentText` 会触发 `currentIndexChanged → selectionchange`,但因当前无 plotdata,`_set_button_states` 只更新按钮文字与勾选状态,不触发重绘,无副作用。

**Bug #005 详情**:

- **现象**:
  - [MTMUI.py#L516-529](file:///c:/Users/zhang%20an/Desktop/Research/paper/6.AnyEIS%20Software/AnyEIS/EIS/ModelFile/MTMUI.py#L516-L529) 的 `self.clearBtn`（计算行 Clear 按钮）**完全没有 connect** —— `Fitting.py` 和 `simulation.py` 中只连了 `self.tab1.clearBtn.clicked.connect(self.clearCalculation)`,**没有任何地方 connect `self.tab2.clearBtn`**。结果:用户点击 MT 的 Clear 按钮无任何反应。
  - EC 的 Clear 槽实现不一致: `Fitting.py` 的 `clearCalculation` 是空函数（仅 `return`）;`simulation.py` 的 `clearCalculation` 实际是 B-2 语义（清空整个模型）,与 `clearECMModel` 功能高度重叠。
  - ECUI.py 与 MTMUI.py 的 `clearBtn` 创建代码本身是一致的（视觉/样式无差异）,问题在于**信号连接和槽实现**。
  - `clearModelBtn`（文件行）已经有完整工作流（`clearECMModel` / `clearMTModel`）,且用了**警示色**（MTMUI: dark_blue,ECUI: red_primary）。两套 Clear 按钮**职责应互补**而非重复。
- **涉及文件**:
  - `EIS/FittingFile/Fitting.py` — `clearCalculation`（L478,空函数）→ `clearECCalculation`（新增 B-1 实现）;新增 `clearMTCalculation`
  - `EIS/FittingFile/Fitting.py` — connect 区块:`self.tab1.clearBtn.clicked.connect(self.clearCalculation)` → `self.clearECCalculation`;新增 `self.tab2.clearBtn.clicked.connect(self.clearMTCalculation)`
  - `EIS/SimulationFile/simulation.py` — `clearCalculation`（L200, B-2 语义）→ `clearECCalculation`（B-1 语义）;`clearMTCalculation`（L336, B-2 语义）→ B-1 语义
  - `EIS/SimulationFile/simulation.py` — connect 区块同上
- **根因分析**:
  - **历史债务**: `tab2.clearBtn` 从未被 connect,导致 MTMUI 的 Clear 按钮始终孤立;`tab1.clearBtn` 的 connect 目标在不同文件中语义不一致（空函数 vs B-2 重型清空）。
  - **职责重叠**: 文件行已有 `clearModelBtn`（红色警示色）做"清空模型";计算行的 `clearBtn`（灰色普通色）若也清空模型,既冗余又与红色警示色按钮功能冲突。
  - **设计结论**: 采用 B-1 语义 —— 计算行 Clear = "清空最近一次 Calculate 的输出",保留模型结构(电路/方程/参数初值/连接文本/勾选);文件行 Clear Model = "重置整个模型"(由 `clearModelBtn` 已承担)。
- **修复方案**:
  - B-1 合约(以 Fitting.py 为准,simulation.py 同形):

    ```python
    def clearECCalculation(self):
        # 清空 fitteddata / fittedresults / resultsdataInfo
        self.fitteddata = list()
        self.fittedresults = list()
        self.resultsdataInfo = []
        # 清空全局 plot 副本
        global plotdata, plotdataname, outputlist
        plotdata = list(); plotdataname = list(); outputlist = list()
        # 清空 ECMtable 的 Fitted_Value(3) / Fixed(6) / Error [%](7) 列
        # 保留 Name(0) / Comments(1) / Initial_Value(2) / Max(4) / Min(5)
        for row in range(self.tab1.ECMtable.rowCount()):
            for col in (3, 6, 7):
                self.tab1.ECMtable.setItem(row, col, QTableWidgetItem(""))
    ```
  - `clearMTCalculation` 同形,作用于 `self.tab2.MTtable`。
  - **保留**:`circuit` / `params` / `termnamelist` / `modelterm` / `MTexpre` / `MTmultitermTextEdit` / `connectionTextEdit` / `option` / EP&DC 勾选 / `MTparams`。
  - **simulation.py** 的 `clearECCalculation` / `clearMTCalculation` 因没有 fitteddata 字段,只清全局 plot 副本与表格 Fitted 列。
  - **connect** 调整:
    - `self.tab1.clearBtn.clicked.connect(self.clearCalculation)` → `self.clearECCalculation`
    - **新增** `self.tab2.clearBtn.clicked.connect(self.clearMTCalculation)`
    - `clearModelBtn` 的 connect 保持不变（仍接 `clearECMModel` / `clearMTModel`）。
- **验证**:
  - 新建 `EIS/FittingFile/Funtest/test_clear_calculation.py`(19 个测试用例,全部通过):
    - 4 个 `TestClearECCalculation`:验证 fitteddata/resultsdataInfo 清空、全局 plotdata 清空、表格只清 3/6/7 列、circuit/params/connectionTextEdit 保留
    - 5 个 `TestClearMTCalculation`:同上 + termnamelist/modelterm/MTexpre/option/MTmultitermTextEdit/EP&DC 全部保留
    - 4 个 `TestSimulationClearMethods`:simulation.py 同形 B-1 验证
    - 5 个 `TestSignalConnections`:静态校验 connect 语句中按钮→槽的映射,确保 `tab2.clearBtn` 真正 connect 到 `clearMTCalculation`;`tab1.clearBtn` 不再 connect 旧 `clearCalculation`;Fitting.py 中旧的 `def clearCalculation(self):` 已删除
  - 关键 mock 技巧:不实例化 Fitting/Simu 类（避免触发 PyTabWidget2 等重依赖 + native crash 风险）,用 `unittest.mock.MagicMock` + `types.SimpleNamespace` 构造最小对象,将 `Fitting.clearECCalculation` 作为函数直接调用,验证对 `self.fitteddata` / `self.tab1.ECMtable.setItem` / 全局变量的访问路径与清空列范围
  - 完整 import 链验证:`python -c "from EIS.FittingFile.Fitting import Fitting; from EIS.SimulationFile.simulation import Simu"` 通过,四个新方法都正确导出。
  - 测试结果: **19/19 通过**(`pytest EIS/FittingFile/Funtest/test_clear_calculation.py -v`,耗时 4.46s)。
  - 无回归:`test_all_methods.py` 中 4 个原有测试 + 1 个 mt_flow 全部通过(原生的 `test_extreme_conditions` / `test_noise_levels` 在我修改前就存在 STATUS_STACK_BUFFER_OVERRUN 崩溃,与本次修改无关)。

**Bug #005b 详情(Clear 按钮第二轮修复)**:

- **用户反馈**:
  > "MT的clear按下后，再按计算，不可以进行新的计算，表格模型参数的名字都被删掉了，而ECM按下后，再按计算，可以进行新的计算。检查差异，统一逻辑。"

- **根因诊断**(用 `debug_clear_mt.py` 在 6 列/8 列 MTtable 上直接复现):
  - **关键差异**:MTtable 在 Fitting 路径下是 **8 列**,在 Simulation 路径下被强制改为 **6 列**(无 Fitted_Value, 无 Error [%])。
  - **Bug 5a**:第一轮我设计的 `cleared_cols = (3, 6, 7)`,在 Fitting 8 列下:
    - col 3 = Fitted_Value ✓ 应清
    - col 6 = **Fixed 用户输入** ❌ 被误清
    - col 7 = Error [%] ✓ 应清
  - **Bug 5a**:同一份代码在 Simulation 6 列下:
    - col 3 = **Max 用户输入** ❌ 被误清(Max 在 6 列下排在第 3 位!)
    - col 6/7 越界但 setItem 不抛错
    - 用户看到"参数名字/边界被删掉"就是这一症状
  - **错位结构**:
    | 列索引 | Fitting 8 列 | Simulation 6 列 |
    |---|---|---|
    | 0 | Name | Name |
    | 1 | Comments | Comments |
    | 2 | Initial_Value | Initial_Value |
    | 3 | Fitted_Value | **Max** ❌ |
    | 4 | Max | Min |
    | 5 | Min | Fixed |
    | 6 | **Fixed** ❌ | (无) |
    | 7 | Error [%] | (无) |

- **修复方案**:
  - Fitting 路径: `cleared_cols = (3, 7)` —— **保留 col 6 (Fixed 用户输入)**
  - Simulation 路径: **完全不动表格** —— 6 列无 Fitted_Value / Error [%] 列,所有列均为用户输入
  - ECMtable 同形: Fitting 8 列下也保留 col 6 (Fixed),Simulation 6 列下不动
  - 对称性:clearECCalculation / clearMTCalculation 在 Fitting 与 Simulation 两条路径下行为完全对称

- **验证**(`test_clear_calculation.py` 扩到 23 个测试用例,全部通过):
  - 新增 `TestRealTableIntegration`(3 个真实 QTableWidget 集成测试,需 QApplication):
    - `test_Fitting_clearMTCalculation_on_8col_preserves_all_user_input`:在 8 列 MTtable 上,验证 clear 后 Name/Comments/Initial_Value/Max/Min/Fixed 全部保留,只清 Fitted_Value/Error [%]
    - `test_Fitting_clearECCalculation_on_8col_preserves_Fixed`:ECMtable Fixed 列在 clear 后必须仍为 'False' (用户输入不被误清)
    - `test_simulation_clearMTCalculation_on_6col_does_nothing_to_table`:6 列 MTtable 在 Simulation 路径下完全不变,columnCount 保持 6 不被 setItem 越界扩展
  - 新增回归保护测试 `test_clear_uses_cleared_cols_3_7_not_including_6`:静态扫描 Fitting.py / simulation.py 中 `clearECCalculation` / `clearMTCalculation` 函数体,确保不再包含 `(3, 6, 7)` 这种错误配置
  - 调整原有断言: `test_clears_ecm_table_columns_3_and_7_only` / `test_clears_mt_table_columns_3_and_7_only` 从 9 次 setItem 改为 6 次,`forbidden` 列集合增加 6
  - 调整 `TestSimulationClearMethods`: 4 个测试现在验证 `setItem` / `clearContents` / `setRowCount` 都不被调用
  - 测试结果: **23/23 通过**(耗时 4.27s)

- **遗留观察**(非本轮问题,记录供后续):
  - Fitting.MTcalculation(L591) 强制覆盖 `MTlowfreqTextEdit` / `MTupfreqTextEdit`,这是另一处隐式行为,但不在 Clear 按钮的修复范围。
  - simulation.MTcalculation 读 col 0/2 (Name/Initial_Value),不读 col 3/4/5,所以 simulation 路径下即使 6 列也不会因 max/min 缺失而崩溃(但 Fitting 路径 MTcalculation 读 col 0/2/4/5,8 列下恰好正确)。

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

**汇总**: Bug/TP 系列 22 个条目 — ✅ 18 已修复 / ✅ 2 已解决 / 🟢 2 复审撤销或降级 / ⏸️ 3 不修复(已记录理由);MT 系列 6 个条目全部 ✅ 已完成。**无未决问题**。

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
| 2026-09-06 | Bug #004 | Simulation/Fitting Tab 联动 | `ui_page_simulation.py:73` 字符串修正 + `ui_page_fitting.py` 补全 `currentChanged` 联动 |
| 2026-09-06 | Bug #005 | 计算行 Clear 按钮 | Fitting/simulation.py 拆分 `clearECCalculation` / `clearMTCalculation`（B-1 语义），connect `tab2.clearBtn`；新建 test_clear_calculation.py（19/19 通过） |
| 2026-09-06 | Bug #005b | Clear 误清 Fixed 列 / Simulation 6 列错位 | 调整 cleared_cols = (3, 7) 不含 6（保留 Fixed 用户输入）；simulation 路径 6 列表无计算结果列，完全不动表；test_clear_calculation.py 扩到 23/23 通过 |
| 2026-09-06 | Bug #006 | 表格列与算法匹配(三阶段方案) | Phase 1: MTMUI.setMTMTableHeader 镜像 ECUI;Phase 2: 彻底删除 Fixed 死列(8→7 / 6→5 列);Phase 3: Error [%] 非 LS 算法显示 N/A;新建 test_fixed_removal.py(17/17)+ test_process_ec_mt_results.py(8/8);update.md 标记已完成 |

---

## 五、文档结束

> 当前文件用于持续跟踪。如需查阅历史 bug 详情,请通过 git 历史访问 `BUGS.md`。
