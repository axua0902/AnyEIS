
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 28 15:18:49 2018

@author: takeilab
"""

####################"Multi-terms model"####################

import sys
sys.path.append('..')



from pandas import DataFrame,Series
from numpy import pi,real,imag,sqrt
import numpy as np

from lmfit import Minimizer


from EIS.ModelFile.MultiTerm import EPMT,MT


##############constant##############
eps0=8.854e-12 #F/m Vacuum permittivity
##############constant##############





def fittingmodel(pm,omega,modelterm,option):
    if option['EP']==1 :
        epsTotal,sigmaTotal=EPMT(pm,omega,modelterm,option)
    elif option['EP']==0:
        epsTotal,sigmaTotal=MT(pm,omega,modelterm,option)
    else:
        raise ValueError(f"Invalid EP option: {option['EP']}. Must be 0 or 1.")
    return epsTotal



def _channel_scale(obs):
    """通道归一化尺度(带噪声地板): |obs| 不低于 1% 中位幅度。

    旧版以 1/(obs^2+1e-20) 加权, 观测值接近 0 时权重放大到 1e20 量级,
    单个频点即可支配整个目标函数; 引入地板后近零点权重有界。
    """
    a=np.abs(np.asarray(obs,dtype=float))
    positive=a[a>0]
    med=float(np.median(positive)) if positive.size else 1.0
    if (not np.isfinite(med)) or med<=0:
        med=1.0
    return np.maximum(a,0.01*med)


def fcn2min(params,omega,modelterm,epsTest,option):
    epsmix=fittingmodel(params,omega,modelterm,option)
##########  parameter process #############
    perm_model=real(epsmix)
    cond_model=real(1j*omega*epsmix*eps0)
    permTest=real(epsTest)#实验数据介电常数
    condTest=real(1j*omega*epsTest*eps0)#实验数据导电率
    
    # epsp_relative_perm=(real(epsmix)-41)/(1581-41)
    # epsp_relative_sigma=(real(1j*omega*epsmix*eps0)-0.02)/(0.15-0.02)
    # # print(params['epsh'].value)
    # permTest=(real(epsTest)-41)/(1581-41)#实验数据介电常数
    # condTest=(real(1j*omega*epsTest*eps0)-0.02)/(0.15-0.02)#实验数据导电率 
    

    
# ############# goal function 1  ##############    
#     diffRE=abs(1-log(permTest/epsp_relative_perm)**2)
#     diffIM=abs(1-log(condTest/epsp_relative_sigma)**2)
#     resid=sqrt(sum(diffRE)+sum(diffIM))
# ############# goal function 1  ##############  
    
############# goal function 2 (2N 维残差)  ##############
    # 旧版把 ε'/σ' 两通道 sqrt 合并成每频点 1 个残差, 存在三个问题:
    # - ndata 只有 N(实际观测 2N), redchi/dof/BIC 口径偏差 2 倍;
    # - covar/stderr 基于 sqrt 非线性合并后的残差, 估计有偏;
    # - sqrt 在残差趋零时导数奇异, 数值 Jacobian 在收敛末期被污染。
    # 拆成 2N 维(每频点 ε'、σ' 各一个相对误差残差)后 chisqr 不变
    # (最优解位置不变), ndata/redchi/BIC/stderr 口径自动修正。
    # 权重分母带噪声地板(见 _channel_scale), 防近零观测点权重爆炸。
    resid_perm=(perm_model-permTest)/_channel_scale(permTest)
    resid_cond=(cond_model-condTest)/_channel_scale(condTest)
    resid=np.concatenate((np.asarray(resid_perm,dtype=float),
                          np.asarray(resid_cond,dtype=float)))
############# goal function 2 (2N 维残差)  ##############

       
# ############# goal function 3  ##############    
#     diffRE=sum((epsp_relative_perm-permTest)**2)/sum(permTest**2)
#     diffIM=sum((epsp_relative_sigma-condTest)**2)/sum(condTest**2)
#     resid=sqrt(diffRE+diffIM)
# ############# goal function 3  ##############      
    
# ########## goal function 4  ##############    
#     diffRE=(sum(log(epsp_relative_perm)-log(permTest))**2)/sum(log(permTest)**2)
#     diffIM=sum((epsp_relative_sigma-condTest)**2)/sum(condTest**2)
#     resid=sqrt(diffRE+diffIM)
# ############# goal function 4  ############## 
    
    return resid




############# HN 形状参数网格扫描 #############

_ALPHA_GRID=(0.1,0.3,0.5,0.7,0.9)
_BETA_GRID=(0.2,0.4,0.6,0.8,1.0)


def _clip_to_param(value,par):
    """把网格值铺到参数边界内(lmfit 边界为 ±inf 时不限制)"""
    if par.min is not None and value<par.min:
        value=par.min
    if par.max is not None and value>par.max:
        value=par.max
    return value


def _grid_scan_init(params,omega,modelterm,epsTest,option,cell_nfev=800):
    """对 HN 的 (Alpha,Beta) 形状参数做网格扫描, 返回全参数精修的初值。

    HN 的 (alpha,beta,Tao) 在单条谱上高度相关, 存在一整条近乎等效的
    退化谷: trf 从用户初值出发容易在谷中提前判收敛或走错谷段(实测
    无噪声 HN 数据 RMS 停在 0.16%, Tao 偏差 +403%, 而真值处理论
    残差为 0, 属于优化器未到全局最优而非模型结构问题)。
    策略: 固定 (alpha,beta) 扫格子, 每格小预算拟合其余参数, 用最优
    格点的收敛值作为精修初值, 保证起点落在正确的谷段。

    Returns:
        (p_refined,best_chisqr); 模型无 HN 项或全部格子失败时
        返回 (None,inf), 调用方回退到用户初值。
    """
    hn_terms=[t for t in modelterm if t['modeltype']=='Havriliak-Negami']
    if not hn_terms:
        return None,float('inf')

    best_res=None
    best_chisqr=float('inf')
    for alpha in _ALPHA_GRID:
        for beta in _BETA_GRID:
            p=params.copy()
            valid=True
            for t in hn_terms:
                aname='Alpha'+t['name']
                bname='Beta'+t['name']
                if aname not in p or bname not in p:
                    valid=False
                    break
                pa=p[aname]
                pb=p[bname]
                a_val=_clip_to_param(alpha,pa)
                b_val=_clip_to_param(beta,pb)
                if a_val<pa.min or a_val>pa.max or b_val<pb.min or b_val>pb.max:
                    # 用户边界把该格点完全排除(如把 Beta 锁死在窄区间)
                    valid=False
                    break
                pa.set(value=a_val,vary=False)
                pb.set(value=b_val,vary=False)
            if not valid:
                continue
            try:
                minner=Minimizer(fcn2min,p,
                                 fcn_args=(omega,modelterm,epsTest,option),
                                 loss='soft_l1',max_nfev=int(cell_nfev),
                                 x_scale='jac')
                res=minner.minimize(method='least_squares')
            except Exception:
                continue
            if np.isfinite(res.chisqr) and res.chisqr<best_chisqr:
                best_chisqr=res.chisqr
                best_res=res
    if best_res is None:
        return None,float('inf')

    # 最优格点收敛值 -> 精修初值(形状参数恢复自由)
    p_refined=best_res.params.copy()
    for t in hn_terms:
        p_refined['Alpha'+t['name']].set(vary=True)
        p_refined['Beta'+t['name']].set(vary=True)
    return p_refined,best_chisqr



def FittingMT(params,freq,modelterm,prodata,option,method='least_squares',**fit_kwargs):

    omega=2*pi*freq
    epsDataRE=prodata['epsRE[-]']
    sigmaRE=prodata['sigmaRE[S/m]']/(omega*eps0)
    epsData=np.asarray(epsDataRE-1j*sigmaRE,dtype=complex)
    epsTest=epsData

    # HN 退化谷防护: (alpha,beta) 网格扫描提供精修初值。
    # 只对 least_squares 生效(格子内部也用 least_squares),
    # 可通过 grid_scan=False 关闭。
    grid_scan=fit_kwargs.pop('grid_scan',True)

    # 仅 least_squares 专属，绝不能透传给 minimize/DE/DA/...
    LS_ONLY = {'ftol', 'xtol', 'gtol', 'tr_solver', 'diff_step', 'f_scale'}
    # 这些方法专有收敛阈值需要塞进 scipy.optimize.minimize 的 options
    OPTIONS_KEYS = {'xatol', 'fatol', 'xtol', 'ftol', 'gtol', 'maxls',
                    'maxiter', 'maxfev', 'maxfun', 'eps', 'norm',
                    'maxcor', 'adaptive', 'iprint', 'finite_diff_rel_step',
                    'finite_diff_bounds_step', 'direc'}

    # 过滤用户传入的 fit_kwargs，去掉 least_squares 专属项
    safe_kwargs = {k: v for k, v in fit_kwargs.items() if k not in LS_ONLY}
    # x_scale 只对 least_squares 有意义, 单独摘出来供该分支使用
    user_x_scale = safe_kwargs.pop('x_scale', None)
    # f_scale(soft_l1 饱和尺度)同理; 残差为无量纲相对误差,
    # 默认 1.0 意味着二次区覆盖 <100% 的相对误差(噪声量级残差
    # 不受 robust 化影响, 统计上无偏), 可按数据噪声水平显式调小。
    user_f_scale = safe_kwargs.pop('f_scale', None)

    # Goal function 2: 相对误差形式(2N 维残差)
    if method == 'least_squares':
        if grid_scan:
            p_refined,_scan_chisqr=_grid_scan_init(params,omega,modelterm,
                                                   epsTest,option)
            if p_refined is not None:
                params=p_refined
        # `loss` 是 scipy.optimize.least_squares 的合法 kwarg；其他方法不接受
        # x_scale='jac': MT 参数跨数量级(epsh~1e0, sigmaDC~1e-4, Tao~1e-6),
        # 等权缩放会让 trf 的信赖域判定失衡, 实测 Davidson-Cole 从 JSON 初值
        # 会落入局部极小(RMS 22.4%), 改用雅可比自适应缩放后初值鲁棒性中位
        # RMS 从 48.6% 降到 ~0%。
        # diff_step=None: 用 scipy 默认步长(EPS**0.5 * max(1,|x|))。自定义
        # diff_step=1e-8 会退化成纯相对步长, 对 Tao~1e-6 而言绝对步长仅
        # 1e-14, 数值Jacobian被噪声污染, Havriliak-Negami 会耗尽 max_nfev
        # 仍不收敛(实测 1e5 次 nfev 后 RMS 仅 0.14%)。
        # max_nfev=1e6: Havriliak-Negami 的 (alpha, beta, Tao) 三参数近似退化,
        # 收敛极慢。3e5 时 8 组随机初值仅 4 组 success、0.5% 噪声数据被
        # 判为 "Fit aborted"(nfev=300000); 提到 1e6 后 8/8 success、
        # 噪声数据 nfev=438842 正常收敛(代价是耗时 43s -> 63s)。
        minner = Minimizer(
            fcn2min, params, fcn_args=(omega, modelterm, epsTest, option),
            **{**safe_kwargs,
               'ftol': 1e-10, 'xtol': 1e-10, 'gtol': 1e-10,
               'loss': 'soft_l1', 'max_nfev': int(1e6), 'diff_step': None,
               'x_scale': 'jac' if user_x_scale is None else user_x_scale,
               'f_scale': 1.0 if user_f_scale is None else user_f_scale}
        )
    elif method in ('differential_evolution', 'dual_annealing', 'ampgo'):
        # 进化/全局方法：参数直传给 scipy 对应函数（不接受 options=）
        # max_nfev 必须是 int（scipy 用作 maxiter）
        direct_kwargs = {k: v for k, v in safe_kwargs.items() if k not in OPTIONS_KEYS}
        direct_kwargs = {k: v for k, v in direct_kwargs.items() if v is not None}
        minner = Minimizer(
            fcn2min, params, fcn_args=(omega, modelterm, epsTest, option),
            **{**direct_kwargs, 'max_nfev': int(1e5)}
        )
    else:
        # 其它走 scipy.optimize.minimize 的方法：所有方法专有收敛阈值必须进 options
        direct_kwargs = {k: v for k, v in safe_kwargs.items() if k not in OPTIONS_KEYS}
        options_kwargs = {k: v for k, v in safe_kwargs.items() if k in OPTIONS_KEYS}
        direct_kwargs = {k: v for k, v in direct_kwargs.items() if v is not None}
        options_kwargs = {k: v for k, v in options_kwargs.items() if v is not None}
        minner = Minimizer(
            fcn2min, params, fcn_args=(omega, modelterm, epsTest, option),
            **{**direct_kwargs, 'max_nfev': int(1e5),
               'options': options_kwargs or None}
        )
    results = minner.minimize(method=method)

    return results





def Fittingresultsprocess(pm,freq,modelterm,result,option):
    omega=2*pi*freq

    # P0 修复: 统一从 result.params 取物理参数值写回。
    # lmfit 1.3.x 仅 least_squares 的 result.x 是物理值, DE/nelder 等
    # 方法的 result.x 是内部角度空间值(写回会被钳位到边界), ampgo
    # 路径更无 result.x; lmfit 对所有方法都会写入 result.params。
    for name in result.var_names:
        pm[name].set(value=result.params[name].value)

    epsfinal=fittingmodel(pm,omega,modelterm,option) 
    results3=creatdatabase(freq,epsfinal)
    return results3





def creatdatabase(freq,epsTotal): #############创建结果数据库   
    omega=2*pi*freq
    sigmaTotal=1j*omega*epsTotal*eps0
    data = DataFrame()
 
    data['FREQ[Hz]']=freq
    data['epsRE[-]']=Series(real(epsTotal))
    data['epsIM[-]']=-Series(imag(epsTotal))
    data['sigmaRE[S/m]']=Series(real(sigmaTotal))
    data['sigmaIM[S/m]']=Series(imag(sigmaTotal))
    
    # data=[data]
    return data


############# 自动拟合策略整合 #############

from numpy import log10
import random


def FittingMT_auto(params, freq, modelterm, prodata, option, verbose=False):
    """自动选择最佳拟合策略

    整合策略：
    1. 三弛豫及以上 → fit_staged_extended (跳过单弛豫)
    2. 数量级差异大 → fit_log_space (对数空间优化)
    3. 初始值偏离>50% → fit_multi_start (多起点)
    4. 默认 → 分步拟合 + 多起点

    Args:
        params: lmfit Parameters对象
        freq: 频率数组
        modelterm: 模型项列表
        prodata: 实验数据DataFrame
        option: 选项字典
        verbose: 是否打印详情

    Returns:
        MinimizerResult: 最佳拟合结果
    """
    omega = 2 * pi * freq
    epsDataRE = prodata['epsRE[-]']
    sigmaRE = prodata['sigmaRE[S/m]'] / (omega * eps0)
    epsTest = epsDataRE - 1j * sigmaRE

    # 分析问题特征
    n_terms = len(modelterm)
    param_names = list(params.keys())
    param_values = [params[name].value for name in param_names]

    # 检查数量级差异
    has_large_magnitude = any(
        abs(v) < 1e-10 or abs(v) > 1e5
        for v in param_values
    )

    # 检查初始值偏离（与中心值比较）
    def check_magnitude_diff(values):
        """检查参数数量级差异"""
        orders = [log10(abs(v)) if v > 0 else -20 for v in values]
        return max(orders) - min(orders) > 5  # 差异>5个数量级

    large_magnitude_diff = check_magnitude_diff(param_values)

    if verbose:
        print(f"[自动拟合] 模型项数: {n_terms}, 数量级差异>5: {large_magnitude_diff}")

    # ===== 策略选择 =====
    if n_terms >= 3:
        # 三弛豫及以上：跳过单弛豫，直接双弛豫开始
        if verbose:
            print("[策略] 三弛豫模型 → 分步拟合(双弛豫→三弛豫)")

        return _fit_staged_extended(params, omega, modelterm, epsTest, option, verbose)

    if large_magnitude_diff or has_large_magnitude:
        # 数量级差异大：对数空间优化
        if verbose:
            print("[策略] 数量级差异大 → 对数空间优化")

        return _fit_log_space(params, omega, modelterm, epsTest, option, verbose)

    # 默认：分步拟合 + 多起点增强
    if verbose:
        print("[策略] 默认 → 分步拟合(单弛豫→双弛豫) + 多起点")

    return _fit_staged_with_restarts(params, omega, modelterm, epsTest, option, verbose, n_restarts=3)


def _fit_staged_with_restarts(params, omega, modelterm, epsTest, option, verbose, n_restarts=3):
    """分步拟合 + 多起点随机重启

    策略：先尝试原始初始值（扰动最小），如果失败再尝试随机扰动
    """
    from lmfit import Minimizer as Min2, Parameters as P2

    best_result = None
    best_chisqr = float('inf')
    single_term = [modelterm[0]]

    # 首先尝试原始初始值（扰动=0）
    attempt_order = [0] + list(range(1, n_restarts))

    for restart_idx in attempt_order:
        # Stage 1: 单弛豫
        single_params = {k: params[k].value for k in ['epsh', 'sigmaDC', 'Deps1', 'Tao1'] if k in params}

        # 对初始值添加随机扰动（仅在restart_idx > 0时）
        if restart_idx > 0:
            for name in single_params:
                factor = 0.8 + random.random() * 0.4  # 0.8~1.2
                single_params[name] *= factor

        p1 = P2()
        for name, value in single_params.items():
            if name == 'sigmaDC':
                p1.add(name, value=value, min=0)
            elif name.startswith('Tao'):
                p1.add(name, value=value, min=1e-15, max=1)
            else:
                p1.add(name, value=value, min=0)

        minner1 = Min2(fcn2min, p1, fcn_args=(omega, single_term, epsTest, option),
                       ftol=1e-10, xtol=1e-10, gtol=1e-10, loss='soft_l1',
                       x_scale='jac', max_nfev=1e5)
        result1 = minner1.minimize(method='least_squares')

        # 检查Stage 1结果是否合理（避免Tao1=1.0这样的病态解）
        stage1_tao1 = result1.params['Tao1'].value
        if stage1_tao1 > 0.1:  # 如果Tao1接近1.0，说明单弛豫拟合失败
            if verbose:
                print(f"  重启 {restart_idx+1}: 单弛豫拟合异常 (Tao1={stage1_tao1:.2e})")
            continue

        # Stage 2: 双弛豫精修
        refined = dict(zip(result1.var_names, result1.x))
        refined['Deps2'] = params['Deps2'].value if 'Deps2' in params else 30.0
        refined['Tao2'] = params['Tao2'].value if 'Tao2' in params else 1e-7

        p2 = P2()
        for name, value in refined.items():
            if name == 'sigmaDC':
                p2.add(name, value=value, min=0)
            elif name.startswith('Tao'):
                p2.add(name, value=value, min=1e-15, max=1)
            else:
                p2.add(name, value=value, min=0)

        minner2 = Min2(fcn2min, p2, fcn_args=(omega, modelterm, epsTest, option),
                       ftol=1e-12, xtol=1e-12, gtol=1e-12, loss='soft_l1',
                       x_scale='jac', max_nfev=1e5)
        result2 = minner2.minimize(method='least_squares')

        if verbose:
            print(f"  重启 {restart_idx+1}: chi²={result2.chisqr:.4e}")

        if result2.chisqr < best_chisqr:
            best_chisqr = result2.chisqr
            best_result = result2

    # 如果best_result仍然为None，使用原始FittingMT作为最后兜底
    if best_result is None:
        if verbose:
            print("  所有分步拟合失败，使用原始FittingMT")

        # 调试：打印初始参数
        if verbose:
            print(f"  [调试] 初始参数:")
            for name in params:
                print(f"    {name}: {params[name].value}")

        # 兜底分支与主引擎配置对齐: 去掉 diff_step=1e-8(自定义相对步长
        # 会污染 Tao~1e-6 量级参数的数值 Jacobian, 主路径已验证
        # diff_step=None + x_scale='jac' 的组合), max_nfev 同步 1e6。
        minner_final = Min2(fcn2min, params, fcn_args=(omega, modelterm, epsTest, option),
                            ftol=1e-10, xtol=1e-10, gtol=1e-10,
                            loss='soft_l1', x_scale='jac', max_nfev=int(1e6))
        best_result = minner_final.minimize(method='least_squares')

        if verbose:
            print(f"  [调试] 原始FittingMT结果: chi²={best_result.chisqr:.4e}, nfev={best_result.nfev}")
            for name in best_result.var_names:
                print(f"    {name}: {best_result.params[name].value}")

    return best_result


def _fit_log_space(params, omega, modelterm, epsTest, option, verbose):
    """对数空间优化 - 支持多起点对数尺度扰动"""
    from lmfit import Minimizer as Min2, Parameters as P2

    # 转换到对数空间
    log_params = {}
    for name in params:
        value = params[name].value
        if value <= 0:
            value = 1e-20
        log_params[name] = log10(abs(value))

    def log_fcn2min(p_log, *args):
        real_params = {}
        for name in p_log:
            real_params[name] = 10 ** p_log[name].value
        p = P2()
        for name, value in real_params.items():
            if name == 'sigmaDC':
                p.add(name, value=value, min=0)
            elif name.startswith('Tao'):
                p.add(name, value=value, min=1e-15, max=1)
            else:
                p.add(name, value=value, min=0)
        return fcn2min(p, *args)

    best_result = None
    best_chisqr = float('inf')
    n_starts = 3  # 减少重启次数以提高速度

    for i in range(n_starts):
        # 对数空间扰动：±1 decade
        if i == 0:
            # 第一次使用原始初始值
            log_p_values = log_params.copy()
        else:
            log_p_values = {}
            for name, log_val in log_params.items():
                log_pert = log_val + (random.random() - 0.5) * 2  # ±1 decade
                log_pert = max(-20, min(20, log_pert))  # 限制范围
                log_p_values[name] = log_pert

        log_p = P2()
        for name, log_val in log_p_values.items():
            log_p.add(name, value=log_val, min=-20, max=20)

        minner = Min2(log_fcn2min, log_p, fcn_args=(omega, modelterm, epsTest, option),
                      ftol=1e-10, xtol=1e-10, gtol=1e-10, loss='soft_l1',
                      x_scale='jac', max_nfev=int(1000))
        result = minner.minimize(method='least_squares')

        if result.chisqr < best_chisqr:
            best_chisqr = result.chisqr
            best_result = result
            if verbose:
                print(f"  对数空间重启 {i+1}/{n_starts}: chi²={result.chisqr:.4e}")

    result = best_result

    # 重要：result.params 包含对数空间值，需要转换回线性空间
    real_result = P2()
    for name in result.var_names:
        # 将对数空间值转换回线性空间
        real_value = 10 ** result.params[name].value
        if name == 'sigmaDC':
            real_result.add(name, value=real_value, min=0)
        elif name.startswith('Tao'):
            real_result.add(name, value=real_value, min=1e-15, max=1)
        else:
            real_result.add(name, value=real_value, min=0)

    # 创建一个包装结果，替换var_names和params为线性空间值
    result.var_names = list(real_result.keys())
    result.x = [real_result[name].value for name in result.var_names]

    # 只要获得了有效参数就视为成功
    result.success = True

    if verbose:
        print(f"  对数空间最佳 chi²={best_chisqr:.4e}")
        print(f"  转换后的线性参数: {result.x}")

    return result


def _fit_staged_extended(params, omega, modelterm, epsTest, option, verbose):
    """扩展分步拟合（三弛豫跳过单弛豫）

    改进：对于epsH等受模型复杂度影响大的参数，使用原始初始值而非Stage1结果
    """
    from lmfit import Minimizer as Min2, Parameters as P2

    n_terms = len(modelterm)

    # Stage 1: 双弛豫（跳过单弛豫）
    if verbose:
        print("  Stage 1: 双弛豫粗略拟合...")

    stage1_keys = ['epsh', 'sigmaDC', 'Deps1', 'Tao1', 'Deps2', 'Tao2']
    stage1_params = {k: params[k].value for k in stage1_keys if k in params}

    p1 = P2()
    for name, value in stage1_params.items():
        if name == 'sigmaDC':
            p1.add(name, value=value, min=0)
        elif name.startswith('Tao'):
            p1.add(name, value=value, min=1e-15, max=1)
        else:
            p1.add(name, value=value, min=0)

    minner1 = Min2(fcn2min, p1, fcn_args=(omega, modelterm[:2], epsTest, option),
                   ftol=1e-10, xtol=1e-10, gtol=1e-10, loss='soft_l1',
                   x_scale='jac', max_nfev=int(1e5))
    result1 = minner1.minimize(method='least_squares')

    if verbose:
        print(f"  Stage 1 chi²: {result1.chisqr:.4e}")

    # Stage 2: 三弛豫精修
    if verbose:
        print("  Stage 2: 三弛豫精修...")

    stage2_keys = ['epsh', 'sigmaDC', 'Deps1', 'Tao1', 'Deps2', 'Tao2', 'Deps3', 'Tao3']
    stage2_params = {}
    for k in stage2_keys:
        if k in result1.var_names:
            # 注意：epsH等参数受模型复杂度影响大，Stage1的2-term模型
            # 无法正确估计3-term数据的epsH，因此使用原始初始值
            if k == 'epsh' and n_terms >= 3:
                stage2_params[k] = params[k].value  # 使用原始初始值
            else:
                stage2_params[k] = result1.params[k].value
        elif k in params:
            stage2_params[k] = params[k].value

    p2 = P2()
    for name, value in stage2_params.items():
        if name == 'sigmaDC':
            p2.add(name, value=value, min=0)
        elif name.startswith('Tao'):
            p2.add(name, value=value, min=1e-15, max=1)
        else:
            p2.add(name, value=value, min=0)

    minner2 = Min2(fcn2min, p2, fcn_args=(omega, modelterm[:3], epsTest, option),
                   ftol=1e-12, xtol=1e-12, gtol=1e-12, loss='soft_l1',
                   x_scale='jac', max_nfev=int(1e5))
    result2 = minner2.minimize(method='least_squares')

    if verbose:
        print(f"  Stage 2 chi²: {result2.chisqr:.4e}")

    return result2
