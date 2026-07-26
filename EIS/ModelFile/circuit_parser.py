"""
电路字符串解析器
将用户习惯的字符串表示形式转换为 parallel_circuit_drawer.py 中使用的 branches 格式
"""

def parse_element_type(element_name):
    """根据元件名称确定元件类型"""
    if element_name.startswith('R'):
        return 'resistor'
    elif element_name.startswith('C'):
        return 'capacitor'
    elif element_name.startswith('L'):
        return 'inductor'
    else:
        return 'resistor'  # 默认为电阻

def find_matching_bracket(tokens, start_idx):
    """找到匹配的右括号位置"""
    bracket_count = 1
    i = start_idx + 1
    while i < len(tokens) and bracket_count > 0:
        if tokens[i] == 'p(':
            bracket_count += 1
        elif tokens[i] == ')':
            bracket_count -= 1
        i += 1
    return i - 1  # 返回右括号的位置

def parse_series_elements(tokens):
    """解析串联元件序列"""
    elements = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == 'p(':
            # 嵌套并联结构
            end_bracket = find_matching_bracket(tokens, i)
            parallel_content = tokens[i+1:end_bracket]
            parallel_branches = parse_parallel_content(parallel_content)
            parallel_structure = {
                'type': 'parallel',
                'spacing': 1.5,
                'branches': parallel_branches
            }
            elements.append(parallel_structure)
            i = end_bracket + 1
        elif token == '+':
            i += 1  # 跳过加号
        elif token in [',', ')']:
            break  # 遇到逗号或右括号，结束当前串联序列
        else:
            # 普通元件
            element_type = parse_element_type(token)
            element_label = token
            elements.append((element_type, element_label))
            i += 1
    return elements, i

def parse_parallel_content(tokens):
    """解析并联结构内部的内容"""
    branches = []
    i = 0
    
    while i < len(tokens):
        if tokens[i] == ',':
            i += 1
            continue
        
        # 解析一个分支（可能包含串联元件）
        branch_elements, next_i = parse_series_elements(tokens[i:])
        if branch_elements:
            branches.append(branch_elements)
        
        i += next_i
        # 寻找下一个逗号或结束
        while i < len(tokens) and tokens[i] != ',':
            i += 1
    
    return branches

def parse_circuit_string(circuit_tokens):
    """
    将电路字符串标记列表转换为 branches 格式
    
    参数:
    circuit_tokens: 电路表示的标记列表，例如：
                   ['p(','R1',',','C1','+','R2',')']
    
    返回:
    branches: 适用于 parallel_circuit_drawer.py 的分支格式
    """
    # 开始解析
    if not circuit_tokens:
        return []
    
    # 检查是否以并联结构开始
    if circuit_tokens[0] == 'p(':
        # 整个电路是并联结构
        end_bracket = find_matching_bracket(circuit_tokens, 0)
        parallel_content = circuit_tokens[1:end_bracket]
        return parse_parallel_content(parallel_content)
    else:
        # 串联结构或混合结构
        elements, _ = parse_series_elements(circuit_tokens)
        return [elements]  # 包装成单个分支



def get_element_label(element_name):
    """
    根据元件名称生成标签
    
    参数:
    element_name: 元件名称，如 'R1', 'C1', 'L1'
    
    返回:
    元件显示标签
    """
    if element_name.startswith('R'):
        # 电阻：只显示符号
        return element_name
    elif element_name.startswith('C'):
        # 电容：只显示符号
        return element_name
    elif element_name.startswith('L'):
        # 电感：只显示符号
        return element_name
    else:
        return element_name

def parse_tokens_with_labels(tokens, label_generator, start_idx=0):
    """递归解析标记列表（带标签生成器）"""
    result = []
    i = start_idx
    
    while i < len(tokens):
        token = tokens[i]
        
        if token == 'p(':
            # 找到对应的右括号
            j = find_matching_bracket(tokens, i)
            
            # 解析并联结构内部
            parallel_content = tokens[i+1:j]
            parallel_branches = parse_parallel_content_with_labels(parallel_content, label_generator)
            
            # 创建并联结构
            parallel_structure = {
                'type': 'parallel',
                'spacing': 1.5,
                'branches': parallel_branches
            }
            result.append(parallel_structure)
            i = j + 1
            
        elif token == '+':
            i += 1
            
        elif token == ',':
            i += 1
            
        elif token == ')':
            break
            
        else:
            # 普通元件，使用标签生成器
            element_type = parse_element_type(token)
            element_label = label_generator(token)
            result.append((element_type, element_label))
            i += 1
    
    return result, i

def parse_parallel_content_with_labels(tokens, label_generator):
    """解析并联结构内部的内容（带标签生成器）"""
    branches = []
    current_branch = []
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        if token == ',':
            if current_branch:
                branches.append(current_branch)
                current_branch = []
            i += 1
            
        elif token == 'p(':
            j = find_matching_bracket(tokens, i)
            
            nested_content = tokens[i+1:j]
            nested_branches = parse_parallel_content_with_labels(nested_content, label_generator)
            parallel_structure = {
                'type': 'parallel',
                'spacing': 1.2,
                'branches': nested_branches
            }
            current_branch.append(parallel_structure)
            i = j + 1
            
        elif token == '+':
            i += 1
            
        else:
            element_type = parse_element_type(token)
            element_label = label_generator(token)
            current_branch.append((element_type, element_label))
            i += 1
    
    if current_branch:
        branches.append(current_branch)
    
    return branches

def parse_circuit_string_with_labels(circuit_tokens, label_generator=None):
    """
    带自定义标签生成器的电路解析函数
    
    参数:
    circuit_tokens: 电路表示的标记列表
    label_generator: 标签生成函数，如果为None则使用默认标签
    
    返回:
    branches: 适用于 parallel_circuit_drawer.py 的分支格式
    """
    if label_generator is None:
        label_generator = get_element_label
    
    # 开始解析
    if not circuit_tokens:
        return []
    
    if circuit_tokens[0] == 'p(':
        parallel_content = circuit_tokens[1:-1]
        return parse_parallel_content_with_labels(parallel_content, label_generator)
    else:
        parsed_result, _ = parse_tokens_with_labels(circuit_tokens, label_generator)
        return [parsed_result]