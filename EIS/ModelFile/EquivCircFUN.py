# -*- coding: utf-8 -*-
"""
电路分析和测试工具集
包含详细的电路分析、边界测试和综合测试功能

@author: zhang an
"""

import schemdraw
import schemdraw.elements as elm
from EIS.ModelFile.circuit_parser import parse_circuit_string
from EIS.ModelFile.parallel_circuit_drawer import draw_parallel_circuit_module, draw_nested_parallel_circuit_module


def analyze_circuit_characteristics(circuits, circuit_names):
    
    print("\n电路特征分析")
    print("=" * 60)
    
    for i, (circuit_string, description) in enumerate(zip(circuits, circuit_names)):
        print(f"\n电路 {i+1}: {description}")
        print(f"字符串长度: {len(circuit_string)} 个标记")
        
        try:
            branches = parse_circuit_string(circuit_string)
            
            # 计算复杂度指标
            def calculate_complexity(branches):
                element_count = 0
                parallel_count = 0
                max_depth = 0
                
                def traverse(item, depth=0):
                    nonlocal element_count, parallel_count, max_depth
                    max_depth = max(max_depth, depth)
                    
                    if isinstance(item, tuple):
                        element_count += 1
                    elif isinstance(item, dict) and item.get('type') == 'parallel':
                        parallel_count += 1
                        for branch in item.get('branches', []):
                            for sub_item in branch:
                                traverse(sub_item, depth + 1)
                    elif isinstance(item, list):
                        for sub_item in item:
                            traverse(sub_item, depth)
                
                for branch in branches:
                    traverse(branch)
                
                return element_count, parallel_count, max_depth
            
            elements, parallels, depth = calculate_complexity(branches)
            complexity_score = elements + parallels * 2 + depth * 3
            
            print(f"  主分支数: {len(branches)}")
            print(f"  元件总数: {elements}")
            print(f"  并联结构数: {parallels}")
            print(f"  最大嵌套深度: {depth}")
            print(f"  复杂度评分: {complexity_score}")
            
            if complexity_score < 10:
                complexity_level = "简单"
            elif complexity_score < 20:
                complexity_level = "中等"
            elif complexity_score < 30:
                complexity_level = "复杂"
            else:
                complexity_level = "极其复杂"
            
            print(f"  复杂度等级: {complexity_level}")
            
        except Exception as e:
            print(f"  ✗ 分析失败: {str(e)}")
        
        print("-" * 40)


def advanced_circuit_drawing(circuit_string, circuit_name):
    """
    高级电路绘制函数

    参数:
    circuit_string: 电路字符串表示
    circuit_name: 电路名称

    返回:
    drawing: schemdraw.Drawing 对象
    """

    # 转换为 branches 格式
    branches = parse_circuit_string(circuit_string)

    # 创建绘图
    d = schemdraw.Drawing()

    # 输入部分
    d += elm.Source().label('Vin')
    input_pos = d.here

    # 电压源与Start节点之间的横线
    d += elm.Line().right()

    # 电路主体
    start_pos = d.here
    d += elm.Dot().label('Start', loc='top')

    # 智能选择绘制方法
    if len(branches) == 1:
        # 检查是否为纯串联电路
        if all(isinstance(item, tuple) for item in branches[0]):
            # 纯串联电路，使用简单模块
            output_pos = draw_parallel_circuit_module(d, start_pos, branches, spacing=1.0)
        else:
            # 含有嵌套结构的单分支
            output_pos = draw_nested_parallel_circuit_module(d, start_pos, branches, spacing=2.0)
    elif len(branches) <= 3:
        # 中等复杂度，使用嵌套模块
        spacing = max(1.8, len(branches) * 0.7)
        output_pos = draw_nested_parallel_circuit_module(d, start_pos, branches, spacing=spacing)
    elif len(branches) <= 6:
        # 多分支，使用简单模块但增大间距
        spacing = max(2.2, len(branches) * 0.4)
        output_pos = draw_parallel_circuit_module(d, start_pos, branches, spacing=spacing)
    else:
        # 超多分支，紧凑布局
        output_pos = draw_parallel_circuit_module(d, start_pos, branches, spacing=1.5)

    # 输出部分 - 添加End节点和横线
    d.here = output_pos
    d += elm.Dot().label('End', loc='top')

    # End节点与接地之间的横线
    d += elm.Line().right()

    # 动态调整接地线高度
    ground_height = max(2.5, min(6.0, len(branches) * 0.9))
    d += elm.Line().down(ground_height)
    d += elm.Ground()

    # 输入接地
    d.here = input_pos
    input_ground_height = max(2.0, min(5.5, len(branches) * 0.7))
    d += elm.Line().down(input_ground_height)
    d += elm.Ground()

    return d


def drawCircuit(circuit):
    """
    绘制完整电路图（保持原有接口兼容性）
    
    Args:
        circuit: 电路列表或字符串
        
    Returns:
        schemdraw.Drawing: 电路图对象
    """
    if isinstance(circuit, str):
        circuit_name = "Circuit"
        return advanced_circuit_drawing(circuit, circuit_name)
    else:
        # 兼容旧格式，转换为字符串
        circuit_string = ''.join(str(item) for item in circuit)
        return advanced_circuit_drawing(circuit_string, "Circuit")


def analyze_circuit(circuit, debug_mode=True):
    """
    分析电路结构
    
    Args:
        circuit: 电路列表或字符串
        debug_mode: 是否输出调试信息
        
    Returns:
        dict: 分析结果
    """
    if isinstance(circuit, list):
        circuit_string = ''.join(str(item) for item in circuit)
    else:
        circuit_string = circuit
    
    try:
        branches = parse_circuit_string(circuit_string)
        
        # 计算复杂度指标
        def calculate_complexity(branches):
            element_count = 0
            parallel_count = 0
            max_depth = 0
            
            def traverse(item, depth=0):
                nonlocal element_count, parallel_count, max_depth
                max_depth = max(max_depth, depth)
                
                if isinstance(item, tuple):
                    element_count += 1
                elif isinstance(item, dict) and item.get('type') == 'parallel':
                    parallel_count += 1
                    for branch in item.get('branches', []):
                        for sub_item in branch:
                            traverse(sub_item, depth + 1)
                elif isinstance(item, list):
                    for sub_item in item:
                        traverse(sub_item, depth)
            
            for branch in branches:
                traverse(branch)
            
            return element_count, parallel_count, max_depth
        
        elements, parallels, depth = calculate_complexity(branches)
        complexity_score = elements + parallels * 2 + depth * 3
        
        result = {
            'branches': branches,
            'total_elements': elements,
            'parallel_structures': parallels,
            'max_depth': depth,
            'complexity_score': complexity_score,
            'is_valid': True
        }
        
        if debug_mode:
            print(f"电路分析结果:")
            print(f"  总元件数: {elements}")
            print(f"  并联结构数: {parallels}")
            print(f"  最大嵌套深度: {depth}")
            print(f"  复杂度评分: {complexity_score}")
        
        return result
        
    except Exception as e:
        if debug_mode:
            print(f"电路分析失败: {str(e)}")
        return {
            'branches': None,
            'total_elements': 0,
            'parallel_structures': 0,
            'max_depth': 0,
            'complexity_score': 0,
            'is_valid': False,
            'error': str(e)
        }