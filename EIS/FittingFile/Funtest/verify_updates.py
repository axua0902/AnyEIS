# -*- coding: utf-8 -*-
"""
测试文件验证脚本
用于快速验证 FittingMSfortest.py 和 FittingMStest.py 是否正确更新

测试目标: FittingMSfortest.py + FittingMStest.py（项目早期版本遗留）
测试类型: 导入验证

注意: 此脚本验证的 FittingMSfortest.py / FittingMStest.py 文件
      已不在当前仓库结构中，仅作历史保留。如已不需要可直接删除。

运行方式:
    python EIS/FittingFile/Funtest/verify_updates.py

Created: 2026-04-29
Updated on 2026-08-25: 规范化头注释
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, project_root)

def verify_imports():
    """验证所有必要的导入是否正常"""
    print("="*60)
    print("步骤 1: 验证导入")
    print("="*60)
    
    try:
        # 验证 FittingMSfortest.py
        print("\n检查 FittingMSfortest.py...")
        from FittingMSfortest import (
            fittingmodel, 
            fcn2min, 
            FittingMS, 
            Fittingresultsprocess,
            creatdatabase
        )
        print("✓ FittingMSfortest.py 所有函数导入成功")
        
        # 验证 FittingMStest.py
        print("\n检查 FittingMStest.py...")
        from FittingMStest import (
            generate_test_data_single_shell,
            test_single_shell_fitting,
            test_double_shell_fitting,
            test_with_electrode_polarization,
            plot_fitting_results,
            run_all_tests
        )
        print("✓ FittingMStest.py 所有函数导入成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def verify_function_signatures():
    """验证函数签名是否正确"""
    print("\n" + "="*60)
    print("步骤 2: 验证函数签名")
    print("="*60)
    
    try:
        import inspect
        from FittingMSfortest import fittingmodel, fcn2min, FittingMS, Fittingresultsprocess
        
        # 检查 fittingmodel 签名
        sig = inspect.signature(fittingmodel)
        expected_params = ['pm', 'omega', 'media', 'shellstructre', 'option']
        actual_params = list(sig.parameters.keys())
        
        print(f"\nfittingmodel() 参数:")
        print(f"  期望: {expected_params}")
        print(f"  实际: {actual_params}")
        
        if actual_params == expected_params:
            print("  ✓ 签名正确")
        else:
            print("  ✗ 签名不匹配")
            return False
        
        # 检查 fcn2min 签名
        sig = inspect.signature(fcn2min)
        expected_params = ['params', 'omega', 'media', 'shellstructre', 'epsTest', 'option']
        actual_params = list(sig.parameters.keys())
        
        print(f"\nfcn2min() 参数:")
        print(f"  期望: {expected_params}")
        print(f"  实际: {actual_params}")
        
        if actual_params == expected_params:
            print("  ✓ 签名正确")
        else:
            print("  ✗ 签名不匹配")
            return False
        
        # 检查 FittingMS 签名
        sig = inspect.signature(FittingMS)
        expected_params = ['params', 'freq', 'media', 'shellstructre', 'prodata', 'option']
        actual_params = list(sig.parameters.keys())
        
        print(f"\nFittingMS() 参数:")
        print(f"  期望: {expected_params}")
        print(f"  实际: {actual_params}")
        
        if actual_params == expected_params:
            print("  ✓ 签名正确")
        else:
            print("  ✗ 签名不匹配")
            return False
        
        # 检查 Fittingresultsprocess 签名
        sig = inspect.signature(Fittingresultsprocess)
        expected_params = ['pm', 'freq', 'media', 'shellstructre', 'result', 'option']
        actual_params = list(sig.parameters.keys())
        
        print(f"\nFittingresultsprocess() 参数:")
        print(f"  期望: {expected_params}")
        print(f"  实际: {actual_params}")
        
        if actual_params == expected_params:
            print("  ✓ 签名正确")
        else:
            print("  ✗ 签名不匹配")
            return False
        
        print("\n✓ 所有函数签名验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 签名验证失败: {e}")
        return False


def verify_model_imports():
    """验证模型导入是否正确"""
    print("\n" + "="*60)
    print("步骤 3: 验证模型导入")
    print("="*60)
    
    try:
        from FittingMSfortest import EPMS, MS, Maxwell, Hanai
        print("\n✓ MultiShell 模型函数导入成功:")
        print("  - EPMS (带电极极化的多壳层模型)")
        print("  - MS (多壳层模型)")
        print("  - Maxwell (Maxwell 混合模型)")
        print("  - Hanai (Hanai 混合模型)")
        
        return True
        
    except ImportError as e:
        print(f"✗ 模型导入失败: {e}")
        return False


def verify_compatibility():
    """验证与 FittingMS.py 的兼容性"""
    print("\n" + "="*60)
    print("步骤 4: 验证与 FittingMS.py 的兼容性")
    print("="*60)
    
    try:
        # 导入主模块
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from FittingMS import (
            FittingMS as FittingMS_main,
            create_single_shell_structure,
            create_double_shell_structure,
            create_triple_shell_structure
        )
        
        print("\n✓ FittingMS.py 主模块导入成功")
        print("✓ 辅助函数可用:")
        print("  - create_single_shell_structure()")
        print("  - create_double_shell_structure()")
        print("  - create_triple_shell_structure()")
        
        # 验证函数签名一致性
        import inspect
        from FittingMSfortest import FittingMS as FittingMS_test
        
        sig_main = inspect.signature(FittingMS_main)
        sig_test = inspect.signature(FittingMS_test)
        
        params_main = list(sig_main.parameters.keys())
        params_test = list(sig_test.parameters.keys())
        
        print(f"\n函数签名对比:")
        print(f"  FittingMS.py:        {params_main}")
        print(f"  FittingMSfortest.py: {params_test}")
        
        if params_main == params_test:
            print("  ✓ 签名完全一致")
            return True
        else:
            print("  ✗ 签名不一致")
            return False
        
    except Exception as e:
        print(f"✗ 兼容性验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_test_structure():
    """验证测试结构"""
    print("\n" + "="*60)
    print("步骤 5: 验证测试结构")
    print("="*60)
    
    try:
        from FittingMStest import (
            test_single_shell_fitting,
            test_double_shell_fitting,
            test_with_electrode_polarization
        )
        
        print("\n✓ 测试函数可用:")
        print("  1. test_single_shell_fitting() - 单壳层模型拟合")
        print("  2. test_double_shell_fitting() - 双壳层模型拟合")
        print("  3. test_with_electrode_polarization() - 带电极极化拟合")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试结构验证失败: {e}")
        return False


def print_summary(results):
    """打印验证摘要"""
    print("\n" + "="*60)
    print("验证摘要")
    print("="*60)
    
    all_passed = all(results.values())
    
    for step, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{step}: {status}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✓✓✓ 所有验证通过！测试文件已正确更新 ✓✓✓")
        print("="*60)
        print("\n可以安全地使用这两个测试文件:")
        print("  - FittingMSfortest.py: 用于实际数据拟合")
        print("  - FittingMStest.py: 用于功能测试和验证")
        print("\n运行完整测试:")
        print("  python FittingMStest.py")
    else:
        print("✗✗✗ 部分验证失败，请检查上述错误信息 ✗✗✗")
        print("="*60)
    
    return all_passed


def main():
    """主验证流程"""
    print("\n" + "="*60)
    print("FittingMS 测试文件验证工具")
    print("="*60)
    print("此脚本将验证 FittingMSfortest.py 和 FittingMStest.py")
    print("是否已正确更新以匹配重构后的 FittingMS.py")
    print("="*60)
    
    results = {}
    
    # 执行各项验证
    results["导入验证"] = verify_imports()
    
    if results["导入验证"]:
        results["函数签名验证"] = verify_function_signatures()
        results["模型导入验证"] = verify_model_imports()
        results["兼容性验证"] = verify_compatibility()
        results["测试结构验证"] = verify_test_structure()
    else:
        print("\n由于导入失败，跳过后续验证步骤")
        results["函数签名验证"] = False
        results["模型导入验证"] = False
        results["兼容性验证"] = False
        results["测试结构验证"] = False
    
    # 打印摘要
    all_passed = print_summary(results)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
