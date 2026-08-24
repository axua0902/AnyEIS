## 🤖 Assistant

# AnyEIS - Electrochemical & Dielectric Spectroscopy Analysis Software

## Overview

**AnyEIS** is a comprehensive, integrated software tool designed for the efficient analysis of **Electrochemical Impedance Spectroscopy (EIS)** and **Dielectric Spectroscopy (DS)** data. It provides researchers in materials science, biomedicine, and energy fields with a powerful, all-in-one solution for data visualization, processing, simulation, and fitting, significantly enhancing the efficiency and reliability of data interpretation.

## Key Features

* **Plotting Module:** Intuitive visualization of EIS/DS experimental data with support for Nyquist, Bode, and other standard plots.
* **Processing Module:** Advanced preprocessing functions including noise reduction filters (Savitzky-Golay, Median, etc.) and specialized calibration/calculation methods for EIS/DS data conversion.
* **Simulation Module:** Flexible construction and simulation of electrochemical equivalent circuit models and dielectric relaxation models (Debye, Cole-Cole, Havriliak-Negami, etc.).
* **Fitting Module:** Precise parameter fitting using intelligent optimization algorithms (Genetic Algorithm, Levenberg-Marquardt, etc.) to bridge experimental data with theoretical models.

## System Requirements & Compatibility

### Operating System
* **Supported:** Windows 10 (64-bit) or later.
* **Not Supported:** Windows 7/8, Linux, or macOS. (May run via virtual machines like VMware, but stability is not guaranteed).

### Hardware
* **Processor:** Intel Core i5 or equivalent AMD (≥ 2.4 GHz recommended).
* **Memory:** Minimum 8 GB RAM (16 GB recommended for large datasets).
* **Storage:** At least 1 GB of free disk space.
* **Display:** Resolution ≥ 1920×1080.

### Software Dependencies
* **Python:** Version 3.8 or higher required.
* **Recommended Distribution:** Anaconda (2025 release) for simplified dependency management.
* **Core Libraries:**
 * `NumPy (>=1.24.0)`, `SciPy (>=1.10.0)`, `pandas (>=2.0.0)`, `mpmath (>=1.3.0)`
 * `Matplotlib (>=3.7.0)`, `schemdraw (>=0.18.0)`
 * `lmfit (>=1.2.0)`
 * `PySide6 (>=6.5.0)`, `xlsxwriter (>=3.1.0)`

## Installation

*(Note: The original document omitted specific installation steps. The following is a general guideline.)*

1. Ensure your system meets the requirements above.
2. Install Python 3.8+ and the recommended dependencies (e.g., via Anaconda).
3. The software is likely distributed as a packaged application or requires running from source. Please refer to the specific installation instructions provided with the software package.
4. Launch `AnyEIS` from the start menu or by running the main Python script.

## Quick Start

1. **Launch AnyEIS:** Start the application. The main interface consists of a title bar, a left-side menu bar, and a central workspace.
2. **Navigate Modules:** Use the vertical menu bar icons to switch between core functions:
 * **🏠 Home:** Returns to the main screen.
 * **📈 Plotting:** Load and visualize your experimental EIS/DS data.
 * **⚙️ Processing:** Apply filters, smoothing, or convert EIS data to DS.
 * **🔄 Simulation:** Build and simulate theoretical models (circuits or dielectric models).
 * **🔬 Fitting:** Fit your experimental data to models to extract physical parameters.
3. **Basic Workflow:** A typical analysis might follow: **Plotting** (view data) → **Processing** (clean data) → **Simulation** (build a model) → **Fitting** (fit model to data).

## Module Guide

### 1. Plotting Module
* **Purpose:** Visualize raw or processed EIS/DS data.
* **Key Actions:** Use the `Input Data` button to load files (.txt, .csv, .xlsx). Select files/data using the control panel. Click `Draw` to generate Nyquist, Bode, or other plots in the main chart area. Use the toolbar for zooming, panning, and exporting images.

### 2. Processing Module
* **Purpose:** Preprocess experimental data to improve quality.
* **Key Actions:** Load data, then use the **Filter** section to apply noise reduction (e.g., Savitzky-Golay). Use the **Processing** section for advanced operations like the **Three-Solution Method** to calculate dielectric properties from EIS data. Processed data can be visualized and exported.

### 3. Simulation Module
* **Purpose:** Generate theoretical EIS/DS response curves based on models.
* **Key Actions:** Select a model type (`Equivalent circuit model` or `Multi-terms model`). For circuits, add elements (R, C, CPE) and define their connections (Series/Parallel). For dielectric models, add terms (Debye, Cole-Cole). Set frequency range and parameters, then click `Simulate` to generate the curve.

### 4. Fitting Module
* **Purpose:** Find the best model parameters that match your experimental data.
* **Key Actions:** Load experimental data. Build or load a model (similar to the Simulation module). Configure the fitting algorithm (e.g., `leastsquares`, `differential_evolution`) and its parameters. Click `Calculate Parameters` to perform the fit. The optimized parameters and fitted curve will be displayed.

## System & Preferences
Access settings via the gear icon (⚙️) in the bottom menu bar.
* **Appearance:** Switch between Light and Dark themes.
* **Language:** Toggle between English and Simplified Chinese.
* **Data Paths:** Set default directories for project files.
* **Help & About:** Access the user manual and view software version/copyright information.

## Copyright & License
* **Copyright:** AnyEIS® © 2025. All rights reserved.
* **License:** For **academic and non-commercial use**, this software is provided under the **MIT Open Source License**. You must retain all copyright notices.
* **Commercial Use:** Requires a separate commercial license. Please contact the development team for authorization.
* **Disclaimer:** The software relies on third-party libraries under their respective licenses. The developers are not responsible for data loss due to system conflicts or unsupported use (e.g., on macOS/Linux).

## Support & Documentation
* For detailed operational guidance, use the built-in **Help** documentation (accessible via the `Help` button in Settings).
* The theoretical background for EIS, DS, and fitting principles is covered in the software's documentation (Chapter 7 of the handbook).

---
*This README is based on the AnyEIS User Handbook. For the most up-to-date information, please refer to the official documentation provided with the software.*
