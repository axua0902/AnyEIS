# -*- coding: utf-8 -*-
"""
test_mutual_exclusion_redraw.py
回归测试: processCheckBox 勾选 (set_mutual_exclusion_enabled) 不应触发 drawfigure。

历史背景 (FILTER_COMPARE_UI_CHANGELOG.md 14.1 E3 节):
  早期实现中 set_mutual_exclusion_enabled 内部调用
  origindataCheckBox.setChecked(False) 触发了 stateChanged,
  最终 _on_processing_state_changed → drawfigure 出图,
  导致用户勾选 processCheckBox 后立即看到图表(用户没点 Draw)。

  当时评估认为"重绘是必要的,不能 blockSignals" — 该判断只对
  画布已有数据时成立,在 processCheckBox 切换阶段画布可能仍空,
  触发重绘是用户没期望的行为。

  修复 (Figure.py:188-202): set_mutual_exclusion_enabled 内部 setChecked
  用 blockSignals 包围,与 _on_proc_checkbox_clicked (line 244-252) 模式一致。
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest


# ----------------------------------------------------------------------
# Test data
# ----------------------------------------------------------------------

@pytest.fixture
def eis_df_5col():
    """5 列 EIS 数据 — 与 test_figure_render.py 一致,确保 plotX 不 IndexError。"""
    return pd.DataFrame({
        'FREQ[Hz]':   [1e3, 1e4, 1e5, 1e6],
        'Rs[ohm]':    [100.0, 95.0, 90.0, 85.0],
        'X[ohm]':     [-50.0, -45.0, -40.0, -35.0],
        'Phase[deg]': [-30.0, -28.0, -25.0, -22.0],
        'Z[ohm]':     [111.8, 105.0, 98.5, 92.0],
    })


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _spy_drawfigure(widget):
    """
    用 monkey-patch 替换 widget.drawfigure 以计数调用次数。
    返回 (calls_list, restore_fn) — restore_fn 在 finally 中调用。
    """
    calls = {'n': 0, 'args': []}
    original = widget.drawfigure

    def spy(*args, **kwargs):
        calls['n'] += 1
        calls['args'].append((args, kwargs))
        return original(*args, **kwargs)

    widget.drawfigure = spy

    def restore():
        widget.drawfigure = original
    return calls, restore


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

class TestMutualExclusionNoRedraw:
    """验证 set_mutual_exclusion_enabled 不触发 drawfigure。"""

    def test_set_mutual_exclusion_true_does_not_trigger_drawfigure(
        self, fig_widget, eis_df_5col
    ):
        """
        场景: 导入数据 → 勾选 processCheckBox (调 set_mutual_exclusion_enabled(True))
        期望: drawfigure 调用次数 = 0 (用户还没点 Draw 按钮,不应出图)
        """
        w = fig_widget
        # 加载数据(导入数据,模拟从 InputFile → Processing 接收数据)
        w.getsignal([1], ['Filt_orig'], [eis_df_5col], [{}])
        # 装 spy
        calls, restore = _spy_drawfigure(w)
        try:
            # 模拟 processCheckBox 勾选 → stateChanged → lambda
            w.set_mutual_exclusion_enabled(True)
        finally:
            restore()
        assert calls['n'] == 0, (
            f'set_mutual_exclusion_enabled(True) 触发了 {calls["n"]} 次 drawfigure,'
            f'期望 0 (用户没点 Draw 按钮,不应自动出图)'
        )

    def test_set_mutual_exclusion_false_does_not_trigger_drawfigure(
        self, fig_widget, eis_df_5col
    ):
        """
        场景: 互斥已开启 → 关闭互斥 (Filter 页面场景)
        期望: drawfigure 调用次数 = 0
        """
        w = fig_widget
        w.getsignal([1], ['Filt_orig'], [eis_df_5col], [{}])
        # 先开启互斥(此时不应触发 drawfigure)
        w.set_mutual_exclusion_enabled(True)
        # 装 spy
        calls, restore = _spy_drawfigure(w)
        try:
            # 关闭互斥(切到 Filter 页面)
            w.set_mutual_exclusion_enabled(False)
        finally:
            restore()
        assert calls['n'] == 0, (
            f'set_mutual_exclusion_enabled(False) 触发了 {calls["n"]} 次 drawfigure,'
            f'期望 0'
        )

    def test_mutual_exclusion_keeps_processed_checkbox_state(
        self, fig_widget, eis_df_5col
    ):
        """
        副断言: 启用互斥时,原 + 处 都勾 → 自动取消原,保留处。
        (这是 set_mutual_exclusion_enabled 的设计契约,必须仍生效)
        """
        w = fig_widget
        w.getsignal([1], ['Filt_orig'], [eis_df_5col], [{}])
        # 验证初始两都勾
        assert w.figuregui.origindataCheckBox.isChecked()
        assert w.figuregui.processeddataCheckBox.isChecked()
        # 启用互斥
        w.set_mutual_exclusion_enabled(True)
        # 验证:原取消,处保留
        assert not w.figuregui.origindataCheckBox.isChecked(), (
            '启用互斥时 origindataCheckBox 应被取消'
        )
        assert w.figuregui.processeddataCheckBox.isChecked(), (
            '启用互斥时 processeddataCheckBox 应保留'
        )

    def test_mutual_exclusion_no_op_when_already_single(
        self, fig_widget, eis_df_5col
    ):
        """
        场景: origindataCheckBox=False, processeddataCheckBox=True (已经是单选)
        启用互斥 → 不应触发任何 setChecked (因为不需要调整)
        也不应触发 drawfigure
        """
        w = fig_widget
        w.getsignal([1], ['Filt_orig'], [eis_df_5col], [{}])
        # 取消 orig
        w.figuregui.origindataCheckBox.setChecked(False)
        # 装 spy
        calls, restore = _spy_drawfigure(w)
        try:
            w.set_mutual_exclusion_enabled(True)
        finally:
            restore()
        # 状态没变,既不调 setChecked 也不调 drawfigure
        assert not w.figuregui.origindataCheckBox.isChecked()
        assert w.figuregui.processeddataCheckBox.isChecked()
        assert calls['n'] == 0

