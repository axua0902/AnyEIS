# AnyEIS Model File Format Specification

## Overview

AnyEIS uses JSON format to store model configuration files, supporting three model types:
- **ECM**: Equivalent Circuit Model
- **MS**: Multi-Shell Model
- **MT**: Multi-Term Model

---

## Common Fields

All model files contain the following common fields:

| Field | Type | Description |
|-----|------|------|
| `version` | string | Model file version number, currently "1.0" |
| `model_type` | string | Model type: ECM / MS / MT |
| `model_name` | string | User-defined model name |
| `file_path` | string | Associated data file path |
| `created_date` | string | File creation date, format: YYYY-MM-DD |
| `frequency` | object | Frequency range configuration |
| `notes` | string | Notes and remarks |

### frequency Field Structure

```json
"frequency": {
  "min": 0.1,        // Minimum frequency
  "max": 10000,      // Maximum frequency
  "points": 50,      // Number of frequency points
  "unit": "Hz"       // Frequency unit
}
```

---

## ECM Model (Equivalent Circuit Model)

### File Location
```
ModelFileExamples/ECM_Randles_Circuit.json
```

### Circuit String Syntax

The circuit is described using a string expression with the following grammar rules:

| Symbol | Meaning | Example |
|-----|------|------|
| `R` | Resistor | `R` |
| `C` | Capacitor | `C` |
| `L` | Inductor | `L` |
| `p(...)` | Parallel | `p(R,C)` means R||C |
| `(...)` | Series | `(R,p(R,C))` |
| `,` | Separator | |

**Example circuits**:
- `R` - Pure resistor
- `R,R` - Two resistors in series
- `p(R,C)` - Resistor in parallel with capacitor
- `R(p(R,C),R)` - Rs + (Rct||Cdl) in series

### Circuit Diagram

```
circuit_string: "R(p(R,C),R)"

    C
   ++ ++
 ---||---
 |  R   |
 |  ||  |
 +--||--+----+
 |       R    |
 +-----------+
```

Equivalent to: Rs + (Rct || Cdl)

### Parameters Field Structure

```json
"parameters": [
  {
    "name": "Rs",              // Parameter name (used in code)
    "display_name": "Solution Resistance",  // Display name
    "value": 100.0,            // Initial value
    "unit": "ohm",             // Unit
    "min": 0.0,               // Minimum value
    "max": 10000.0,           // Maximum value
    "fixed": false             // Whether fixed (not involved in fitting)
  }
]
```

---

## MS Model (Multi-Shell Model)

> **Note**: The MS model file directory and example files are pending implementation.

The MS model is used to describe the dielectric response of particle systems with core-shell structures, such as biological cells, coated particles, etc.

### Expected File Location
```
ModelFileExamples/MS/MS_Core_Shell_TwoLayer.json
```

### Supported Built-in Model Types

| Model Type | Code | Description |
|---------|------|------|
| Db | Debye | Debye relaxation model |
| CC | Cole-Cole | Cole-Cole dispersion model |
| DC | Davidson-Cole | Davidson-Cole dispersion model |
| HN | Havriliak-Negami | HN dispersion model |

### Model Formulas

**Debye Model**:
```
ε(ω) = εh + Δε / (1 + jωτ)
```
- `εh`: High-frequency permittivity
- `Δε`: Relaxation strength (εl - εh)
- `τ`: Relaxation time

**Cole-Cole Model**:
```
ε(ω) = εh + Δε / (1 + (jω/ωc)^(1-α))
```
- `α`:  Cole-Cole exponent (0 < α < 1)

**Davidson-Cole Model**:
```
ε(ω) = εh + Δε / (1 + jω/ωc)^β
```
- `β`: Davidson-Cole exponent (0 < β ≤ 1)

**Havriliak-Negami Model**:
```
ε(ω) = εh + Δε / (1 + (jω/ωc)^(1-α))^β
```
- `α`: Describes symmetric broadening
- `β`: Describes asymmetric broadening

### Shell Structure Field

```json
"shell_structure": [
  {
    "layer": 1,
    "layer_name": "Core",
    "modeltype": "Db",
    "parameters": {
      "epsh": { "init": 10.0, "min": 0.0, "max": 100.0 },
      "Deps": { "init": 100.0, "min": 0.0, "max": 1000.0 },
      "Tao": { "init": 1e-9, "min": 1e-12, "max": 1e-2 }
    }
  },
  {
    "layer": 2,
    "layer_name": "Shell",
    "modeltype": "CC",
    "parameters": {
      "epsh": { "init": 10.0, "min": 0.0, "max": 100.0 },
      "Deps": { "init": 50.0, "min": 0.0, "max": 1000.0 },
      "Tao": { "init": 1e-6, "min": 1e-12, "max": 1e-2 },
      "Alpha": { "init": 0.3, "min": 0.0, "max": 1.0 }
    }
  }
]
```

### Medium Parameters (media)

```json
"media": {
  "Eps": 80.0,
  "Sigma": 0.001,
  "phi": 0.05,
  "mixture_model": "auto"
}
```

| Parameter | Description | Typical Value |
|-----|------|-------|
| Eps | Relative permittivity of medium | 80 (water) |
| Sigma | Medium conductivity (S/m) | 0.0 ~ 1.0 |
| phi | Particle volume fraction | 0.01 ~ 0.5 |
| mixture_model | Mixture model | Maxwell/Hanai/auto/none |

### mixture_model Options

| Option | Description |
|-----|------|
| `none` | Pure particles, no mixture model |
| `Maxwell` | Maxwell mixture model (suitable for phi < 0.1) |
| `Hanai` | Hanai mixture model (suitable for phi > 0.1) |
| `auto` | Automatically selected based on phi |

---

## MT Model (Multi-Term Model)

The MT model is used to describe materials with multiple dielectric relaxation processes, such as biological tissues, polymers, etc.

### File Location
```
ModelFileExamples/MT/MT_Debye.json          # Single Debye model
ModelFileExamples/MT/MT_DoubleDebye.json    # Double Debye model
ModelFileExamples/MT/MT_ColeCole.json       # Cole-Cole model
ModelFileExamples/MT/MT_DavidsonCole.json   # Davidson-Cole model
ModelFileExamples/MT/MT_HavriliakNegami.json # Havriliak-Negami model
```

### Supported Model Types

| Model Type | Code | Description |
|---------|------|------|
| Debye | Db | Single Debye relaxation process |
| Cole-Cole | CC | Cole-Cole dispersion model |
| Davidson-Cole | DC | Davidson-Cole dispersion model |
| Havriliak-Negami | HN | HN dispersion model |

### Complete File Structure

```json
{
    "version": "1.0",
    "model_type": "MT",
    "model_name": "Double_Debye",
    "file_path": "",
    "created_date": "2026-06-15",
    "frequency": {
        "min": 10.0,
        "max": 1000000000.0,
        "distribution": "Log",
        "unit": "Hz"
    },
    "option": {
        "EP": 0,
        "DC Conductivity": 1
    },
    "model_terms": [
        {
            "name": "1",
            "modeltype": "Debye",
            "expression": "Deps1/(1+j*omega*Tao1)"
        },
        {
            "name": "2",
            "modeltype": "Debye",
            "expression": "Deps2/(1+j*omega*Tao2)"
        }
    ],
    "parameters": [
        {
            "name": "epsh",
            "init": 10.0,
            "min": 0.0,
            "max": 100.0
        },
        {
            "name": "sigmaDC",
            "init": 1e-4,
            "min": 0.0,
            "max": 1.0
        },
        {
            "name": "Deps1",
            "init": 50.0,
            "min": 0.0,
            "max": 200.0
        },
        {
            "name": "Tao1",
            "init": 1e-5,
            "min": 1e-12,
            "max": 1e-2
        },
        {
            "name": "Deps2",
            "init": 30.0,
            "min": 0.0,
            "max": 200.0
        },
        {
            "name": "Tao2",
            "init": 1e-7,
            "min": 1e-12,
            "max": 1e-2
        }
    ]
}
```

### model_terms Field Description

| Field | Type | Description |
|-----|------|------|
| `name` | string | Term number (1, 2, 3...) |
| `modeltype` | string | Model type: Debye/Cole-Cole/Davidson-Cole/Havriliak-Negami |
| `expression` | string | Dielectric response expression, using omega for angular frequency |

### model_terms Expression Examples

**Debye Term**:
```
Deps1/(1+j*omega*Tao1)
```

**Cole-Cole Term**:
```
Deps1/(1+(j*omega*Tao1)^(1-Alpha1))
```

**Davidson-Cole Term**:
```
Deps1/(1+j*omega*Tao1)^Beta1
```

**Havriliak-Negami Term**:
```
Deps1/(1+(j*omega*Tao1)^(1-Alpha1))^Beta1
```

### Global Parameters

Each MT model contains the following global parameters:

| Parameter Name | Description | Typical Value Range |
|-------|------|------------|
| `epsh` | High-frequency permittivity (electrode polarization contribution) | 0 ~ 100 |
| `sigmaDC` | DC conductivity | 0 ~ 1.0 S/m |

### Term Parameters

Each model_term corresponds to the following parameters:

| Parameter Name | Description | Applicable Model |
|-------|------|---------|
| `Deps` | Relaxation strength (Δε) | All models |
| `Tao` | Relaxation time (τ) | All models |
| `Alpha` | Cole-Cole/HN exponent (0<α<1) | Cole-Cole, HN |
| `Beta` | Davidson-Cole/HN exponent (0<β≤1) | Davidson-Cole, HN |

### Options (option)

| Option | Description | Value |
|-----|------|----|
| `EP` | Electrode polarization effect | 0=Not considered, 1=Considered |
| `DC Conductivity` | DC conductivity | 0=Not considered, 1=Considered |

---

## File Naming Convention

It is recommended to use the following format for naming:
```
{Model Type}_{Description}.json
```

**Examples**:
- `ECM_Randles.json` - Randles equivalent circuit
- `ECM_Double_Randles.json` - Double Randles circuit
- `MT_Debye.json` - Single Debye relaxation model
- `MT_DoubleDebye.json` - Double Debye relaxation model
- `MT_ColeCole.json` - Cole-Cole model
- `MT_DavidsonCole.json` - Davidson-Cole model
- `MT_HavriliakNegami.json` - Havriliak-Negami model

---

## Recommended Directory Structure

```
ModelFileExamples/
├── ECM/                    # ECM model files directory
│   ├── ECM_Randles.json
│   ├── ECM_Double_Randles.json
│   ├── ECM_Randles_4element.json
│   ├── ECM_RC_Series.json
│   └── ECM_RL_Series.json
├── MT/                     # MT model files directory
│   ├── MT_Debye.json
│   ├── MT_DoubleDebye.json
│   ├── MT_ColeCole.json
│   ├── MT_DavidsonCole.json
│   └── MT_HavriliakNegami.json
└── MS/                     # MS model files directory (pending implementation)
    └── ...
```

---

## Version History

| Version | Date | Description |
|-----|------|------|
| 1.0 | 2026-05-24 | Initial version |
| 1.1 | 2026-06-15 | Improved MS and MT model documentation, corrected field names, added complete examples |
