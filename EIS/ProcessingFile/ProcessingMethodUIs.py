from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtWidgets import QWidget, QFrame, QComboBox
from PySide6.QtCore import QSize

from widgets.py_push_button.py_push_button2 import PyPushButton2    # 自定义按钮
from widgets.py_table_widget.py_table_widget2 import PyTableWidget2  # 自定义表格组件
from widgets.py_line_edit.py_line_edit2 import PyLineEdit2          # 自定义输入框
from widgets.py_qcheckbox.py_qcheckbox2 import PyCheckBox2         # 自定义复选框
from widgets.py_combobox.py_combobox2 import PyComboBox2           # 自定义下拉框
from widgets.py_label.py_label2 import PyLabel2
from widgets.py_line_edit.py_line_edit2 import PyLineEdit2    


class ProcessingMethodUIs:
    def __init__(self, parent):
        self.parent = parent
        self.settings = parent.settings
        self.themes = parent.themes

    def ui_calibration(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(3)
        refdataname = ['Open', 'Short', 'Load']

        # Create calibration units without solution/concentration/temperature controls
        for i in range(3):
            unitContainer = QWidget()
            unitLayout = QVBoxLayout(unitContainer)
            unitLayout.setSpacing(5)
            unitLayout.setContentsMargins(0, 0, 0, 0)

            # Only the first row with buttons
            unitRow1 = QWidget()
            unitRow1.setFixedHeight(40)
            unitRow1Layout = QHBoxLayout(unitRow1)
            unitRow1Layout.setSpacing(10)
            unitRow1Layout.setContentsMargins(0, 0, 0, 0)

            self.parent.refdataBtn[i] = PyPushButton2(
                text=refdataname[i],
                font_size=self.settings["font"]["text_size_normal"],
                font_weight=700,
                radius=4,
                font_color=self.themes["app_color"]["white"],
                bg_color=self.themes["app_color"]["purple_blue"],
                bg_color_hover=self.themes["app_color"]["purple_blue_hover"],
                bg_color_pressed=self.themes["app_color"]["purple_blue_pressed"],
                border_color="transparent",
            )
            self.parent.refdataBtn[i].setFixedHeight(40)
            self.parent.refdataBtn[i].setMinimumWidth(120)
            setattr(self.parent, f'refdataBtn{i}_effect', self.parent.setup_button_hover_effect(self.parent.refdataBtn[i]))
            unitRow1Layout.addWidget(self.parent.refdataBtn[i])

            self.parent.refdataComboBox[i] = PyComboBox2(
            color=self.themes["app_color"]["text_foreground"],
            radius=4,  # 使用HTML中的border-radius: 4px
            font_size=self.settings["font"]["text_size_small"],
            font_weight=700,
            min_height=35,
            bg_color=self.themes["app_color"]["bg_two"],  # 使用白色背景
            bg_color_hover=self.themes["app_color"]["light_three"],
            bg_color_pressed=self.themes["app_color"]["context_hover"],
            selection_color=self.themes["app_color"]["context_pressed"],
            border_color=self.themes["app_color"]["light_three"],  # 使用浅色边框
             )
            unitRow1Layout.addWidget(self.parent.refdataComboBox[i])

            self.parent.openreffilebtn[i] = PyPushButton2(
                text="Open File",
                font_size=self.settings["font"]["text_size_normal"],
                font_weight=700,
                radius=4,
                font_color=self.themes["app_color"]["white"],
                bg_color=self.themes["app_color"]["context_color"],
                bg_color_hover=self.themes["app_color"]["context_hover"],
                bg_color_pressed=self.themes["app_color"]["context_pressed"],
                border_color="transparent",
            )
            self.parent.openreffilebtn[i].setFixedHeight(40)
            self.parent.openreffilebtn[i].setMinimumWidth(100)
            setattr(self.parent, f'openreffilebtn{i}_effect', self.parent.setup_button_hover_effect(self.parent.openreffilebtn[i]))
            unitRow1Layout.addWidget(self.parent.openreffilebtn[i])

            self.parent.deletereffilebtn[i] = PyPushButton2(
                text="Delete File",
                font_size=self.settings["font"]["text_size_normal"],
                font_weight=700,
                radius=4,
                font_color=self.themes["app_color"]["white"],
                bg_color = self.themes["app_color"]["red_primary"],
                bg_color_hover = self.themes["app_color"]["red_hover"],
                bg_color_pressed = self.themes["app_color"]["red_pressed"],
                border_color="transparent",
            )
            self.parent.deletereffilebtn[i].setFixedHeight(40)
            self.parent.deletereffilebtn[i].setMinimumWidth(100)
            setattr(self.parent, f'deletereffilebtn{i}_effect', self.parent.setup_button_hover_effect(self.parent.deletereffilebtn[i]))
            unitRow1Layout.addWidget(self.parent.deletereffilebtn[i])

            unitLayout.addWidget(unitRow1)
            self.parent.DPsublayout2.addWidget(unitContainer)
            
            # Connect signals for this specific button after creation
            if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
                # 使用闭包来捕获当前的i值，避免lambda的延迟绑定问题
                self.parent.refdataBtn[i].clicked.connect(lambda checked, n=i: self.parent.parent_processing_instance.GetrefFiles(n + 1))
                self.parent.openreffilebtn[i].clicked.connect(lambda checked, n=i: self.parent.parent_processing_instance.OpenFiles(n + 1))
                self.parent.deletereffilebtn[i].clicked.connect(lambda checked, n=i: self.parent.parent_processing_instance.ClearrefFiles(n + 1))

        # [适用条件] System Calibration 是 OSL 三步校准 (Open/Short/Load):
        # Z_MUT = Z_std·(Z_short−Z_meas)·(Z_load−Z_open) / [(Z_meas−Z_open)·(Z_short−Z_load)]
        # 与 TLcalibrate 不同:不需要已知介电参数,但需要三组标准件参考测量。
        # 限制:当 Z_meas → Z_open 时公式退化 (分母→0);Load 阻抗需已知 (默认 50 Ω)。
        from PySide6.QtWidgets import QLabel
        self.syscal_note = QLabel(
            "⚠ System Calibration applicability: requires 3 reference standards (Open, Short, Load=50 Ω)\n"
            "   OSL formula: Z_MUT = Z_std·(Z_short−Z_meas)·(Z_load−Z_open) / [(Z_meas−Z_open)·(Z_short−Z_load)].\n"
            "   Degrades when Z_meas ≈ Z_open (denominator → 0). No dielectric parameters needed, "
            "applicable from low frequency to GHz; use TLcalibrate if reference solution (e.g. NaCl) is preferred."
        )
        self.syscal_note.setStyleSheet(
            "color: #aa6600; background-color: #fff8e1; "
            "padding: 6px; border: 1px solid #e0c080; border-radius: 4px;"
        )
        self.syscal_note.setWordWrap(True)
        self.parent.DPsublayout2.addWidget(self.syscal_note)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

    def ui_ParallelPlate(self):
        self.parent.freshprocessUI()
        
        # Add geometric constant input
        ppContainer = QWidget()
        ppContainer.setFixedHeight(40)
        ppLayout = QHBoxLayout(ppContainer)
        ppLayout.setSpacing(10)
        ppLayout.setContentsMargins(0, 0, 0, 0)

        self.parent.GeomconstantLineEdit = PyLabel2(
            text="Geometric constant:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        ppLayout.addWidget(self.parent.GeomconstantLineEdit)

        self.parent.GeomconstantTextEdit = PyLineEdit2(
            text='',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.GeomconstantTextEdit.setFixedHeight(40)
        ppLayout.addWidget(self.parent.GeomconstantTextEdit)

        ppLayout.addStretch()
        self.parent.DPsublayout2.addWidget(ppContainer)

        # [适用条件] Parallel Plate Capacitor 直接由 Z(ω) 反演 ε、σ:
        #     εr = 1/(jω·ε0·Gf·Z),  σ = 1/(Gf·Z)   (平行板 R‖C 物理模型, TP-001/TP-008)
        # 假设:电极间为均匀介质,无引线电感,无接触电阻。
        # 适用:低/中频段 (< 100 MHz),薄膜/低损样品;
        #     不适用:含电极极化的电解池 (高 σ 溶液,例如 NaCl > 0.1M) — 请改用 TL 系列。
        from PySide6.QtWidgets import QLabel
        self.pp_note = QLabel(
            "⚠ Parallel Plate Capacitor applicability: requires only Gf; assumes uniform R‖C medium\n"
            "   Formula: εᵣ = 1/(jω·ε₀·Gf·Z),  σ = 1/(Gf·Z)   (lossless plate-capacitor model).\n"
            "   Valid for thin films / low-loss samples (f < 100 MHz). Not suitable for conductive "
            "electrolytes with electrode polarization — use TL series instead."
        )
        self.pp_note.setStyleSheet(
            "color: #aa6600; background-color: #fff8e1; "
            "padding: 6px; border: 1px solid #e0c080; border-radius: 4px;"
        )
        self.pp_note.setWordWrap(True)
        self.parent.DPsublayout2.addWidget(self.pp_note)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()


    def ui_DielectricMaterial(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(2)
        # 第一个参考固定为 Air,第二个固定为 Water(DieMat 仅支持 Air+Water)
        refdataname_air = ['Air']
        refdataname_water = ['Water']
        self.parent.uiUnit(0, 2, refdataname_air)
        self.parent.uiUnit(1, 2, refdataname_water)

        # 第一个参考:固定 Air,禁用 combobox 和浓度
        if 0 in self.parent.refsoluionComboBox:
            self.parent.refsoluionComboBox[0].setCurrentIndex(0)
            self.parent.refsoluionComboBox[0].setEnabled(False)
        if 0 in self.parent.concentrationTextEdit:
            self.parent.concentrationTextEdit[0].setText('0')
            self.parent.concentrationTextEdit[0].setEnabled(False)
        if 0 in self.parent.concentrationLineEdit:
            self.parent.concentrationLineEdit[0].setEnabled(False)
        if 0 in self.parent.concentrationUnitLineEdit:
            self.parent.concentrationUnitLineEdit[0].setEnabled(False)

        # 第二个参考:固定 Water,禁用 combobox 和浓度
        if 1 in self.parent.refsoluionComboBox:
            self.parent.refsoluionComboBox[1].setCurrentIndex(0)
            self.parent.refsoluionComboBox[1].setEnabled(False)
        if 1 in self.parent.concentrationTextEdit:
            self.parent.concentrationTextEdit[1].setText('0')
            self.parent.concentrationTextEdit[1].setEnabled(False)
        if 1 in self.parent.concentrationLineEdit:
            self.parent.concentrationLineEdit[1].setEnabled(False)
        if 1 in self.parent.concentrationUnitLineEdit:
            self.parent.concentrationUnitLineEdit[1].setEnabled(False)

        # [TP-002] Applicable conditions (static warning)
        # DieMat assumes L=0, R=0, only suitable for f < 1 MHz on conductive electrolytes.
        # At higher frequencies, use Three-Solution or Transmission Line methods instead.
        from PySide6.QtWidgets import QLabel
        self.dm_freq_note = QLabel(
            "⚠ DieMat applicability: f < 1 MHz, conductive electrolytes (aqueous, biological tissue)\n"
            "   At higher frequencies (f ≥ 1 MHz) errors become significant; "
            "use Three-Solution or Transmission Line instead."
        )
        self.dm_freq_note.setStyleSheet(
            "color: #aa6600; background-color: #fff8e1; "
            "padding: 6px; border: 1px solid #e0c080; border-radius: 4px;"
        )
        self.dm_freq_note.setWordWrap(True)
        self.parent.DPsublayout2.addWidget(self.dm_freq_note)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

        

    def _apply_ref_solution_rules(self, num):
        """
        根据当前 refsoluionComboBox[num] 的选择,自动调整浓度输入框的状态和单位。

        规则:
            - "Water"  : 浓度禁用 + 写 0(纯水无浓度概念),单位保持 "mol/L"
            - "Ethanol": 浓度启用,单位切到 "vol%"(体积分数)
            - 其他      : 浓度启用,单位 "mol/L"
        """
        if num not in self.parent.refsoluionComboBox:
            return
        sol = self.parent.refsoluionComboBox[num].currentText().strip()

        conc_edit = self.parent.concentrationTextEdit.get(num)
        conc_label = self.parent.concentrationLineEdit.get(num)
        conc_unit = self.parent.concentrationUnitLineEdit.get(num)

        if sol == 'Water':
            if conc_edit is not None:
                conc_edit.setText('0')
                conc_edit.setEnabled(False)
            if conc_label is not None:
                conc_label.setEnabled(False)
            if conc_unit is not None:
                conc_unit.setEnabled(False)
                conc_unit.setText('mol/L')
        elif sol == 'Ethanol':
            if conc_edit is not None:
                conc_edit.setEnabled(True)
            if conc_label is not None:
                conc_label.setEnabled(True)
            if conc_unit is not None:
                conc_unit.setEnabled(True)
                conc_unit.setText('vol%')
        else:  # NaCl 等需要 mol/L 浓度的参考液
            if conc_edit is not None:
                conc_edit.setEnabled(True)
            if conc_label is not None:
                conc_label.setEnabled(True)
            if conc_unit is not None:
                conc_unit.setEnabled(True)
                conc_unit.setText('mol/L')

    def ui_ThreeSolution(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(3)
        refdataname = ['NaCl', 'Water', 'Ethanol']
        self.parent.uiUnit(0, 2, refdataname)
        self.parent.uiUnit(1, 2, refdataname)
        self.parent.uiUnit(2, 2, refdataname)

        # 根据 ref 液类型自动调整浓度输入框:Water→禁用,Ethanol→vol%
        for i in range(3):
            if i in self.parent.refsoluionComboBox:
                self.parent.refsoluionComboBox[i].currentIndexChanged.connect(
                    lambda _idx, n=i: self._apply_ref_solution_rules(n)
                )
                # 初始应用一次
                self._apply_ref_solution_rules(i)

        # [适用条件] Three-Solution Method 用三种不同浓度/类型的参考液 (NaCl/Water/Ethanol)
        # 反演未知样品的 ε、σ。插值用 Z(实测差异 < 0.0001%, TP-004 已确认低优先级);
        # 也可使用 threesolutions_Y (Y 插值) 作为对照。
        # 适用:宽频段 (10 kHz - 10 MHz),适合含电极极化的导电样品;
        #     不需要几何参数,但需要三组参考液校准。
        from PySide6.QtWidgets import QLabel
        self.ts_note = QLabel(
            "⚠ Three-Solution Method applicability: requires 3 reference solutions (NaCl/Water/Ethanol)\n"
            "   Inverse problem: 3 ref. solutions + interpolation (Z-based, threesolutions_Y available) "
            "to recover ε(ω) and σ(ω) of unknown sample.\n"
            "   Valid for 10 kHz - 10 MHz, suitable for conductive electrolytes. No geometric parameter "
            "needed, but the 3 references must have well-separated (ε, σ)."
        )
        self.ts_note.setStyleSheet(
            "color: #aa6600; background-color: #fff8e1; "
            "padding: 6px; border: 1px solid #e0c080; border-radius: 4px;"
        )
        self.ts_note.setWordWrap(True)
        self.parent.DPsublayout2.addWidget(self.ts_note)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()






    def ui_TransmissionLine(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(1)
        refdataname = ['NaCl', 'Water', 'Ethanol', 'Air']
        self.parent.uiUnit(0, 2, refdataname)

        # 根据 ref 液类型自动调整浓度输入框:Water→禁用,Ethanol→vol%,Air→禁用
        if 0 in self.parent.refsoluionComboBox:
            self.parent.refsoluionComboBox[0].currentIndexChanged.connect(
                lambda _idx, n=0: self._apply_ref_solution_rules(n)
            )
            self._apply_ref_solution_rules(0)

        # Add transmission line specific parameters
        tlContainer = QWidget()
        tlLayout = QVBoxLayout(tlContainer)
        tlLayout.setSpacing(5)
        tlLayout.setContentsMargins(0, 0, 0, 0)

        # First row - Geometric constant and Character Impedance
        tlRow1 = QWidget()
        tlRow1.setFixedHeight(40)
        tlRow1Layout = QHBoxLayout(tlRow1)
        tlRow1Layout.setSpacing(10)
        tlRow1Layout.setContentsMargins(0, 0, 0, 0)

        self.parent.GeomconstantLineEdit = PyLabel2(
            text="Geometric constant:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.GeomconstantLineEdit)

        self.parent.GeomconstantTextEdit = PyLineEdit2(
            text='3.874',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.GeomconstantTextEdit.setFixedHeight(40)
        tlRow1Layout.addWidget(self.parent.GeomconstantTextEdit)

        self.parent.CharaImpedanceLineEdit = PyLabel2(
            text="Character Impedance:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.CharaImpedanceLineEdit)

        self.parent.CharaImpedanceTextEdit = PyLineEdit2(
            text='50',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.CharaImpedanceTextEdit.setFixedHeight(40)
        tlRow1Layout.addWidget(self.parent.CharaImpedanceTextEdit)

        self.parent.CharaImpedanceUnitLineEdit = PyLabel2(
            text="Ω",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.CharaImpedanceUnitLineEdit)

        tlLayout.addWidget(tlRow1)

        # Second row - Electrode Length and Solution Length
        tlRow2 = QWidget()
        tlRow2.setFixedHeight(40)
        tlRow2Layout = QHBoxLayout(tlRow2)
        tlRow2Layout.setSpacing(10)
        tlRow2Layout.setContentsMargins(0, 0, 0, 0)

        self.parent.ElectLengthLineEdit = PyLabel2(
            text="Electorde Length:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.ElectLengthLineEdit)

        self.parent.ElectLengthTextEdit = PyLineEdit2(
            text='0.0164',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.ElectLengthTextEdit.setFixedHeight(40)
        tlRow2Layout.addWidget(self.parent.ElectLengthTextEdit)

        self.parent.ElectLengthUnitLineEdit = PyLabel2(
            text="mm",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.ElectLengthUnitLineEdit)

        self.parent.SoluLengthLineEdit = PyLabel2(
            text="Solution Length:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengthLineEdit)

        self.parent.SoluLengtTextEdit = PyLineEdit2(
            text='0.002',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.SoluLengtTextEdit.setFixedHeight(40)
        tlRow2Layout.addWidget(self.parent.SoluLengtTextEdit)

        self.parent.SoluLengtUnitLineEdit = PyLabel2(
            text="mm",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengtUnitLineEdit)

        tlLayout.addWidget(tlRow2)
        self.parent.DPsublayout2.addWidget(tlContainer)

        # [TP-006 适用条件] TLcalibrate 用参考液反推 γCable,在高频段 (γl 饱和)
        # 反推的 γCable 和去嵌入的 Z_mut 可能返回 NaN。
        # 适用:低/中频段 (f < 1 GHz) + 已知参考液 (NaCl/Water/Ethanol/Air)。
        from PySide6.QtWidgets import QLabel
        self.tlcal_note = QLabel(
            "ℹ RF Impedance Calibration: uses a reference solution and the transmission-line model to back-solve cable parameters γCable and de-embed, recovering the sample's port impedance Z_mut.\n"
            "⚠ RF Impedance Calibration applicability: f < 1 GHz, known reference solution required\n"
            "   At higher frequencies (f ≥ 1 GHz) γ·l saturates and tanh/arctanh become numerically unstable; "
            "the recovered Z_mut will be marked NaN. Use TLcalculateEIS (forward) for verification."
        )
        self.tlcal_note.setStyleSheet(
            "color: #aa6600; background-color: #fff8e1; "
            "padding: 6px; border: 1px solid #e0c080; border-radius: 4px;"
        )
        self.tlcal_note.setWordWrap(True)
        self.parent.DPsublayout2.addWidget(self.tlcal_note)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()


    def ui_TransmissionLine_cal(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(1)

        # Add transmission line specific parameters
        tlContainer = QWidget()
        tlLayout = QVBoxLayout(tlContainer)
        tlLayout.setSpacing(5)
        tlLayout.setContentsMargins(0, 0, 0, 0)

        # First row - Geometric constant and Character Impedance
        tlRow1 = QWidget()
        tlRow1.setFixedHeight(40)
        tlRow1Layout = QHBoxLayout(tlRow1)
        tlRow1Layout.setSpacing(10)
        tlRow1Layout.setContentsMargins(0, 0, 0, 0)

        self.parent.GeomconstantLineEdit = PyLabel2(
            text="Geometric constant:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.GeomconstantLineEdit)

        self.parent.GeomconstantTextEdit = PyLineEdit2(
            text='3.874',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.GeomconstantTextEdit.setFixedHeight(40)
        tlRow1Layout.addWidget(self.parent.GeomconstantTextEdit)



        tlLayout.addWidget(tlRow1)

        # Second row - Electrode Length and Solution Length
        tlRow2 = QWidget()
        tlRow2.setFixedHeight(40)
        tlRow2Layout = QHBoxLayout(tlRow2)
        tlRow2Layout.setSpacing(10)
        tlRow2Layout.setContentsMargins(0, 0, 0, 0)




        self.parent.SoluLengthLineEdit = PyLabel2(
            text="Solution Length:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengthLineEdit)

        self.parent.SoluLengtTextEdit = PyLineEdit2(
            text='0.00255',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.SoluLengtTextEdit.setFixedHeight(40)
        tlRow2Layout.addWidget(self.parent.SoluLengtTextEdit)

        self.parent.SoluLengtUnitLineEdit = PyLabel2(
            text="mm",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengtUnitLineEdit)

        tlLayout.addWidget(tlRow2)
        self.parent.DPsublayout2.addWidget(tlContainer)

        # [适用条件] TLcalculateEPS 是传输线反问题:已知校准后的 Z(ω) → 求 ε(ω)。
        # 前提:需要先调用 RF Impedance Calibration 校准 (TLcalibrate) 得到去嵌入的 Z。
        # 算法:用 mpmath.findroot 数值反求,已应用双初值策略 (30 + paraplate 复数初值)
        # 提升极端 ε' 样品的收敛性 (TP-007 修复)。
        # 限制:依赖校准结果,高频段 (γl 饱和) 输入 Z 失效,需在该频段使用其他方法。
        from PySide6.QtWidgets import QLabel
        self.tlcaldiel_note = QLabel(
            "ℹ RF Dielectric Calculation: inverse transmission-line problem — given the calibrated Z(ω), solve for the sample's complex permittivity ε(ω).\n"
            "⚠ RF Dielectric Calculation applicability: requires prior TLcalibrate (Open/NaCl reference)\n"
            "   Inverse problem: Z(ω) → ε(ω) via mpmath.findroot, with dual-initial-guess "
            "(ε=30 + ε_paraplate) for robust convergence on extreme samples.\n"
            "   Depends on calibrated Z; high-frequency band (γ·l saturates) will propagate NaN. "
            "Pair with TLcalculateEIS (forward) for ε → Z → ε round-trip verification."
        )
        self.tlcaldiel_note.setStyleSheet(
            "color: #aa6600; background-color: #fff8e1; "
            "padding: 6px; border: 1px solid #e0c080; border-radius: 4px;"
        )
        self.tlcaldiel_note.setWordWrap(True)
        self.parent.DPsublayout2.addWidget(self.tlcaldiel_note)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()


    def ui_TransmissionLine_EIScal(self):
        self.parent.freshprocessUI()
        self.parent.defbuttn()
        # Initialize refdata and refdataname lists with proper size
        if hasattr(self.parent, 'parent_processing_instance') and self.parent.parent_processing_instance:
            self.parent.parent_processing_instance.clearrefdata(1)

        # Add transmission line specific parameters
        tlContainer = QWidget()
        tlLayout = QVBoxLayout(tlContainer)
        tlLayout.setSpacing(5)
        tlLayout.setContentsMargins(0, 0, 0, 0)

        # First row - Geometric constant and Character Impedance
        tlRow1 = QWidget()
        tlRow1.setFixedHeight(40)
        tlRow1Layout = QHBoxLayout(tlRow1)
        tlRow1Layout.setSpacing(10)
        tlRow1Layout.setContentsMargins(0, 0, 0, 0)

        self.parent.GeomconstantLineEdit = PyLabel2(
            text="Geometric constant:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow1Layout.addWidget(self.parent.GeomconstantLineEdit)

        self.parent.GeomconstantTextEdit = PyLineEdit2(
            text='3.874',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.GeomconstantTextEdit.setFixedHeight(40)
        tlRow1Layout.addWidget(self.parent.GeomconstantTextEdit)



        tlLayout.addWidget(tlRow1)

        # Second row - Electrode Length and Solution Length
        tlRow2 = QWidget()
        tlRow2.setFixedHeight(40)
        tlRow2Layout = QHBoxLayout(tlRow2)
        tlRow2Layout.setSpacing(10)
        tlRow2Layout.setContentsMargins(0, 0, 0, 0)




        self.parent.SoluLengthLineEdit = PyLabel2(
            text="Solution Length:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengthLineEdit)

        self.parent.SoluLengtTextEdit = PyLineEdit2(
            text='0.00255',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.SoluLengtTextEdit.setFixedHeight(40)
        tlRow2Layout.addWidget(self.parent.SoluLengtTextEdit)

        self.parent.SoluLengtUnitLineEdit = PyLabel2(
            text="mm",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        tlRow2Layout.addWidget(self.parent.SoluLengtUnitLineEdit)

        tlLayout.addWidget(tlRow2)
        self.parent.DPsublayout2.addWidget(tlContainer)

        # [适用条件] TLcalculateEIS 是传输线正演:已知 ε(ω) → 求 Z(ω)。
        # 输入要求:prodata 必须含 EpsRE/EpsIM 字段 (即 check5='DS')。
        # 与 RF Dielectric Calculation (反问题: Z → ε) 互为正/反操作,
        # 主要用于材料模型验证、合成数据生成、或拟合流程中的正演模型。
        from PySide6.QtWidgets import QLabel
        self.tleis_note = QLabel(
            "ℹ RF Impedance Calculation: forward transmission-line model — given the sample's complex permittivity ε(ω), compute the port impedance Z(ω).\n"
            "⚠ RF Impedance Calculation applicability: prodata must contain EpsRE/EpsIM (dielectric spectrum)\n"
            "   Forward model: Z(ω) = (η/Gf) / tanh(γ·ls) with γ = jω√(με). "
            "Pair with RF Dielectric Calculation (inverse) for ε → Z → ε consistency checks."
        )
        self.tleis_note.setStyleSheet(
            "color: #aa6600; background-color: #fff8e1; "
            "padding: 6px; border: 1px solid #e0c080; border-radius: 4px;"
        )
        self.tleis_note.setWordWrap(True)
        self.parent.DPsublayout2.addWidget(self.tleis_note)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()


    def uiKKDS(self):
        """UI for K-K for DS method"""
        self.parent.freshprocessUI()
        
        # Add K-K for DS specific parameters
        kkdsContainer = QWidget()
        kkdsLayout = QVBoxLayout(kkdsContainer)
        kkdsLayout.setSpacing(5)
        kkdsLayout.setContentsMargins(0, 0, 0, 0)

        # Parameter input row
        paramRow = QWidget()
        paramRow.setFixedHeight(40)
        paramLayout = QHBoxLayout(paramRow)
        paramLayout.setSpacing(10)
        paramLayout.setContentsMargins(0, 0, 0, 0)

        self.parent.kkdsParamLabel = PyLabel2(
            text="K-K Parameters:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        paramLayout.addWidget(self.parent.kkdsParamLabel)

        self.parent.kkdsParamEdit = PyLineEdit2(
            text='',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.kkdsParamEdit.setFixedHeight(40)
        paramLayout.addWidget(self.parent.kkdsParamEdit)

        paramLayout.addStretch()
        kkdsLayout.addWidget(paramRow)
        self.parent.DPsublayout2.addWidget(kkdsContainer)
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

    def uiKKEIS(self):
        """UI for K-K for EIS method"""
        self.parent.freshprocessUI()
        
        # Add K-K for EIS specific parameters
        kkeisContainer = QWidget()
        kkeisLayout = QVBoxLayout(kkeisContainer)
        kkeisLayout.setSpacing(5)
        kkeisLayout.setContentsMargins(0, 0, 0, 0)

        # Parameter input row
        paramRow = QWidget()
        paramRow.setFixedHeight(40)
        paramLayout = QHBoxLayout(paramRow)
        paramLayout.setSpacing(10)
        paramLayout.setContentsMargins(0, 0, 0, 0)

        self.parent.kkeisParamLabel = PyLabel2(
            text="K-K EIS Parameters:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        paramLayout.addWidget(self.parent.kkeisParamLabel)

        self.parent.kkeisParamEdit = PyLineEdit2(
            text='',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.kkeisParamEdit.setFixedHeight(40)
        paramLayout.addWidget(self.parent.kkeisParamEdit)

        paramLayout.addStretch()
        kkeisLayout.addWidget(paramRow)
        self.parent.DPsublayout2.addWidget(kkeisContainer)
        
        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()

    def uiOther(self):
        """UI for Other method"""
        self.parent.freshprocessUI()
        
        # Add generic parameter inputs for other methods
        otherContainer = QWidget()
        otherLayout = QVBoxLayout(otherContainer)
        otherLayout.setSpacing(5)
        otherLayout.setContentsMargins(0, 0, 0, 0)

        # Parameter input row
        paramRow = QWidget()
        paramRow.setFixedHeight(40)
        paramLayout = QHBoxLayout(paramRow)
        paramLayout.setSpacing(10)
        paramLayout.setContentsMargins(0, 0, 0, 0)

        self.parent.otherParamLabel = PyLabel2(
            text="Custom Parameters:",
            color=self.themes["app_color"]["text_title"],
            font_size=12,
            font_family=self.settings["font"]["family"],
            font_weight=700,
        )
        paramLayout.addWidget(self.parent.otherParamLabel)

        self.parent.otherParamEdit = PyLineEdit2(
            text='',
            radius=4,
            border_size=1,
            color=self.themes["app_color"]["text_foreground"],
            selection_color=self.themes["app_color"]["blue_primary"],
            bg_color=self.themes["app_color"]["input_bg"],
            bg_color_active=self.themes["app_color"]["input_bg"],
            context_color=self.themes["app_color"]["input_border"],
            font_size=self.settings["font"]["text_size_normal"],
            font_weight=600
        )
        self.parent.otherParamEdit.setFixedHeight(40)
        paramLayout.addWidget(self.parent.otherParamEdit)

        paramLayout.addStretch()
        otherLayout.addWidget(paramRow)
        self.parent.DPsublayout2.addWidget(otherContainer)

        # Add spacer to fill remaining space
        self.parent.DPsublayout2.addStretch()