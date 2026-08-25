# -*- coding: utf-8 -*-
"""
conftest.py for EIS/ProcessingFile/Funtest

在 pytest 收集阶段（test 文件导入前）阻止 gmpy2 加载，
避免触发 Windows fatal exception: code 0xc0000139 (STATUS_ENTRYPOINT_NOT_FOUND)

注意: conftest.py 是 pytest 配置文件，不属于程序本身。
模块级 import mpmath (Processingfun.py line 15) 会触发 gmpy2 加载。
通过预先设置 sys.modules['gmpy2'] = None 阻止加载，mpmath 会自动 fallback。
"""
import sys

# 阻止 gmpy2 加载（必须在任何 mpmath/Processingfun 导入之前执行）
sys.modules['gmpy2'] = None
