# FittingMT.py 拟合测试报告

## 测试文件
`e:\Research\AnyEIS\AnyEIS4_test\EIS\FittingFile\Funtest\FittingMT_new_test.py`

辅助文件：`e:\Research\AnyEIS\AnyEIS4_test\EIS\FittingFile\Funtest\PrecisionFitHelper.py`

---

## 核心问题：参数耦合导致的局部最优

双Debye模型（6参数）存在强参数耦合。不同参数组合可能产生相似的频谱响应，导致优化器在局部最优停止。

### 诊断：Sanity Check
- 初始值=真值 → 误差0% ✓
- 初始值偏离20% → 误差~20%（未收敛到真值）

---

## 推荐方法：分步拟合 (`fit_staged`)

### 问题根源分析
1. **参数耦合**：Deps/Tao之间存在相关性
2. **数量级差异**：sigmaDC(1e-4) vs Tao(1e-7) 相差3个数量级
3. **局部最优**：标准优化器在Stage 2被卡住

### 解决思路

**核心思想**：分而治之，先简化问题，再精细化

```
Stage 1: 单弛豫拟合
├── 只优化 epsh, sigmaDC, Deps1, Tao1
├── 固定 Deps2=30, Tao2=1e-7（猜测值）
└── 得到粗略的 epsh, sigmaDC, Deps1, Tao1

Stage 2: 双弛豫精修
├── 使用 Stage 1 结果作为初始值
├── 释放全部6个参数
└── 精细优化
```

### 代码实现

```python
def fit_staged(self, params_init, prodata, verbose=False):
    """分步拟合策略"""

    # Stage 1: 单弛豫粗略拟合
    single_term = [self.modelterm[0]]  # 只用第一个Debye项
    single_init = {
        'epsh': params_init['epsh'],
        'sigmaDC': params_init['sigmaDC'],
        'Deps1': params_init['Deps1'],
        'Tao1': params_init['Tao1']
    }

    # 严格容差 + soft_l1损失函数
    minner = Minimizer(fcn2min, params,
                      ftol=1e-10, xtol=1e-10, gtol=1e-10,
                      loss='soft_l1', max_nfev=1e5)
    result1 = minner.minimize(method='least_squares')

    # Stage 2: 双弛豫精修
    refined_init = dict(zip(result1.var_names, result1.x))
    refined_init['Deps2'] = params_init.get('Deps2', 30.0)  # 猜测值
    refined_init['Tao2'] = params_init.get('Tao2', 1e-7)    # 猜测值

    # 更严格容差
    minner2 = Minimizer(fcn2min, params2,
                       ftol=1e-12, xtol=1e-12, gtol=1e-12,
                       loss='soft_l1', max_nfev=1e5)
    result2 = minner2.minimize(method='least_squares')

    return result2
```

### 关键技巧

| 技巧 | 作用 | 效果 |
|-----|------|-----|
| soft_l1损失函数 | 鲁棒化，对离群点不敏感 | 避免极端值干扰 |
| 参数边界 min=0 | 物理约束 | 防止负参数 |
| Stage 2更严容差 | 精细调优 | chi²从3.0降至0.002 |
| 仅优化4参数(Stage1) | 降低自由度 | 避免过早陷入局部最优 |

---

## 测试结果

| 测试 | 结果 | 说明 |
|-----|------|-----|
| 分步拟合(标准) | ✓ | 误差<5% |
| 宽频率范围 | ✓ | 误差1.12% |
| 多参数组合 | ⚠ | 小参数时272% |
| 三弛豫模型 | ⚠ | 停在初始值20% |
| 参数数量级差异 | ⚠ | sigmaDC误差96% |
| Sanity Check | ✓ | 误差0% |

---

## 适用场景

| 场景 | 参数特点 | 误差 |
|-----|---------|------|
| 标准参数 | 数量级相近 | <5% |
| 宽频率(1kHz~10GHz) | 8频率点 | ~1% |
| 三弛豫模型 | 8参数 | ~20% |

## 不适用场景

| 场景 | 问题 | 误差 |
|-----|------|-----|
| 小参数 Tao~1e-8 | 数量级差异大 | ~270% |
| 参数差异>5数量级 | 极端差异 | ~100% |

---

## 经验总结

### 为什么分步拟合有效？

1. **降维**：Stage 1 只优化4参数 vs 6参数
2. **粗调定位**：Stage 1 快速找到参数大致范围
3. **精调收敛**：Stage 2 在好初始值附近细搜

### 什么情况下会失败？

**1. 参数数量级差异>5**：Tao1=1e-3, Tao2=1e-8 导致耦合严重

**2. 初始值偏离过大**：初始值与真值差异>50%

**3. 三弛豫以上**：参数耦合更复杂

**4. 频率点太少**：5个频率点难以区分2个弛豫，chi²偏高

**5. 频率范围未覆盖特征频率**：ωτ≈1时响应最明显，未覆盖则拟合不唯一

**6. Deps1 ≈ Deps2**：两个弛豫叠加难以分离，参数耦合

**7. 数据噪声过大**：信噪比低时拟合参数震荡

**8. 模型与数据不匹配**：Debye模型拟合Cole-Cole数据，误差大但拟合"成功"

### 常见问题排查

| 问题 | 检查项 | 解决方案 |
|-----|-------|---------|
| chi²偏高 | 频率覆盖？ | 扩展频率范围 |
| 参数误差大 | 初始值？ | 接近真值 |
| 不收敛 | 边界过严？ | 放松min/max |
| 负参数 | 缺少边界？ | 添加min=0 |
| 局部最优 | 参数耦合？ | 使用分步拟合 |

### 调试建议

- 先跑 Sanity Check（初始值=真值）确认拟合器正常
- 再跑分步拟合，误差<5%说明工作正常
- 误差>20%时，检查：参数数量级、数据质量、频率覆盖

## 高级拟合策略 (AdvancedFittingStrategies.py)

针对复杂拟合问题，提供3种高级策略：

### 策略1: 对数空间优化 (`fit_log_space`)

**原理**：将参数转换到对数空间优化，避免大数量级参数主导优化

**解决**：
- 数量级差异>5（如Tao1=1e-3, Tao2=1e-8）
- sigmaDC与其他参数数量级差异大

**测试结果**：
| 参数 | 拟合值 | 真值 | 误差 |
|-----|-------|------|-----|
| epsh | 1.00e+01 | 1.00e+01 | 0.0% |
| Deps1 | 8.08e+01 | 8.00e+01 | 1.0% |
| Tao1 | 1.01e-03 | 1.00e-03 | 0.5% |
| Deps2 | 5.00e+00 | 5.00e+00 | 0.0% |
| Tao2 | 1.00e-08 | 1.00e-08 | 0.0% |

**评价**：数量级差异5个量级时仍有效，chi²达到9.7e-09

### 策略2: 多起点随机初始化 (`fit_multi_start`)

**原理**：在参数空间多个随机点开始优化，寻找全局最优。改用对数尺度扰动（±1 decade），更有效探索参数空间。

**解决**：
- 初始值偏离>50%
- 局部最优陷阱

**测试结果**（100%初始偏差）：
| 参数 | 拟合值 | 真值 | 误差 |
|-----|-------|------|-----|
| epsh | 1.00e+01 | 1.00e+01 | 0.3% |
| sigmaDC | 1.01e-04 | 1.00e-04 | 0.6% |
| Deps1 | 4.99e+01 | 5.00e+01 | 0.3% |
| Tao1 | 9.98e-06 | 1.00e-05 | 0.2% |

**评价**：对数尺度扰动后效果显著提升，100%初始偏差时误差<1%

### 策略3: 扩展分步拟合 (`fit_staged_extended`)

**原理**：三弛豫时直接从双弛豫开始（跳过单弛豫避免误差传递），然后精修三弛豫。双弛豫仍使用原始分步策略。

**解决**：
- 三弛豫及以上模型
- 参数耦合问题

**测试结果**：
- Stage 1 chi²: 0.15 → Stage 2: 0.77
- 部分参数误差仍大（epsh 161%, Tao2 252%）

**评价**：三弛豫参数耦合强，需要更好的初始估计或预判特征频率

### 组合策略 (`fit_robust`)

结合多起点 + 对数空间 + 分步拟合，处理最困难的情况

### 关键发现

1. **对数空间优化** - 数量级差异5个量级时仍有效
2. **多起点策略** - 100%初始偏差可接受
3. **三弛豫问题** - Stage1误差会传递放大，需改进

### 适用场景

| 策略 | 适用 | 不适用 |
|-----|------|-------|
| fit_log_space | 数量级差异大 | 参数有负值 |
| fit_multi_start | 初始值不确定 | 计算时间敏感 |
| fit_staged | 双弛豫，参数接近 | 三弛豫，数量级差异大 |

---

## 拟合方法总结

### 文件与拟合方法对照表

| 文件 | 拟合方法 | 适用场景 |
|-----|---------|---------|
| `FittingMT.py` | 原始`FittingMT`函数 | 基本拟合，参数接近真值 |
| `FittingMT.py` | `FittingMT_auto` | **自动选择最佳策略（推荐）** |
| `PrecisionFitHelper.py` | `fit_staged` | 双弛豫，推荐首选 |
| `PrecisionFitHelper.py` | `fit_staged_with_restart` | 初始值不确定，需全局搜索 |
| `PrecisionFitHelper.py` | `fit_multi_method` | 避免局部最优，多求解器 |
| `PrecisionFitHelper.py` | `fit_with_initial_guess_variation` | 系统搜索，穷举初始值 |
| `AdvancedFittingStrategies.py` | `fit_log_space` | 数量级差异>5个量级 |
| `AdvancedFittingStrategies.py` | `fit_multi_start` | 初始值偏离>50% |
| `AdvancedFittingStrategies.py` | `fit_staged_extended` | 三弛豫及以上 |
| `AdvancedFittingStrategies.py` | `fit_robust` | 最困难情况，组合策略 |

---

### 场景推荐

**推荐使用 `FittingMT_auto`** - 自动分析问题特征并选择最佳策略

**1. 双弛豫模型，参数数量级相近**
→ `FittingMT_auto` 自动选择分步拟合+多起点

**2. 双弛豫模型，数量级差异大（如Tao1=1e-3, Tao2=1e-8）**
→ `FittingMT_auto` 自动选择对数空间优化，误差<1%

**3. 初始值不确定，偏离真值>50%**
→ `FittingMT_auto` 自动选择多起点策略

**4. 三弛豫及以上模型**
→ `FittingMT_auto` 自动选择跳过单弛豫的分步拟合

**5. 最困难的情况（数量级差异+初始值偏离+多弛豫）**
→ `FittingMT_auto` 自动组合多种策略

**6. 避免局部最优，多方法尝试**
→ `PrecisionFitter.fit_multi_method`（多求解器）

---

### 拟合方法选择流程

```
开始
  │
  ├─ 双弛豫？
  │    ├─ 是 → 参数数量级相近？
  │    │        ├─ 是 → fit_staged
  │    │        └─ 否 → fit_log_space
  │    │
  │    └─ 否 → 三弛豫+？
  │             ├─ 是 → fit_staged_extended
  │             └─ 否 → 检查其他问题
  │
  └─ 初始值偏离>50%？
       ├─ 是 → fit_multi_start
       └─ 否 → 使用推荐方法
```

---

*测试文件由AI生成，用于验证FittingMT.py模块功能*
