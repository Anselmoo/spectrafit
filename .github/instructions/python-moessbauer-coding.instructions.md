---
applyTo: "spectrafit/**/moessbauer*.py"
---

# Project physical standards for Moessbauer implementation in Python

In Mössbauer spectroscopy, singlet, doublet, and sextet patterns correspond to distinct hyperfine interactions:

## 1. Singlet

**Physical Cause:**

On isomer shift (IS) present — no quadrupole or magnetic hyperfine interaction.

**Spectrum:**
• Oneine, centered at the isomer shift.

**Typical Systems:**
• Non-maetic, high-symmetry sites (e.g., Fe²⁺ in a cubic site, at high temperature).

**Model Parameters:**

```py
"moesbauer_singlet": {
    "isomer_shift": {"min": -2, "max": 2, "value": 0.3, "vary": True},
    "linewidth": {"min": 0.05, "max": 0.5, "value": 0.2, "vary": True},
    "intensity": {"min": 0.5, "max": 2.0, "value": 1.0, "vary": True},
    "center": {"min": -1.0, "max": 1.0, "value": 0.0, "vary": False}
}
```

## 2. Doublet

**Physical Cause:**

Quadrupole splitting from electric field gradient (EFG) interaction.

**Spectrum:**
• Two symmetric lines, split by ΔE_Q.
• Intensity ratio typically 1:1.

**Typical Systems:**
• Fe³⁺ in low-symmetry ligand fields (e.g., distorted octahedral).
• Paramagnetic or non-magnetic.

**Model Parameters:**

```py
"moesbauer_doublet": {
    "isomer_shift": {"min": -2, "max": 2, "value": 0.4, "vary": True},
    "quadrupole_splitting": {"min": 0.0, "max": 3.0, "value": 0.8, "vary": True},  # mm/s
    "linewidth": {"min": 0.05, "max": 0.5, "value": 0.2, "vary": True},
    "intensity": {"min": 0.5, "max": 2.0, "value": 1.0, "vary": True},
    "center": {"min": -1.0, "max": 1.0, "value": 0.0, "vary": False}
}
```

## Sextet

**Physical Cause:**

Magnetic hyperfine interaction (Zeeman effect). Spin 1/2 ground → Spin 3/2 excited splits into 6 allowed transitions.

**Spectrum:**

- Six lines with specific relative intensities (depending on texture and polarization).
- Line positions determined by hyperfine field.

**Typical Systems:**

- Magnetically ordered materials (e.g., α-Fe at low T).
- Ferromagnetic or antiferromagnetic phases.
  **Model Parameters:**

```py
    "moesbauer_sextet": {
    "isomer_shift": {"min": -2, "max": 2, "value": 0.0, "vary": True},
    "magnetic_field": {"min": 0.0, "max": 40.0, "value": 33.0, "vary": True},  # Tesla
    "linewidth": {"min": 0.05, "max": 0.5, "value": 0.25, "vary": True},
    "intensity": {"min": 0.5, "max": 2.0, "value": 1.0, "vary": True},
    "center": {"min": -1.0, "max": 1.0, "value": 0.0, "vary": False},

    # Optional angular dependence (powder averaging if needed)
    "angle_B_theta_phi": {"theta": 0.0, "phi": 0.0},

    # Optional quadrupole shift (nonzero if EFG present too)
    "quadrupole_shift": {"min": -1.0, "max": 1.0, "value": 0.0, "vary": False}
    }
```

### Comparison Summary

| Pattern | Lines | Hyperfine Interaction           | Common Materials             |
| ------- | ----- | ------------------------------- | ---------------------------- |
| Singlet | 1     | Isomer shift only               | Cubic sites, high T          |
| Doublet | 2     | Quadrupole splitting            | Fe²⁺/Fe³⁺ in distorted sites |
| Sextet  | 6     | Magnetic field (Zeeman effect)  | Magnetic iron phases         |
| Octet   | 8     | Magnetic + quadrupole + angular | Complex low-symmetry sites   |

## Mössbauer Octet Model – Full Parameter Specification

This model is designed for fitting Mössbauer spectra, especially those exhibiting an octet pattern due to magnetic hyperfine interactions (e.g., in α-Fe).

### Purpose

Define a complete Mössbauer model based on both:

1. Hyperfine parameter fitting
2. Underlying spin Hamiltonian for quantum-accurate simulation

⸻

### Parameter Dictionary (Python Format)

```py
initial_model = [
    {
        "moesbauer_octet": {
            # --- Core Hyperfine Parameters ---
            "isomer_shift": {"min": -2.0, "max": 2.0, "vary": True, "value": 0.0},           # mm/s
            "magnetic_field": {"min": 0.0, "max": 40.0, "vary": True, "value": 33.0},        # Tesla
            "quadrupole_shift": {"min": -1.0, "max": 1.0, "vary": True, "value": 0.0},       # mm/s
            "linewidth": {"min": 0.05, "max": 0.5, "vary": True, "value": 0.25},             # mm/s
            "intensity": {"min": 0.5, "max": 1.5, "vary": True, "value": 1.0},
            "center": {"min": -1.0, "max": 1.0, "vary": False, "value": 0.0},                 # mm/s

            # --- Spin Hamiltonian Parameters ---
            "nuclear_spin": 1.5,                                                              # I (e.g., 3/2 for 57Fe excited state)
            "g_factor": 0.18,                                                                 # dimensionless
            "quadrupole_moment": 0.16e-28,                                                    # m² (0.16 barns)
            "EFG_Vzz": {"value": 1e21, "vary": False},                                        # V/m²
            "EFG_eta": {"value": 0.0, "vary": False},                                         # EFG asymmetry
            "angle_B_theta_phi": {"theta": 0.0, "phi": 0.0},                                  # orientation (radians)

            # --- Temperature & Debye Effects ---
            "temperature": {"value": 300, "vary": False},                                     # K
            "SOD_shift": {"value": 0.0, "vary": False},                                       # mm/s (optional override)

            # --- Site Weight (for multi-component fits) ---
            "site_fraction": {"value": 1.0, "vary": False}
        }
    }
]
```

### Physical Meaning of Parameters

| Parameter         | Description                                                    |
| ----------------- | -------------------------------------------------------------- |
| isomer_shift      | Shift due to electron density at the nucleus (chemical shift)  |
| magnetic_field    | Effective hyperfine field causing Zeeman splitting             |
| quadrupole\_      | shift Energy shift due to EFG interaction (if any)             |
| linewidth         | FWHM of individual lines (instrumental or physical broadening) |
| intensity         | Line strength, for site-specific fitting                       |
| center            | Global offset in mm/s (optional)                               |
| nuclear_spin      | Spin of excited nuclear state (e.g., 3/2 for 57Fe)             |
| g_factor          | Nuclear g-factor for magnetic moment calculation               |
| quadrupole_moment | Nuclear quadrupole moment (e.g., 0.16 barns for 57Fe)          |
| EFG_Vzz           | Principal EFG component                                        |
| EFG_eta           | EFG asymmetry parameter                                        |
| angle_B_theta_phi | Orientation of magnetic field with respect to EFG              |
| temperature       | For second-order Doppler shift modeling                        |
| SOD_shift         | Optional fixed SOD shift if not modeled dynamically            |
| site_fraction     | Weight of this site/component in a composite spectrum          |
