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


def _safe_print(text):
    """受限编码(GBK等)控制台安全打印: 不可编码字符降级为 '?'"""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        print(text.encode(enc, errors='replace').decode(enc, errors='replace'))


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
    title = title or f'Fitting Notice / 拟合提示 - {level.upper()}'

    if _SILENT_MODE:
        # 静默模式: 仅打印 (ASCII 前缀, 避免 GBK 控制台编码错误)
        prefix = {'info': '[INFO]', 'warning': '[WARN]', 'critical': '[ERROR]'}.get(level, '[WARN]')
        _safe_print(f"\n{prefix} [{title}]")
        _safe_print(f"  {message}\n")
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
        prefix = {'info': '[INFO]', 'warning': '[WARN]', 'critical': '[ERROR]'}.get(level, '[WARN]')
        _safe_print(f"\n{prefix} [{title}]")
        _safe_print(f"  {message}\n")
        return True
    except Exception as e:
        # GUI 不可用: 回退到控制台
        _safe_print(f"\n[WARN] [{title}] (popup failed / 弹窗失败: {e})")
        _safe_print(f"  {message}\n")
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


def _format_param_lines(result, true_params=None):
    """格式化拟合参数行 (英汉双语, 简洁)"""
    lines = []
    if result is not None and hasattr(result, 'params'):
        for name in result.params:
            if name.endswith('_min') or name.endswith('_max'):
                continue
            val = result.params[name].value
            true_val = true_params.get(name) if true_params else None
            if true_val is not None and true_val != 0:
                err = abs((val - true_val) / true_val) * 100
                lines.append(f"  {name} = {val:.4g} "
                             f"(true/真实 {true_val:.4g}, err/误差 {err:.1f}%)")
            else:
                lines.append(f"  {name} = {val:.4g}")
    return lines


def warn_fallback(method, original_result, fallback_result,
                original_chisqr, fallback_chisqr, true_params=None):
    """
    问题 3 修复: 弹窗显示完整对比（弹窗方案 B）

    显示:
        - 原方法参数 + χ²
        - 降级方法参数 + χ²
        - 自动使用降级结果
        - fallback_result=None 时为第一阶段提示 (降级计算中)
    """
    title = f"Auto Fallback / 拟合降级 - {method}"
    pending = fallback_result is None

    # 构造对比消息 (英汉双语, 简洁)
    lines = [
        f"[WARN] {method} fit abnormal (param error > 50% or RMS > 10%)",
        f"{method} 拟合结果异常（参数误差>50% 或残差RMS>10%）",
    ]
    if pending:
        lines.append("Retrying with differential_evolution / "
                     "正在用 differential_evolution 重试\n")
    else:
        lines.append("Switched to differential_evolution / "
                     "已自动降级至 differential_evolution\n")

    # 原方法
    lines.append(f"【Original / 原方法】{method}")
    lines.append(f"  χ² = {original_chisqr:.3e}")
    lines.extend(_format_param_lines(original_result, true_params))
    lines.append("")

    # 降级方法
    if pending:
        # 第一阶段: DE 重试尚未完成, 不显示误导性的 χ²=0
        lines.append("【Fallback / 降级后】differential_evolution (running / 计算中)")
        lines.append("")
        lines.append("[INFO] Result will be reported after retry / "
                     "重试完成后另行报告")
    else:
        lines.append("【Fallback / 降级后】differential_evolution")
        lines.append(f"  χ² = {fallback_chisqr:.3e}")
        lines.extend(_format_param_lines(fallback_result, true_params))
        lines.append("")
        lines.append("[OK] differential_evolution result adopted / "
                     "已采用 differential_evolution 结果")

    message = "\n".join(lines)
    return emit_warning(message, 'warning', title)


if __name__ == '__main__':
    # 自测试
    set_silent_mode(True)
    print("Test 1 / 测试 1: warning / 普通警告")
    warn("Nelder unstable with wide bounds; use tight bounds.\nNelder 宽边界下不稳定，建议使用紧边界。")
    print("\nTest 2 / 测试 2: critical / 严重错误")
    critical("Fitting failed completely.\n拟合完全失败!")
    print("\nTest 3 / 测试 3: info / 信息")
    info("Fitting completed with differential_evolution.\n已用 differential_evolution 完成拟合。")
    print("\nTest 4 / 测试 4: fallback pending / 降级第一阶段")
    warn_fallback('nelder', None, None, 1.234e-3, 0.0)
    print("\nAll tests done / 所有测试完成。")
