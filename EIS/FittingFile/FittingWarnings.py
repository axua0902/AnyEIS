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
        from PyQt5.QtWidgets import QMessageBox
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
        # 无 PyQt5: 回退到控制台
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
