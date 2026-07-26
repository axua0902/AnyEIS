"""
并联电路绘制模块
包含用于绘制简单和嵌套并联电路的核心函数
"""

import schemdraw
import schemdraw.elements as elm

# 共享的元件类型映射
ELEMENT_MAP = {
    'resistor': elm.Resistor,
    'capacitor': elm.Capacitor, 
    'inductor': elm.Inductor,
    'line': elm.Line
}

def _connect_branches_to_output(drawing, branch_ends, start_pos, output_spacing=0.5):
    """
    将所有分支连接到输出汇聚点的通用函数
    
    参数:
    drawing: schemdraw.Drawing对象
    branch_ends: 分支结束位置列表
    start_pos: 起始位置（输入点）
    output_spacing: 输出汇聚点的额外间距
    
    返回: 输出点的位置 (x, y)
    """
    if not branch_ends:
        return start_pos
    
    # 计算输出汇聚点位置
    max_x = max(end_pos[0] for end_pos in branch_ends)
    output_x = max_x + output_spacing
    output_y = start_pos[1]
    
    # 连接所有分支到输出点
    for end_pos in branch_ends:
        drawing.here = end_pos
        # 先向右延伸到输出x坐标
        drawing += elm.Line().to((output_x, end_pos[1]))
        # 再向输出y坐标连接（如果需要）
        if end_pos[1] != output_y:
            drawing += elm.Line().to((output_x, output_y))
    
    # 在输出点标记
    drawing.here = (output_x, output_y)
    drawing += elm.Dot().label('', loc='top')
    
    return (output_x, output_y)

def draw_parallel_circuit_module(drawing, start_pos, branches, spacing=1.5, output_spacing=0.5):
    """
    绘制局部并联电路模块的通用函数
    
    参数:
    drawing: schemdraw.Drawing对象
    start_pos: 起始位置 (x, y)
    branches: 列表，每个元素是一个分支的元件列表
             每个分支格式: [('resistor', 'R1'), ('capacitor', 'C1'), ...]
    spacing: 分支间的垂直间距
    output_spacing: 输出汇聚点的额外间距
    
    返回: 输出点的位置 (x, y)
    """
    # 使用共享的元件类型映射
    element_map = ELEMENT_MAP
    
    drawing.here = start_pos
    input_dot = drawing.here
    drawing += elm.Dot().label('', loc='top')
    
    branch_ends = []
    max_x = start_pos[0]
    
    # 绘制每个分支
    for i, branch in enumerate(branches):
        drawing.here = input_dot
        
        # 计算分支的垂直偏移
        if len(branches) == 1:
            y_offset = 0
        else:
            y_offset = (i - (len(branches) - 1) / 2) * spacing
        
        # 移动到分支起始位置
        if y_offset != 0:
            drawing += elm.Line().to((input_dot[0], input_dot[1] + y_offset))
        
        branch_start = drawing.here
        
        # 绘制分支中的每个元件
        for j, (element_type, label) in enumerate(branch):
            if element_type in element_map:
                if element_type == 'line':
                    # 解析line参数，如果label包含长度信息
                    if 'right' in label.lower():
                        length = float(label.split('(')[1].split(')')[0]) if '(' in label else 1.0
                        drawing += elm.Line().right(length)
                    elif 'up' in label.lower():
                        length = float(label.split('(')[1].split(')')[0]) if '(' in label else 1.0
                        drawing += elm.Line().up(length)
                    elif 'down' in label.lower():
                        length = float(label.split('(')[1].split(')')[0]) if '(' in label else 1.0
                        drawing += elm.Line().down(length)
                    else:
                        drawing += elm.Line().right(1.0)
                else:
                    drawing += element_map[element_type]().right().label(label)
        
        branch_ends.append(drawing.here)
    
    # 使用共享的连接函数
    return _connect_branches_to_output(drawing, branch_ends, input_dot, output_spacing)

def draw_nested_parallel_circuit_module(drawing, start_pos, branches, spacing=1.5, output_spacing=0.5):
    """
    绘制嵌套并联电路模块的高级函数
    支持分支内部再次并联的情况
    
    参数:
    drawing: schemdraw.Drawing对象
    start_pos: 起始位置 (x, y)
    branches: 列表，每个元素可以是：
             1. 简单分支: [('resistor', 'R1'), ('capacitor', 'C1'), ...]
             2. 嵌套并联: {'type': 'parallel', 'branches': [[...], [...]], 'spacing': 1.0}
             3. 混合分支: [('resistor', 'R1'), {'type': 'parallel', 'branches': [...]}, ('capacitor', 'C1')]
    spacing: 分支间的垂直间距
    output_spacing: 输出汇聚点的额外间距
    
    返回: 输出点的位置 (x, y)
    """
    # 使用共享的元件类型映射
    element_map = ELEMENT_MAP
    
    drawing.here = start_pos
    input_dot = drawing.here
    drawing += elm.Dot().label('', loc='top')
    
    branch_ends = []
    max_x = start_pos[0]
    
    # 绘制每个分支
    for i, branch in enumerate(branches):
        drawing.here = input_dot
        
        # 计算分支的垂直偏移
        if len(branches) == 1:
            y_offset = 0
        else:
            y_offset = (i - (len(branches) - 1) / 2) * spacing
        
        # 移动到分支起始位置
        if y_offset != 0:
            drawing += elm.Line().to((input_dot[0], input_dot[1] + y_offset))
        
        branch_start = drawing.here
        
        # 处理分支内容（可能是简单元件或嵌套并联）
        branch_end = _process_branch_content(drawing, branch)
        
        branch_ends.append(branch_end)
    
    # 使用共享的连接函数
    return _connect_branches_to_output(drawing, branch_ends, input_dot, output_spacing)

def _process_branch_content(drawing, branch):
    """
    处理分支内容，支持简单元件和嵌套并联
    
    参数:
    drawing: schemdraw.Drawing对象
    branch: 分支定义（列表或字典）
    
    返回: 分支结束位置 (x, y)
    """
    # 使用共享的元件类型映射
    element_map = ELEMENT_MAP
    branch_start = drawing.here
    
    if isinstance(branch, list):
        # 处理列表形式的分支（可能包含嵌套并联）
        for element in branch:
            if isinstance(element, dict) and element.get('type') == 'parallel':
                # 处理嵌套并联部分
                nested_spacing = element.get('spacing', 1.0)
                nested_branches = element.get('branches', [])
                nested_end = draw_nested_parallel_circuit_module(
                    drawing, drawing.here, nested_branches, 
                    spacing=nested_spacing, output_spacing=0.3
                )
                drawing.here = nested_end
            elif isinstance(element, tuple) and len(element) == 2:
                # 处理简单元件
                element_type, label = element
                if element_type in element_map:
                    if element_type == 'line':
                        # 处理线条元件
                        if 'right' in label.lower():
                            length = float(label.split('(')[1].split(')')[0]) if '(' in label else 1.0
                            drawing += elm.Line().right(length)
                        elif 'up' in label.lower():
                            length = float(label.split('(')[1].split(')')[0]) if '(' in label else 1.0
                            drawing += elm.Line().up(length)
                        elif 'down' in label.lower():
                            length = float(label.split('(')[1].split(')')[0]) if '(' in label else 1.0
                            drawing += elm.Line().down(length)
                        else:
                            drawing += elm.Line().right(1.0)
                    else:
                        drawing += element_map[element_type]().right().label(label)
    elif isinstance(branch, dict) and branch.get('type') == 'parallel':
        # 整个分支就是一个并联结构
        nested_spacing = branch.get('spacing', 1.0)
        nested_branches = branch.get('branches', [])
        nested_end = draw_nested_parallel_circuit_module(
            drawing, drawing.here, nested_branches, 
            spacing=nested_spacing, output_spacing=0.3
        )
        drawing.here = nested_end
    
    return drawing.here