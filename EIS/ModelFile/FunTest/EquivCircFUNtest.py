"""
新电路测试程序 - test4.py
测试 new_test_circuits 中的10个全新电路
"""

from EIS.ModelFile.circuit_parser import parse_circuit_string
from EIS.ModelFile.EquivCircFUN import advanced_circuit_drawing

# 定义10个全新的测试电路
new_test_circuits = [
    # 电路1: RC串并联组合
    # (R1+C1) | (R2+C2) | R3
    ['p(', 'R1', '+', 'C1', ',', 'R2', '+', 'C2', ',', 'R3', ')'],
    
    # 电路2: LC谐振与RC并联
    # (L1+C3) | (R4+C4+R5)
    ['p(', 'L1', '+', 'C3', ',', 'R4', '+', 'C4', '+', 'R5', ')'],
    
    # 电路3: 三级深度嵌套 - RLC混合
    # R6 + p((L2+p(C5,R7+L3)),C6+R8)
    ['R6', '+', 'p(', 
     'L2', '+', 'p(', 'C5', ',', 'R7', '+', 'L3', ')', 
     ',', 
     'C6', '+', 'R8', 
     ')'],
    
    # 电路4: 对称双路并联
    # p((R9+L4+C7),(R10+L5+C8))
    ['p(', 'R9', '+', 'L4', '+', 'C7', ',', 'R10', '+', 'L5', '+', 'C8', ')'],
    
    # 电路5: 复杂四级嵌套
    # p(R11, C9+p(L6+p(R12,C10+L7), R13+C11+p(R14,L8)))
    ['p(', 'R11', ',', 
     'C9', '+', 'p(', 
         'L6', '+', 'p(', 'R12', ',', 'C10', '+', 'L7', ')', 
         ',', 
         'R13', '+', 'C11', '+', 'p(', 'R14', ',', 'L8', ')', 
     ')', 
     ')'],
    
    # 电路6: 大规模并联 - 6个分支
    # p(C12, R15+L9, C13+R16, L10+C14+R17, R18+L11, C15+R19+L12)
    ['p(', 'C12', ',', 'R15', '+', 'L9', ',', 'C13', '+', 'R16', ',', 
     'L10', '+', 'C14', '+', 'R17', ',', 'R18', '+', 'L11', ',', 
     'C15', '+', 'R19', '+', 'L12', ')'],
    
    # 电路7: 串联中的多重并联
    # L13 + p(R20+C16, L14+R21) + C17 + p(R22, L15+C18)
    ['L13', '+', 'p(', 'R20', '+', 'C16', ',', 'L14', '+', 'R21', ')', '+', 
     'C17', '+', 'p(', 'R22', ',', 'L15', '+', 'C18', ')'],
    
    # 电路8: 深度嵌套对称结构
    # p(R23+p(C19+p(L16,R24),R25+L17), R26+p(C20+p(L18,R27),R28+L19))
    ['p(', 
     'R23', '+', 'p(', 'C19', '+', 'p(', 'L16', ',', 'R24', ')', ',', 'R25', '+', 'L17', ')',
     ',',
     'R26', '+', 'p(', 'C20', '+', 'p(', 'L18', ',', 'R27', ')', ',', 'R28', '+', 'L19', ')',
     ')'],
    
    # 电路9: 单分支复杂串联
    # R29 + L20 + C21 + R30 + L21 + C22 + R31
    ['R29', '+', 'L20', '+', 'C21', '+', 'R30', '+', 'L21', '+', 'C22', '+', 'R31'],
    
    # 电路10: 五级极限嵌套
    # p(R32+p(L22+p(C23+p(R33+p(L23,C24),R34),L24+C25),R35+L25), C26+R36+L26)
    ['p(', 
     'R32', '+', 'p(', 
         'L22', '+', 'p(', 
             'C23', '+', 'p(', 
                 'R33', '+', 'p(', 'L23', ',', 'C24', ')', 
                 ',', 
                 'R34', 
             ')', 
             ',', 
             'L24', '+', 'C25', 
         ')', 
         ',', 
         'R35', '+', 'L25', 
     ')', 
     ',', 
     'C26', '+', 'R36', '+', 'L26', 
     ')']
]

def test_new_circuits():
    """测试所有新电路的转换和绘制"""
    
    print("开始测试new_test_circuits中的10个电路...")
    print("=" * 50)
    
    success_count = 0
    total_count = len(new_test_circuits)
    
    for i, circuit_string in enumerate(new_test_circuits):
        print(f"\n正在处理新电路 {i+1}")
        
        try:
            # 转换测试
            branches = parse_circuit_string(circuit_string)
            print(f"✓ 转换成功: {len(branches)} 个主分支")
            
            # 绘制测试
            circuit_name = f"NewTest{i+1}"
            drawing = advanced_circuit_drawing(circuit_string, circuit_name)
            
            # 保存图像
            filename = f'CircuitFigure/new_test{i+1}_circuit.png'
            drawing.save(filename)
            
            print(f"✓ 绘制成功，已保存到: {filename}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ 处理失败: {str(e)}")
            
        print("-" * 40)
    
    print(f"\n新电路测试完成!")
    print(f"成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")

if __name__ == "__main__":
    test_new_circuits()
