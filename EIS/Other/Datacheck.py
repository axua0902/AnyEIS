"""
Data Validation Functions for EIS/DS Analysis
EIS/DS分析数据验证函数

Data Structure Analysis / 数据结构分析:
Based on the validation functions, the expected data structures are:
根据验证函数分析，预期的数据结构如下：

1. Main Data Lists / 主要数据列表:
   - selectlist: List of selection flags/indices (1=selected, 0=not selected) / 选择标志/索引列表(1=已选择,0=未选择）
     Example / 示例: [1, 1, 1, 1, 1]
   
   - prodataname: List of processing data names / 处理数据名称列表  
     Example / 示例: ['name1', 'name2', 'name3', 'name4', 'name5']
   
   - prodata: List of pandas DataFrames containing processing data / 包含处理数据的pandas DataFrame列表
     Example / 示例: Each DataFrame contains EIS measurement data with columns:
     每个DataFrame包含EIS/DS测量数据,列包括：
     * FREQ[Hz]: Frequency in Hz / 频率（赫兹）
     * Z[ohm]: Impedance magnitude in ohms / 阻抗幅值（欧姆）
     * PHASE[deg]: Phase angle in degrees / 相位角（度）
     * Rs[ohm]: Series resistance in ohms / 串联电阻（欧姆）
     * X[ohm]: Reactance in ohms / 电抗（欧姆）
     Typical size: 200 rows x 5 columns / 典型尺寸:200行x5列
   
   - refdata: List of pandas DataFrames containing reference data / 包含参考数据的pandas DataFrame列表
     Same structure as prodata, used for comparison / 与prodata结构相同,用于比较
   
   - dataInfo: Additional data information list (can be empty) / 附加数据信息列表（可为空）
     Example / 示例: []
     
        print(self.selectlist)
        [1, 1, 1, 1, 1]

        print(self.prodataname)
        ['name1', 'name2', 'name3', 'name4', 'name5']

        print(self.prodata)
        [       FREQ[Hz]    Z[ohm]  PHASE[deg]   Rs[ohm]    X[ohm]
        0       1000000  131.3670      -6.152  130.6110  -14.0793
        1       1000000  131.3790      -6.145  130.6240  -14.0628
        2       1100000  130.4170      -6.520  129.5740  -14.8085
        ..          ...       ...         ...       ...       ...
        198  2881700000  115.5250     -77.610   24.7885 -112.8340
        199  3000000000  126.9770     -78.427   25.4741 -124.3950
            [200 rows x 5 columns],

        print(self.refdata)
        [       FREQ[Hz]    Z[ohm]  PHASE[deg]   Rs[ohm]    X[ohm]
        0       1000000  138.3640      -8.027  137.0080  -19.3210
        1       1000000  138.3790      -8.016  137.0270  -19.2976
        2       1100000  136.9670      -8.388  135.5020  -19.9791
        ..          ...       ...         ...       ...       ...
        198  2881700000  116.7160     -77.330   25.5997 -113.8740
        199  3000000000  128.3470     -78.126   26.4084 -125.6010
            [200 rows x 5 columns],

        print(self.dataInfo)
        []  

2. Data Format / 数据格式:
   - Each DataFrame has .shape attribute (rows, columns) / 每个DataFrame具有.shape属性(行数,列数）
     Example / 示例: (200, 5) - 200 data points with 5 measurement parameters
   - Each DataFrame has .columns attribute for column names / 每个DataFrame具有.columns属性用于列名
     Example / 示例: ['FREQ[Hz]', 'Z[ohm]', 'PHASE[deg]', 'Rs[ohm]', 'X[ohm]']
   - All DataFrames in the same list should have consistent dimensions / 同一列表中的所有DataFrame应具有一致的维度
   - Frequency range typically spans from 1MHz to 3GHz / 频率范围通常从1MHz到3GHz
   - Data contains both low and high frequency measurements / 数据包含低频和高频测量

3. EIS Data Columns / EIS数据列:
   - Frequency: FREQ[Hz] - Measurement frequency / 测量频率
   - Impedance: Z, absZ, Z[ohm], Z[OHM], Z[Ω] - Impedance magnitude / 阻抗幅值
   - Phase: PHASE, PHASE[deg], PHASE[DEG], ph - Phase angle (typically negative) / 相位角（通常为负值）
   - Resistance: Rs, Rs[ohm], RS[OHM], Rs[Ω], R -  resistance / 阻抗实部，电阻
   - Reactance: X, X[ohm], X[OHM], X[Ω] - Reactance (typically negative for capacitive) /阻抗虚部， 电抗（电容性通常为负值）

4. DS (Dielectric Spectroscopy) Data Columns / DS(介电谱)数据列:
   - Real Permittivity: PERMITTIVITY RE, EPSILON RE, EPS RE, epsRE[-] / 实部介电常数
   - Imaginary Permittivity: PERMITTIVITY IM, EPSILON IM, EPS IM, epsIM[-] / 虚部介电常数  
   - Real Conductivity: CONDUCTIVITY RE, SIGMA RE, SIG RE, sigmaRE[S/m] / 实部电导率
   - Imaginary Conductivity: CONDUCTIVITY IM, SIGMA IM, SIG IM, sigmaIM[S/m] / 虚部电导率

5. Validation Rules / 验证规则:
   - All related lists must have equal lengths / 所有相关列表必须具有相等的长度
     Example / 示例: len(selectlist) = len(prodataname) = len(prodata) = 5
   - All DataFrames in a list must have same row count / 列表中所有DataFrame必须具有相同的行数
     Example / 示例: All DataFrames have 200 rows / 所有DataFrame都有200行
   - All DataFrames in a list must have same column count / 列表中所有DataFrame必须具有相同的列数
     Example / 示例: All DataFrames have 5 columns / 所有DataFrame都有5列
   - Processing data and reference data must have compatible dimensions / 处理数据和参考数据必须具有兼容的维度

"""

##################################数据检查#############################
def check1(selectlist, prodataname, prodata):  # 全部输入数据检查
    if len(selectlist) == len(prodataname) and len(prodataname) == len(prodata):
        return 1
    else:
        print('Data Check Error')  ##输出到状态栏
        return 0

def check2(prodata):  # 输入数据内部检查
    if len(prodata) > 0:
        rownumtot = prodata[0].shape[0]  ##数据总行数
        colnumtot = prodata[0].shape[1]  ##数据总列数
        for numtemp in range(1, len(prodata)):
            if rownumtot != prodata[numtemp].shape[0]:  ##数据总行数
                print('Data Error please check row number of data')  ##输出到状态栏
                return 0
            else:
                print('check2 pass')
                return 1
        for numtemp in range(1, len(prodata)):
            if colnumtot != prodata[numtemp].shape[1]:  ##数据总列数
                print('Data Error please check colnum number of data')  ##输出到状态栏
                return 0
            else:
                print('check2 pass')
                return 1
    else:
        print('No data Input')
        return 1

def check3(data, namelist):  # 参考数据之间检查
    print(namelist, len(data))
    if namelist[0] == 'empty':
        return 1
    else:
        if len(data) > 0:
            rownumtot = data[0].shape[0]  ##数据总行数
            colnumtot = data[0].shape[1]  ##数据总列数
            for numtemp in range(0, len(data)):
                if rownumtot != data[numtemp].shape[0]:  ##数据总行数
                    print('Data Error please check row number of data')  ##输出到状态栏
                    return 0
                else:
                    print('check3 pass')
                    return 1
            for numtemp in range(1, len(data)):
                if colnumtot != data[numtemp].shape[1]:  ##数据总列数
                    print('Data Error please check colnum number of data')  ##输出到状态栏
                    return 0
                else:
                    print('check3 pass')
                    return 1
        else:
            print('No data Input')
            return 1

def check4(prodata, refdata):  # 参考数据与输入数据比较检查
    prodataRownumtot = list()
    refdataRownumtot = list()
    prodataColnumtot = list()
    refdataColnumtot = list()

    for i in range(0, len(prodata)):
        prodataRownumtot.append(prodata[i].shape[0])
        prodataColnumtot.append(prodata[i].shape[1])

    for i in range(0, len(refdata)):
        refdataRownumtot.append(refdata[i].shape[0])
        refdataColnumtot.append(refdata[i].shape[1])

    a = [x for x in prodataRownumtot if x in refdataRownumtot]
    b = [y for y in (prodataRownumtot + refdataRownumtot) if y not in a]

    a1 = [x for x in prodataColnumtot if x in refdataColnumtot]
    b1 = [y for y in (prodataColnumtot + refdataColnumtot) if y not in a1]

    if len(b) != 0:
        print('prodata and refdata error please check colnum number of data')
        return 0
    elif len(b1) != 0:
        print('prodata and refdata error please check colnum number of data')
        return 0
    else:
        print('check4 pass')
        return 1


def resolve_column(df, candidates, default=None):
    """
    在 DataFrame 的列名中查找第一个匹配候选名的列(大小写不敏感、首尾空白不敏感)。
    用于容忍不同数据源列名变体(如 'Rs[ohm]' / 'RS[OHM]' / 'Rs' / 'Rs[Ω]')。

    Args:
        df: pandas DataFrame
        candidates: 候选列名列表,按优先级排列
        default: 所有候选都未匹配时返回的默认值(默认 None)

    Returns:
        匹配到的列名(原样,大小写与 DataFrame 实际列名一致),未找到则返回 default
    """
    if df is None or not hasattr(df, 'columns'):
        return default
    # 标准化:去空白 + 统一小写
    col_lookup = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        key = str(cand).strip().lower()
        if key in col_lookup:
            return col_lookup[key]
    return default


def check5(data):  #判断数据类型
    """判断输入数据是EIS数据还是DS数据"""
    if not data or len(data) == 0:
        return 'UNKNOWN'
    
    # EIS和DS数据的特征列名
    eis_columns = {
        'Z': ['Z', 'absZ', 'Z[ohm]', 'Z[OHM]', 'Z[Ω]'],
        'PHASE': ['PHASE', 'PHASE[deg]', 'PHASE[DEG]', 'ph'],
        'Rs': ['Rs', 'Rs[ohm]', 'RS[OHM]', 'Rs[Ω]', 'R'],
        'X': ['X', 'X[ohm]', 'X[OHM]', 'X[Ω]']
    }
    
    ds_columns = {
        'epsRE': ['PERMITTIVITY RE', 'EPSILON RE', 'EPS RE','EPS RE[-]', 'PERMITTIVITYRE', 'EPSILONRE', 'EPSRE', 'epsRE[-]','EpsRE[-]'],
        'epsIM': ['PERMITTIVITY IM', 'EPSILON IM', 'EPS IM','EPS IM[-]', 'PERMITTIVITYIM', 'EPSILONIM', 'EPSIM', 'epsIM[-]','EpsIM[-]'],
        'sigmaRE': ['CONDUCTIVITY RE', 'SIGMA RE', 'SIG RE','SIGMA RE[S/m]', 'CONDUCTIVITYRE', 'SIGMARE', 'SIGRE', 'sigmaRE[S/m]'],
        'sigmaIM': ['CONDUCTIVITY IM', 'SIGMA IM', 'SIG IM','SIGMA IM[S/m]', 'CONDUCTIVITYIM', 'SIGMAIM', 'SIGIM', 'sigmaIM[S/m]']
    }
    
    # 获取列名
    if not hasattr(data[0], 'columns'):
        return 'UNKNOWN'
    column_names = [str(col).strip() for col in data[0].columns]
    
    # 检查匹配的特征列
    def check_match(col_name, name_list):
        return col_name in name_list or col_name.upper() in [name.upper() for name in name_list]
    
    eis_matches = sum(1 for key, names in eis_columns.items() 
                        if any(check_match(col, names) for col in column_names))
    
    ds_matches = sum(1 for key, names in ds_columns.items() 
                    if any(check_match(col, names) for col in column_names))
    
    # 判断数据类型
    if eis_matches >= 2:
        return 'EIS'
    elif ds_matches >= 2:
        return 'DS'
    else:
        return 'UNKNOWN'

def check6_freq_consistency(prodata, refdata, rtol_log=1e-3):
    """
    Check if prodata and refdata have approximately consistent frequency points.

    For logarithmic frequency distributions (typical for EIS), exact equality
    is too strict because different data sources may keep different numbers
    of decimal places. This check uses a relative tolerance in log space:
        max|log10(f_pro) - log10(f_ref)| <= rtol_log

    Default rtol_log = 1e-3 means the relative frequency difference
    is allowed up to ~0.23% (10^0.001 ≈ 1.0023).

    Returns:
        1: frequencies are consistent (within tolerance)
        0: frequencies are inconsistent (with details printed)
    """
    # [TP-003] 频率一致性检查(对数空间相对容差)
    import numpy as np
    if not prodata or not refdata:
        return 1  # 无数据时跳过

    if 'FREQ[Hz]' not in prodata[0].columns or 'FREQ[Hz]' not in refdata[0].columns:
        print('FREQ[Hz] column not found, skip check6')
        return 1

    pro_freq = prodata[0]['FREQ[Hz]'].values
    ref_freq = refdata[0]['FREQ[Hz]'].values

    # 长度必须一致
    if len(pro_freq) != len(ref_freq):
        print(f'check6 fail: frequency length mismatch '
              f'(pro={len(pro_freq)}, ref={len(ref_freq)})')
        return 0

    # 排除 f = 0 (DC) 避免 log10 报错
    pro_pos = pro_freq[pro_freq > 0]
    ref_pos = ref_freq[ref_freq > 0]
    if len(pro_pos) != len(ref_pos):
        print(f'check6 fail: non-DC frequency count mismatch '
              f'(pro={len(pro_pos)}, ref={len(ref_pos)})')
        return 0

    # 对数空间相对误差
    log_diff = np.abs(np.log10(pro_pos) - np.log10(ref_pos))
    max_log_diff = float(np.max(log_diff))
    if max_log_diff > rtol_log:
        print(f'check6 fail: frequency log-space diff {max_log_diff:.4e} '
              f'> tolerance {rtol_log}')
        return 0

    print('check6 (freq consistency) pass')
    return 1

##################################数据检查#############################


def detect_data_type_from_columns(plotdata, message=None):
    """
    Inspect plotdata columns to determine whether the data is EIS (Z / Phase /
    Rs / X) or DS (Epsilon / Sigma). Reuses resolve_column for the case /
    whitespace tolerant matching used elsewhere in this module.

    Priority:
    1. Processed entries (odd indices whose dataInfo has process_applied=True)
       — these represent the actual output of a processing module and reflect
       the type the user wants to chart.
    2. Fallback to any available entry — for unprocessed Input / Simulation
       data where no processing has been applied yet.

    Args:
        plotdata: list of pandas DataFrame.
        message:  optional list of dict (dataInfo). When provided, processed
                  entries are detected via the 'process_applied' flag.

    Returns:
        'EIS' | 'DS' | 'UNKNOWN'
    """
    if not plotdata:
        return 'UNKNOWN'

    # Feature column candidates (reuse resolve_column for tolerant matching)
    eis_cols = ('Rs[ohm]', 'X[ohm]', 'Z[ohm]')
    ds_cols = ('EpsRE[-]', 'EpsIM[-]', 'SigmaRE[S/m]', 'SigmaIM[S/m]')

    def _has_any(df, cols):
        return any(resolve_column(df, [c]) is not None for c in cols)

    def _classify(df):
        if _has_any(df, ds_cols):
            return 'DS'
        if _has_any(df, eis_cols):
            return 'EIS'
        return None

    # 1. Prefer processed entries (odd indices + process_applied flag)
    # 约定:偶数索引是"原始"侧,奇数索引是"处理后/合成"侧,process_applied=True
    # 只在处理后侧标。保持只扫奇数位以文档化这一约定,避免未来误用(若
    # process_applied 误标在偶数位,会 fall through 到 fallback,行为更安全)。
    if message and len(message) == len(plotdata):
        for i in range(1, len(plotdata), 2):
            info = message[i]
            if isinstance(info, dict) and info.get('process_applied', False):
                result = _classify(plotdata[i])
                if result is not None:
                    return result

    # 2. Fallback: any available entry (handles raw Input / Simulation data)
    for df in plotdata:
        result = _classify(df)
        if result is not None:
            return result

    return 'UNKNOWN'


##################################方法数据要求#############################
# 集中描述每个方法对数据的要求。
# 字段:
#   refdata_types:  list[str]  refdata 必须是其中一种类型
#   prodata_types:  list[str]  prodata 必须是其中一种类型
#   freq_consistency: bool     是否需要 ref/prodata 频率一致(触发 check6)
#   required_params: list[str] 必需的 processing_parameters 字段名
# 新增方法: 只需在此 dict 加 1 个 entry,无需修改 validate_method_prereq。
METHOD_DATA_SPECS = {
    'Parallel Plate Capacitor': {
        'prodata_types': ['EIS', 'DS'],
    },
    'System Calibration': {
        'refdata_types': ['EIS'],
    },
    'Dielectric Material Method': {
        'refdata_types': ['EIS'],
        'freq_consistency': True,  # 触发 check6
    },
    'Three-Solution Method': {
        'refdata_types': ['EIS'],
    },
    'RF Impedance Calibration': {
        'refdata_types': ['EIS'],
        'prodata_types': ['EIS'],
    },
    'RF Dielectric Calculation': {
        'prodata_types': ['EIS'],
    },
    'RF Impedance Calculation': {
        'prodata_types': ['DS'],
    },
    'K-K for EIS': {
        'required_params': ['validation_parameter'],
    },
}


def validate_method_prereq(method_name, refdata, refdataname, prodata,
                           params_info=None):
    """
    统一校验方法的前置条件,返回 (is_valid, error_messages: list[str])。
    一次报告所有问题,不再"按一次发现一个"。

    不识别的方法返回 (True, [])(向后兼容:旧代码用 else: return 静默)。

    调用方负责把 errors 列表展示给用户(QMessageBox.warning)。
    """
    spec = METHOD_DATA_SPECS.get(method_name)
    if not spec:
        return True, []
    errors = []

    if spec.get('refdata_types'):
        if check3(refdata, refdataname) != 1:
            errors.append(
                f"Reference data count invalid: need 1 valid ref, "
                f"got {len(refdata)} ({refdataname})"
            )
        else:
            ref_type = check5(refdata)
            if ref_type not in spec['refdata_types']:
                errors.append(
                    f"Reference data type is {ref_type}, "
                    f"need {spec['refdata_types']}"
                )

    if spec.get('prodata_types'):
        pro_type = check5(prodata)
        if pro_type not in spec['prodata_types']:
            errors.append(
                f"Processing data type is {pro_type}, "
                f"need {spec['prodata_types']}"
            )

    if spec.get('freq_consistency'):
        if check6_freq_consistency(prodata, refdata) == 0:
            errors.append(
                "Frequency points inconsistent between refdata and prodata"
            )

    for p in spec.get('required_params', []):
        val = (params_info or {}).get('processing_parameters', {}).get(p)
        if not val:
            errors.append(f"Required parameter missing: {p}")

    return len(errors) == 0, errors


##################################成对化工具#############################
def ensure_paired_form(selectlist, plotdataname, plotdata, dataInfo=None):
    """
    数据成对化工具
    让所有上游 sendsignal 输出一致的 [(原始, 合成), ...] 形式,
    下游(Figure/selectsavedata)统一按奇偶索引处理。
    名字保持原样(不加重命名),仅在 dataInfo 的合成侧加 'synthetic': True 标记。

    入参(顺序与下游 emit 保持一致):
        selectlist    : list[int]      0/1 勾选标记
        plotdataname  : list[str]      数据名
        plotdata      : list[DataFrame]  数据
        dataInfo      : list[dict]|None 元信息(可选)

    行为:
        - 已是成对形式(检测到奇数位 dataInfo 含 'synthetic': True)→ 透传
        - 否则:每条复制成 (original, synthetic_copy) 两条,
          合成侧带 'synthetic': True 标记,DataFrame 引用与原始同对象
    """
    if dataInfo is None:
        dataInfo = [{}] * len(plotdata)

    # 关键修复:dataInfo 可能比 plotdata 短(Input 模块始终传空列表)
    # 如果不补齐,zip() 会截断到最短列表长度,导致输出全空
    if len(dataInfo) < len(plotdata):
        dataInfo = list(dataInfo) + [{}] * (len(plotdata) - len(dataInfo))

    # 已是成对形式 → 透传
    if (len(plotdata) > 0
            and len(plotdata) % 2 == 0
            and any(isinstance(info, dict) and info.get('synthetic', False)
                    for info in dataInfo[1::2])):
        # 关键修复:selectlist 可能比 plotdataname 短(fresh() 重置了 selectlist 长度)
        # 透传时也要把 selectlist 复制成对,保持 4 个列表等长
        if len(selectlist) < len(plotdataname):
            paired_selectlist = []
            for flag in selectlist:
                paired_selectlist.append(flag)
                paired_selectlist.append(flag)
            return paired_selectlist, list(plotdataname), list(plotdata), list(dataInfo)
        return list(selectlist), list(plotdataname), list(plotdata), list(dataInfo)

    # 否则:每条复制成 2 条,名字保持原样
    new_selectlist, new_names, new_plots, new_infos = [], [], [], []
    for i, (flag, name, df, info) in enumerate(zip(
            selectlist, plotdataname, plotdata, dataInfo)):
        # 原始侧
        new_selectlist.append(flag)
        new_names.append(name)
        new_plots.append(df)
        new_infos.append(info if isinstance(info, dict) else {})

        # 合成侧(同对象引用,带 synthetic 标记)
        new_selectlist.append(flag)
        new_names.append(name)
        new_plots.append(df)
        synth_info = dict(info) if isinstance(info, dict) else {}
        synth_info['synthetic'] = True
        new_infos.append(synth_info)

    # 调试输出:辅助代码检查(已注释,问题修复后不再需要)
    # print(new_selectlist)
    # print(new_names)
    # print(new_plots)
    # print(new_infos)

    return new_selectlist, new_names, new_plots, new_infos
##################################成对化工具#############################
