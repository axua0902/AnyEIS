# -*- coding: utf-8 -*-
"""
拟合警告统一弹窗接口

提供:
- FittingWarningEmitter: 统一的警告/建议弹窗
- emit_warning: 简化调用
- _silent_mode: 测试环境关闭弹窗

设计原则:
- GUI 环境: QMessageBox.warning
- CLI/测试 环境: 仅 print log
- 失败/降级/建议 都通过此接口统一处理
"""

import sys

# 全局静默标志 (测试环境使用)
_SILENT_MODE = False


def set_silent_mode(silent=True):
    """设置静默模式 (True=不弹窗, 只打印)"""
    global _SILENT_MODE
    _SILENT_MODE = silent


def is_silent():
    """查询当前是否静默模式"""
    return _SILENT_MODE


def emit_warning(message, level='warning', title=None):
    """
    统一警告接口

    参数:
        message: 警告内容
        level: 'info' | 'warning' | 'critical'
        title: 自定义标题 (默认 '拟合建议 - {level}')

    返回:
        bool: True=用户确认, False=用户取消
    """
    title = title or f'拟合建议 - {level.upper()}'

    if _SILENT_MODE:
        # 静默模式: 仅打印
        prefix = {'info': 'ℹ️', 'warning': '⚠️ ', 'critical': '❌'}.get(level, '⚠️ ')
        print(f"\n{prefix} [{title}]")
        print(f"  {message}\n")
        return True

    # GUI 环境: 弹窗
    try:
        # 延迟导入, 避免在非 GUI 环境报错
        from PySide6.QtWidgets import QMessageBox
        if level == 'critical':
            box_func = QMessageBox.critical
        elif level == 'info':
            box_func = QMessageBox.information
        else:
            box_func = QMessageBox.warning

        ret = box_func(None, title, message,
                       QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        return ret == QMessageBox.StandardButton.Ok
    except ImportError:
        # 无 PySide6: 回退到控制台
        prefix = {'info': 'ℹ️', 'warning': '⚠️ ', 'critical': '❌'}.get(level, '⚠️ ')
        print(f"\n{prefix} [{title}]")
        print(f"  {message}\n")
        return True
    except Exception as e:
        # GUI 不可用: 回退到控制台
        print(f"\n⚠️  [{title}] (弹窗失败: {e})")
        print(f"  {message}\n")
        return True


# 便捷函数
def warn(message, title=None):
    """普通警告"""
    return emit_warning(message, 'warning', title)


def info(message, title=None):
    """信息提示"""
    return emit_warning(message, 'info', title)


def critical(message, title=None):
    """严重错误"""
    return emit_warning(message, 'critical', title)


def warn_fallback(method, original_result, fallback_result,
                original_chisqr, fallback_chisqr, true_params=None):
    """
    问题 3 修复: 弹窗显示完整对比（弹窗方案 B）

    显示:
        - 原方法参数 + χ²
        - 降级方法参数 + χ²
        - 自动使用降级结果
    """
    title = f"拟合失败自动降级 - {method}"

    # 构造对比消息
    lines = []
    lines.append(f"⚠️ {method} 拟合结果异常（参数误差 > 50%）")
    lines.append(f"已自动降级到 differential_evolution\n")

    # 原方法
    lines.append(f"【原方法】{method}")
    lines.append(f"  χ² = {original_chisqr:.3e}")
    if original_result is not None and hasattr(original_result, 'params'):
        for name in original_result.params:
            if name.endswith('_min') or name.endswith('_max'):
                continue
            val = original_result.params[name].value
            true_val = true_params.get(name) if true_params else None
            if true_val is not None and true_val != 0:
                err = abs((val - true_val) / true_val) * 100
                lines.append(f"  {name} = {val:.4g} (真实 {true_val:.4g}, 误差 {err:.1f}%)")
            else:
                lines.append(f"  {name} = {val:.4g}")

    lines.append("")

    # 降级方法
    lines.append(f"【降级后】differential_evolution")
    lines.append(f"  χ² = {fallback_chisqr:.3e}")
    if fallback_result is not None and hasattr(fallback_result, 'params'):
        for name in fallback_result.params:
            if name.endswith('_min') or name.endswith('_max'):
                continue
            val = fallback_result.params[name].value
            true_val = true_params.get(name) if true_params else None
            if true_val is not None and true_val != 0:
                err = abs((val - true_val) / true_val) * 100
                lines.append(f"  {name} = {val:.4g} (真实 {true_val:.4g}, 误差 {err:.1f}%)")
            else:
                lines.append(f"  {name} = {val:.4g}")

    lines.append("")
    lines.append("✅ 已自动使用 differential_evolution")

    message = "\n".join(lines)
    return emit_warning(message, 'warning', title)


if __name__ == '__main__':
    # 自测试
    set_silent_mode(True)
    print("测试 1: 普通警告")
    warn("Nelder 在宽边界下不稳定,建议使用紧边界。")
    print("\n测试 2: 严重错误")
    critical("拟合完全失败,无法继续!")
    print("\n测试 3: 信息")
    info("已使用 differential_evolution 完成拟合。")
    print("\n所有测试完成。")
