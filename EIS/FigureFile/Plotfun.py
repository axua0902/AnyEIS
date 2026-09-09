from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import numpy as np
import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from datetime import datetime


import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 设置字体支持（使用支持Unicode的字体）
plt.rcParams["font.family"] = ["DejaVu Sans", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False


class MyMplCanvas(FigureCanvas):
    global labelref

    labelref = ["Fit", "Simul", "Filt"]

    def __init__(self, parent=None, width=8, height=10, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = self.fig.add_subplot(111)
        self.axes.tick_params(axis="both", labelsize=12)

        self.axes.grid(True)
        self.fig.set_facecolor("#F0F7FF")  # 这里可以设置为你想要的颜色
        self.axes.set_facecolor("#F0F7FF")

        super().__init__(self.fig)

        # 设置最小高度，确保绘图区域有足够的空间
        self.setMinimumHeight(400)

    def plotNormal(
        self,
        outputlist,
        dataname,
        data,
        figpos=None,
        col_index=None,
        ylabel=None,
        auto_layout=True,
    ):
        """
        统一的Normal绘图函数，支持单图和多图模式

        Parameters:
        outputlist: 输出列表
        dataname: 数据名称列表
        data: 数据列表
        figpos: 子图位置 (如果为None且auto_layout=True，则自动布局)
        col_index: 要绘制的列索引 (如果为None且auto_layout=True，则绘制所有列)
        ylabel: Y轴标签 (如果为None，则自动生成)
        auto_layout: 是否启用自动布局 (默认True)
        """

        if auto_layout and figpos is None and col_index is None:
            # 自动布局模式：绘制所有列的多子图
            self._plot_normal_auto(outputlist, dataname, data)
        else:
            # 手动模式：绘制单个子图
            self._plot_normal_single(
                outputlist, dataname, data, figpos or 111, col_index or 1, ylabel or "Y"
            )

    def _plot_normal_auto(self, outputlist, dataname, data):
        """自动布局模式：根据数据列数动态绘制所有Normal图表"""
        self.fig.clear()
        print("Drawing Normal figures with auto layout...")

        # 获取数据的最大列数
        max_cols = 0
        for i in range(len(outputlist)):
            if outputlist[i] == 1 and len(data) > i:
                colname = list(data[i].columns)
                max_cols = max(max_cols, len(colname))

        # 计算需要绘制的列数（从第1列开始，第0列是x轴）
        plot_cols = max_cols - 1 if max_cols > 1 else 1

        if plot_cols == 1:
            # 只有一列数据，绘制单图
            self._plot_normal_single(outputlist, dataname, data, 111, 1, "Y")
        else:
            # 多列数据，绘制多子图
            subplot_layout = self._get_subplot_layout(plot_cols)

            # 生成子图配置并绘制
            for i in range(plot_cols):
                col_index = i + 1  # 从第1列开始（第0列是x轴）
                ylabel = f"Y{col_index}"
                figpos = subplot_layout[i] if i < len(subplot_layout) else 111
                self._plot_normal_single(
                    outputlist, dataname, data, figpos, col_index, ylabel
                )

        self.fig.tight_layout()
        self.draw()
        print(f"plotNormal auto layout - {plot_cols} subplots")
        self.update()

    def _plot_normal_single(
        self, outputlist, dataname, data, figpos, col_index, ylabel
    ):
        """绘制单个Normal子图"""
        ax = self.fig.add_subplot(figpos)
        ax.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                # 检查是否有足够的列
                if len(colname) > col_index:
                    x = data[i][colname[0]]
                    y = data[i][colname[col_index]]

                    if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                        ax.plot(x, y, "--", linewidth=2, label=dataname[i])
                    elif labelref[1] in dataname[i]:
                        ax.plot(x, y, "-", linewidth=2, label=dataname[i])
                    else:
                        ax.scatter(x, y, marker="x", s=10, label=dataname[i])
                    has_data = True

        ax.set_xlabel("X", fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.tick_params(axis="both", labelsize=12)

        if has_data:
            ax.legend(loc="best")

        # 只在单图模式下调用draw
        if figpos == 111:
            self.draw()
            print(f"plotNormal single - column {col_index}")

    def _get_subplot_layout(self, num_plots):
        """根据子图数量返回合适的布局位置列表"""
        if num_plots == 1:
            return [111]
        elif num_plots == 2:
            return [211, 212]  # 上下布局
        elif num_plots == 3:
            return [221, 222, 212]  # 上面两个，下面一个跨两列
        elif num_plots == 4:
            return [221, 222, 223, 224]  # 2x2布局
        elif num_plots <= 6:
            return [231, 232, 233, 234, 235, 236]  # 2x3布局
        elif num_plots <= 8:
            return [241, 242, 243, 244, 245, 246, 247, 248]  # 2x4布局
        elif num_plots <= 9:
            return [331, 332, 333, 334, 335, 336, 337, 338, 339]  # 3x3布局
        else:
            # 对于更多子图，使用动态计算
            rows = int(np.ceil(np.sqrt(num_plots)))
            cols = int(np.ceil(num_plots / rows))
            layout = []
            for i in range(num_plots):
                layout.append(int(f"{rows}{cols}{i + 1}"))
            return layout

    ##########################impedance################################################################################

    def plotRs(self, outputlist, dataname, data, figpos):
        # Bode-Rs#######
        self.axRs = self.fig.add_subplot(figpos)
        self.axRs.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axRs.plot(
                        data[i][colname[0]],
                        data[i][colname[1]],
                        "--",
                        linewidth=2,
                        label=dataname[i],
                    )
                elif labelref[1] in dataname[i]:
                    self.axRs.plot(
                        data[i][colname[0]],
                        data[i][colname[1]],
                        "-",
                        linewidth=2,
                        label=dataname[i],
                    )
                else:
                    self.axRs.scatter(
                        data[i][colname[0]],
                        data[i][colname[1]],
                        marker="x",
                        s=10,
                        label=dataname[i],
                    )
                has_data = True
            else:
                pass

        self.axRs.set_xscale("log")
        self.axRs.set_xlabel("Frequency [Hz]", fontsize=12)
        self.axRs.set_ylabel("Rs [ohm]", fontsize=12)
        self.axRs.tick_params(axis="both", labelsize=12)

        if has_data:
            self.axRs.legend(loc="best")
        self.draw()
        print("plotRs")
        # Bode-Rs#######

    def plotX(self, outputlist, dataname, data, figpos):
        # Bode-X########

        self.axbodeX = self.fig.add_subplot(figpos)
        self.axbodeX.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axbodeX.plot(
                        data[i][colname[0]],
                        data[i][colname[4]],
                        "--",
                        linewidth=2,
                        label=dataname[i],
                    )
                elif labelref[1] in dataname[i]:
                    self.axbodeX.plot(
                        data[i][colname[0]],
                        data[i][colname[4]],
                        "-",
                        linewidth=2,
                        label=dataname[i],
                    )
                else:
                    self.axbodeX.scatter(
                        data[i][colname[0]],
                        data[i][colname[4]],
                        marker="x",
                        s=10,
                        label=dataname[i],
                    )
                has_data = True
            else:
                pass
        self.axbodeX.set_xscale("log")
        self.axbodeX.set_xlabel("Frequency [Hz]", fontsize=12)
        self.axbodeX.set_ylabel("X [ohm]", fontsize=12)
        self.axbodeX.tick_params(axis="both", labelsize=12)
        if has_data:
            self.axbodeX.legend(loc="best")
        self.axbodeX.invert_yaxis()

        self.draw()
        print("plotX")

        # Bode-X########

    def plotPhy(self, outputlist, dataname, data, figpos):
        # Bode-Phy#######
        self.axPhy = self.fig.add_subplot(figpos)
        self.axPhy.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)

                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axPhy.plot(
                        data[i][colname[0]],
                        data[i][colname[2]],
                        "--",
                        linewidth=2,
                        label=dataname[i],
                    )
                elif labelref[1] in dataname[i]:
                    self.axPhy.plot(
                        data[i][colname[0]],
                        data[i][colname[2]],
                        "-",
                        linewidth=2,
                        label=dataname[i],
                    )
                else:
                    self.axPhy.scatter(
                        data[i][colname[0]],
                        data[i][colname[2]],
                        marker="x",
                        s=10,
                        label=dataname[i],
                    )
                has_data = True
            else:
                pass

        self.axPhy.set_xscale("log")
        self.axPhy.set_xlabel("Frequency [Hz]", fontsize=12)
        self.axPhy.set_ylabel("Phase [°]", fontsize=12)
        self.axPhy.tick_params(axis="both", labelsize=12)
        if has_data:
            self.axPhy.legend(loc="best")
        self.draw()
        print("plotPhy")
        # Bode-Phy#######

    def plotNyquist(self, outputlist, dataname, data, figpos):
        ##'Nyquist#########

        self.axNyquist = self.fig.add_subplot(figpos)
        self.axNyquist.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axNyquist.plot(
                        data[i][colname[3]],
                        data[i][colname[4]],
                        "--",
                        linewidth=2,
                        label=dataname[i],
                    )
                elif labelref[1] in dataname[i]:
                    self.axNyquist.plot(
                        data[i][colname[3]],
                        data[i][colname[4]],
                        "-",
                        linewidth=2,
                        label=dataname[i],
                    )
                else:
                    self.axNyquist.scatter(
                        data[i][colname[3]],
                        data[i][colname[4]],
                        marker="x",
                        s=10,
                        label=dataname[i],
                    )
                has_data = True
            else:
                pass

        self.axNyquist.set_xlabel("Rs [ohm]", fontsize=12)
        self.axNyquist.set_ylabel("X [ohm]", fontsize=12)
        self.axNyquist.tick_params(axis="both", labelsize=12)
        if has_data:
            self.axNyquist.legend(loc="best")
        self.axNyquist.invert_yaxis()

        self.draw()
        ##'Nyquist#########

    def plotZall(self, outputlist, dataname, data):
        self.fig.clear()
        print("Drawing figure...")
        figposRs = 221
        self.plotRs(outputlist, dataname, data, figposRs)

        figposX = 222
        self.plotX(outputlist, dataname, data, figposX)

        figposNyquist = 223
        self.plotNyquist(outputlist, dataname, data, figposNyquist)

        figposPhy = 224
        self.plotPhy(outputlist, dataname, data, figposPhy)

        self.fig.tight_layout()
        self.draw()
        print("plotALL")

        self.update()

    ##########################impedance################################################################################

    ############################permittivity#################################################################################

    def plotEps(self, outputlist, dataname, data, figpos):
        # Bode-Eps#######
        self.axEps = self.fig.add_subplot(figpos)
        self.axEps.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axEps.plot(
                        data[i][colname[0]],
                        data[i][colname[1]],
                        "--",
                        linewidth=2,
                        label=dataname[i],
                    )
                elif labelref[1] in dataname[i]:
                    self.axEps.plot(
                        data[i][colname[0]],
                        data[i][colname[1]],
                        "-",
                        linewidth=2,
                        label=dataname[i],
                    )
                else:
                    self.axEps.scatter(
                        data[i][colname[0]],
                        data[i][colname[1]],
                        marker="x",
                        s=50,
                        label=dataname[i],
                    )
                has_data = True
            else:
                pass

        self.axEps.set_xscale("log")
        self.axEps.set_xlabel("Frequency [Hz]", fontsize=12)
        self.axEps.set_ylabel("ε'", fontsize=12)
        self.axEps.tick_params(axis="both", labelsize=12)

        if has_data:
            self.axEps.legend(loc="best")

        self.draw()
        # Bode-Eps#######

    def plotSigma(self, outputlist, dataname, data, figpos):
        # Bode-X########

        self.axSigma = self.fig.add_subplot(figpos)
        self.axSigma.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axSigma.plot(
                        data[i][colname[0]],
                        data[i][colname[3]],
                        "--",
                        linewidth=2,
                        label=dataname[i],
                    )
                elif labelref[1] in dataname[i]:
                    self.axSigma.plot(
                        data[i][colname[0]],
                        data[i][colname[3]],
                        "-",
                        linewidth=2,
                        label=dataname[i],
                    )
                else:
                    self.axSigma.scatter(
                        data[i][colname[0]],
                        data[i][colname[3]],
                        marker="x",
                        s=50,
                        label=dataname[i],
                    )
                has_data = True
            else:
                pass

        self.axSigma.set_xscale("log")
        self.axSigma.set_xlabel("Frequency [Hz]", fontsize=12)
        self.axSigma.set_ylabel("σ' ", fontsize=12)
        self.axSigma.tick_params(axis="both", labelsize=12)

        if has_data:
            self.axSigma.legend(loc="best")

        self.draw()
        # Bode-X########

    def plotColeCole(self, outputlist, dataname, data, figpos):

        self.axColeCole = self.fig.add_subplot(figpos)
        self.axColeCole.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axColeCole.plot(
                        data[i][colname[3]],
                        data[i][colname[4]],
                        "--",
                        linewidth=2,
                        label=dataname[i],
                    )
                elif labelref[1] in dataname[i]:
                    self.axColeCole.plot(
                        data[i][colname[3]],
                        data[i][colname[4]],
                        "-",
                        linewidth=2,
                        label=dataname[i],
                    )
                else:
                    self.axColeCole.scatter(
                        data[i][colname[3]],
                        data[i][colname[4]],
                        marker="x",
                        s=50,
                        label=dataname[i],
                    )
                has_data = True
            else:
                pass
        self.axColeCole.set_xlabel("σ'", fontsize=12)
        self.axColeCole.set_ylabel("σ'' ", fontsize=12)
        self.axColeCole.tick_params(axis="both", labelsize=12)
        if has_data:
            self.axColeCole.legend(loc="best")

        # 设置横纵坐标
        ymin, ymax = self.axColeCole.get_ylim()  # 1. 获取纵轴范围
        y_range = ymax - ymin
        if y_range <= 0:
            y_range = 1  # 默认纵轴范围差为1
        xmax = y_range * 0.5
        self.axColeCole.set_xlim(0, xmax)

        self.draw()

    def plotTheta(self, outputlist, dataname, data, figpos):
        # Bode-Theta (介电损耗角)#######

        self.axTheta = self.fig.add_subplot(figpos)
        self.axTheta.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                # 计算介电损耗角: θ = arctan(ε''/ε')
                eps_real = data[i][colname[1]]  # ε' (实部)
                eps_imag = data[i][colname[2]]  # ε'' (虚部)

                # 避免除零错误，当ε'接近0时设置一个小值
                eps_real_safe = np.where(np.abs(eps_real) < 1e-10, 1e-10, eps_real)
                theta = np.arctan(eps_imag / eps_real_safe) * 180 / np.pi  # 转换为度

                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axTheta.plot(
                        data[i][colname[0]], theta, "--", linewidth=2, label=dataname[i]
                    )
                elif labelref[1] in dataname[i]:
                    self.axTheta.plot(
                        data[i][colname[0]], theta, "-", linewidth=2, label=dataname[i]
                    )
                else:
                    self.axTheta.scatter(
                        data[i][colname[0]], theta, marker="x", s=10, label=dataname[i]
                    )
                has_data = True
            else:
                pass

        self.axTheta.set_xscale("log")
        self.axTheta.set_xlabel("Frequency [Hz]", fontsize=12)
        self.axTheta.set_ylabel("Loss Angle θ [°]", fontsize=12)
        self.axTheta.tick_params(axis="both", labelsize=12)
        if has_data:
            self.axTheta.legend(loc="best")
        self.draw()
        print("plotTheta")
        # Bode-Theta#######

    def plotEpsall(self, outputlist, dataname, data):
        self.fig.clear()

        figposRs = 221
        self.plotEps(outputlist, dataname, data, figposRs)

        figposX = 222
        self.plotSigma(outputlist, dataname, data, figposX)

        figposNyquist = 223
        self.plotColeCole(outputlist, dataname, data, figposNyquist)

        figposTheta = 224
        self.plotTheta(outputlist, dataname, data, figposTheta)

        self.fig.tight_layout()
        self.draw()

    def plotEpsIM(self, outputlist, dataname, data, figpos):
        # Bode-Rs#######
        self.axEpsIM = self.fig.add_subplot(figpos)
        self.axEpsIM.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axEpsIM.plot(
                        data[i][colname[0]],
                        data[i][colname[2]],
                        "--",
                        linewidth=2,
                        label=dataname[i],
                    )
                elif labelref[1] in dataname[i]:
                    self.axEpsIM.plot(
                        data[i][colname[0]],
                        data[i][colname[2]],
                        "-",
                        linewidth=2,
                        label=dataname[i],
                    )
                else:
                    self.axEpsIM.scatter(
                        data[i][colname[0]],
                        data[i][colname[2]],
                        marker="x",
                        s=50,
                        label=dataname[i],
                    )
                has_data = True
            else:
                pass

        self.axEpsIM.set_xscale("log")
        self.axEpsIM.set_xlabel("Frequency [Hz]", fontsize=12)
        self.axEpsIM.set_ylabel("ε'", fontsize=12)
        self.axEpsIM.tick_params(axis="both", labelsize=12)
        if has_data:
            self.axEpsIM.legend(loc="best")

        self.draw()
        # Bode-Rs#######

    def plotSigmaIM(self, outputlist, dataname, data, figpos):
        # Bode-X########

        self.axSigmaIM = self.fig.add_subplot(figpos)
        self.axSigmaIM.grid(True)

        has_data = False
        for i in range(0, len(outputlist)):
            if outputlist[i] == 1:
                if i >= len(data) or data[i] is None or len(data[i]) == 0:
                    continue
                colname = list(data[i].columns)
                if labelref[0] in dataname[i] or labelref[2] in dataname[i]:
                    self.axSigmaIM.plot(
                        data[i][colname[0]],
                        data[i][colname[4]],
                        "--",
                        linewidth=2,
                        label=dataname[i],
                    )
                elif labelref[1] in dataname[i]:
                    self.axSigmaIM.plot(
                        data[i][colname[0]],
                        data[i][colname[4]],
                        "-",
                        linewidth=2,
                        label=dataname[i],
                    )
                else:
                    self.axSigmaIM.scatter(
                        data[i][colname[0]],
                        data[i][colname[4]],
                        marker="x",
                        s=50,
                        label=dataname[i],
                    )
                has_data = True
            else:
                pass

        self.axSigmaIM.set_xscale("log")
        self.axSigmaIM.set_xlabel("Frequency [Hz]", fontsize=12)
        self.axSigmaIM.set_ylabel("σ' ", fontsize=12)
        self.axSigmaIM.tick_params(axis="both", labelsize=12)

        if has_data:
            self.axSigmaIM.legend(loc="best")
        self.axSigmaIM.invert_yaxis()

        self.draw()
        # Bode-X########


############################permittivity#################################################################################


##################学术论文图表样式设置函数########################
def setup_academic_style():
    """
    设置适合学术论文的matplotlib样式
    """

    try:
        # 设置基本样式参数
        style_params = {
            # 字体设置
            "font.family": "serif",
            "font.size": 12,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "figure.titlesize": 16,
            # 解决Unicode减号字体警告
            "axes.unicode_minus": False,
            # 线条和标记样式
            "lines.linewidth": 1.5,
            "lines.markersize": 6,
            # 坐标轴样式
            "axes.linewidth": 1.0,
            "axes.grid": True,
            # 网格样式
            "grid.alpha": 0.3,
            "grid.linewidth": 0.5,
            # 刻度样式
            "xtick.major.size": 5,
            "xtick.minor.size": 3,
            "ytick.major.size": 5,
            "ytick.minor.size": 3,
            "xtick.direction": "in",
            "ytick.direction": "in",
            # 图形背景
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            # 保存参数
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.1,
            # 图例样式
            "legend.frameon": True,
            "legend.framealpha": 0.9,
            "legend.fancybox": False,
        }

        # 只更新有效的参数
        valid_params = {}
        for key, value in style_params.items():
            if key in plt.rcParams:
                valid_params[key] = value
            else:
                print(f"Warning: {key} is not a valid rcParam, skipping...")

        plt.rcParams.update(valid_params)
        print("Academic style applied successfully!")

    except Exception as e:
        print(f"Error applying academic style: {e}")
        print("Using default matplotlib style...")


def create_academic_canvas(width=10, height=8, dpi=150):
    """
    创建适合学术论文的画布并自动应用增强样式

    Parameters:
    width: 画布宽度
    height: 画布高度
    dpi: 分辨率
    Returns:
    canvas: 配置好的MyMplCanvas对象
    """
    # 应用学术样式
    setup_academic_style()

    # 创建画布，使用更适合论文的尺寸和DPI
    canvas = MyMplCanvas(width=width, height=height, dpi=dpi)

    # 设置背景为白色（避免与rcParams重复设置）
    canvas.fig.set_facecolor("white")

    return canvas


def save_publication_figure(
    canvas,
    filename=None,
    format="tiff",
    dpi=300,
    parent=None,
    show_dialog=False,
    save_mode="dialog",
):
    """
    保存适合发表的高质量图形

    Parameters:
    canvas: MyMplCanvas对象
    filename: 保存文件名
    format: 保存格式 ('png', 'tiff', 'pdf')
    dpi: 分辨率
    parent: 父窗口（用于文件对话框和消息显示）
    show_dialog: 是否显示文件保存对话框（已弃用，使用save_mode代替）
    save_mode: 保存模式 ('dialog'=显示对话框, 'direct'=直接保存到Results文件夹)
    """

    try:
        if save_mode == "dialog":
            # 模式1：显示文件保存对话框，用户选择保存位置
            if filename is None:
                dt = datetime.now()
                filename = f"academic_plot_{dt.strftime('%Y%m%d_%H%M%S')}"

            # 显示文件保存对话框
            file_path, selected_filter = QFileDialog.getSaveFileName(
                parent,
                "Save Figure As",
                f"Results/{filename}.{format}",
                "TIFF files (*.tiff);;PNG files (*.png);;PDF files (*.pdf)",
            )

            if not file_path:
                return None  # 用户取消了保存

            # 从文件路径中提取文件名和格式
            filename_with_ext = os.path.basename(file_path)
            filename, ext = os.path.splitext(filename_with_ext)
            format = ext[1:] if ext else format  # 去掉点号

            # 使用用户选择的完整路径
            filepath = file_path

        else:
            # 模式2：直接保存到Results文件夹（与saveasexcel相同位置）
            if filename is None:
                dt = datetime.now()
                filename = f"Python_plot_{dt.strftime('%Y%m%d_%H%M%S')}"

            # 确保Results文件夹存在
            results_dir = "Results"
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)

            # 完整文件路径
            filepath = os.path.join(results_dir, f"{filename}.{format}")

        # 保存图形
        canvas.fig.savefig(
            filepath,
            format=format,
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.1,
            facecolor="white",
            edgecolor="none",
        )

        print(f"Figure saved to: {filepath}")

        # 显示成功消息
        if parent:
            if save_mode == "dialog":
                QMessageBox.information(
                    parent, "Success", f"Figure saved to: {filepath}"
                )
            else:
                QMessageBox.information(
                    parent,
                    "Success",
                    f"Figure saved to Results folder: {os.path.basename(filepath)}",
                )

        return filepath

    except Exception as e:
        print(f"Failed to save image: {str(e)}")
        if parent:
            QMessageBox.critical(parent, "Error", f"Failed to save image: {str(e)}")
        return None


##################误差分析绘图函数########################


def plot_multi_dataset_results(
    self, error_df_list, stats_list, error_stats, stats_summary
):
    """
    绘制多数据集误差分析结果

    Parameters:
    error_df_list: 相对误差DataFrame列表(每个 entry 对应一个 comp_data vs base)
    stats_list: 统计分析DataFrame列表 [mean_df, variance_df, std_df, cv_df]
    error_stats: 误差统计信息
    stats_summary: 统计摘要信息
    """
    if not hasattr(self, "mpl") or not hasattr(self.mpl, "fig"):
        print("Warning: mpl.fig not available")
        return

    # 清除图形并创建子图
    self.mpl.fig.clear()

    # 创建2x2的子图布局
    subplot_positions = [221, 222, 223, 224]

    # 绘制相对误差(只以第一组数据为基准计算,即 error_df_list[0])
    # 多个 comp_data 会导致图例条目过多(每 comp_data 贡献 4 条曲线),故仅保留第一组
    if error_df_list and len(error_df_list) > 0:
        ax1 = self.mpl.fig.add_subplot(subplot_positions[0])
        plot_analysis_unified(
            ax1, error_df_list[0], "Relative Error Analysis", column_filter="RelErr"
        )

    # 绘制统计分析（如果有数据）
    if stats_list and len(stats_list) >= 4:
        # 绘制变异系数 (CV%)
        ax2 = self.mpl.fig.add_subplot(subplot_positions[1])
        plot_analysis_unified(
            ax2,
            stats_list[3],
            "Coefficient of Variation (%)",
            column_filter="CV%",
            linewidth=2,
            markersize=4,
        )

        # 绘制标准差
        ax3 = self.mpl.fig.add_subplot(subplot_positions[2])
        plot_analysis_unified(
            ax3,
            stats_list[2],
            "Standard Deviation",
            column_filter="StdDev",
            markersize=4,
        )

        # 绘制均值
        ax4 = self.mpl.fig.add_subplot(subplot_positions[3])
        plot_analysis_unified(
            ax4, stats_list[0], "Mean Values", column_filter="Mean", markersize=4
        )

    # 调整布局并绘制
    self.mpl.fig.tight_layout()
    self.mpl.draw()


def plot_single_dataset_results(
    self, stats_dfs_list, single_stats_summary, dataset_name
):
    """
    绘制单数据集统计分析结果

    Parameters:
    stats_dfs_list: 包含两个DataFrame的列表 [rolling_std_df, relative_deviation_df]
    single_stats_summary: 单数据集统计摘要
    dataset_name: 数据集名称
    """
    if not hasattr(self, "mpl") or not hasattr(self.mpl, "fig"):
        print("Warning: mpl.fig not available")
        return

    # 清除图形并创建子图
    self.mpl.fig.clear()

    if len(stats_dfs_list) >= 2:
        # 创建1x2的子图布局
        ax1 = self.mpl.fig.add_subplot(121)
        plot_analysis_unified(
            ax1,
            stats_dfs_list[0],
            f"Rolling Standard Deviation - {dataset_name}",
            column_filter="RollingStd",
        )

        ax2 = self.mpl.fig.add_subplot(122)
        plot_analysis_unified(
            ax2,
            stats_dfs_list[1],
            f"Relative Deviation (%) - {dataset_name}",
            column_filter="RelDeviation%",
        )
    else:
        # 如果只有一个DataFrame，使用整个图形
        ax = self.mpl.fig.add_subplot(111)
        plot_analysis_unified(
            ax,
            stats_dfs_list[0],
            f"Statistical Analysis - {dataset_name}",
            column_filter="RollingStd",
        )

    # 调整布局并绘制
    self.mpl.fig.tight_layout()
    self.mpl.draw()


def plot_analysis_unified(
    ax,
    data_df,
    title,
    ylabel=None,
    column_filter=None,
    marker_style="o",
    linewidth=1.5,
    markersize=3,
):
    """
    统一的分析绘图函数，替代所有重复的绘图函数

    Parameters:
    ax: matplotlib轴对象
    data_df: 数据DataFrame
    title: 图表标题
    ylabel: Y轴标签（如果为None，从title自动推断）
    column_filter: 列名过滤关键词（如果为None，绘制所有非x轴列）
    marker_style: 标记样式
    linewidth: 线宽
    markersize: 标记大小
    """
    ax.grid(True)
    columns = list(data_df.columns)
    x_col = columns[0]

    # 默认颜色序列
    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
    ]

    # 标记样式映射
    marker_map = {
        "RelErr": "o",
        "CV%": "s",
        "StdDev": "^",
        "Mean": "d",
        "RollingStd": "o",
        "RelDeviation%": "s",
    }

    color_idx = 0

    for col in columns[1:]:
        # 如果指定了列过滤器，只绘制匹配的列
        if column_filter and column_filter not in col:
            continue
        # 如果没有指定过滤器，绘制所有非x轴列
        elif column_filter is None:
            pass

        # 根据列名选择合适的标记样式
        current_marker = marker_style
        for key, marker in marker_map.items():
            if key in col:
                current_marker = marker
                break

        color = colors[color_idx % len(colors)]
        ax.plot(
            data_df[x_col],
            data_df[col],
            color=color,
            linewidth=linewidth,
            label=col,
            marker=current_marker,
            markersize=markersize,
        )
        color_idx += 1

    # 设置标签
    ax.set_xlabel(x_col, fontsize=10)

    # 自动推断Y轴标签
    if ylabel is None:
        if "Error" in title:
            ylabel = "Relative Error (%)"
        elif "Coefficient" in title or "CV" in title:
            ylabel = "CV (%)"
        elif "Standard Deviation" in title or "Std" in title:
            ylabel = "Standard Deviation"
        elif "Mean" in title:
            ylabel = "Mean Values"
        elif "Rolling" in title:
            ylabel = "Rolling Standard Deviation"
        elif "Deviation" in title:
            ylabel = "Relative Deviation (%)"
        else:
            ylabel = "Values"

    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=10)

    # 如果x轴是频率，使用对数刻度
    if "FREQ" in x_col.upper() or "Hz" in x_col:
        ax.set_xscale("log")

    # 添加图例
    if len(columns) > 1:
        ax.legend(loc="best", fontsize=8)
