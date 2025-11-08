# Mold Expert Skill

**Version**: 1.0.0
**Status**: Production Ready ✅
**Purpose**: Plastic injection mold design, tooling, manufacturing, and maintenance

> **Mold design & tooling expertise** - Injection mold design, tooling, materials, processes, troubleshooting, and cost optimization.

---

## Quick Reference

### Commands

```bash
# Mold Design
mold design-review <part> --material <resin>       # Design feasibility analysis
mold draft-angle <geometry> --depth <mm>           # Draft angle calculation
mold wall-thickness <design>                       # Wall thickness optimization
mold cooling-analysis <part> --cycle-time <target> # Cooling channel design

# Tooling
mold cavity-count <volume> --part-size <mm>        # Optimal cavity layout
mold runner-design <cavities> --material <resin>   # Runner system design
mold ejection-system <undercuts>                   # Ejector pin placement
mold cost-estimate <cavities> --complexity <1-5>   # Tooling cost estimation

# Manufacturing
mold process-parameters <material>                 # Injection parameters
mold troubleshoot <defect-type>                    # Defect root cause analysis
mold maintenance-schedule <shot-count>             # Preventive maintenance plan
mold cycle-time-optimize <current>                 # Cycle time reduction

# Quality
mold dimensional-inspection <tolerance>            # Quality control plan
mold first-article <cavities>                      # FAI procedure
mold ppap-documentation <customer>                 # PPAP package creation
```

---

## Core Expertise

### 1. Mold Design Fundamentals

**Key Design Principles**:

**Draft Angles**:
| Surface | Minimum Draft | Recommended |
|---------|---------------|-------------|
| Textured | 2-3° | 3-5° |
| Smooth | 0.5-1° | 1-2° |
| Deep ribs | 1-1.5° | 2-3° |

**Wall Thickness**:
```
Nominal thickness: 2-4mm (most plastics)
Variation: ±25% maximum
Thick-to-thin transition: Gradual (3:1 ratio)

Examples by Material:
- PP: 0.8-3.0mm
- ABS: 1.2-3.5mm
- PC: 1.0-4.0mm
- PET: 0.3-3.0mm
```

**Ribs & Bosses**:
- Rib thickness: 50-60% of wall thickness
- Boss wall: 50% of nominal wall
- Rib height: < 3× wall thickness

---

### 2. Cavity Layout & Gating

**Cavity Count Decision**:

| Annual Volume | Recommended Cavities | Tooling Cost |
|---------------|---------------------|--------------|
| < 10K | 1-2 | $5K-$15K |
| 10K-100K | 2-4 | $15K-$40K |
| 100K-500K | 4-8 | $40K-$80K |
| 500K-1M | 8-16 | $80K-$150K |
| > 1M | 16-32 | $150K-$300K+ |

**Gate Types**:

**Edge Gate**:
- Best for: Flat parts
- Pros: Easy de-gating, balanced fill
- Cons: Gate vestige visible

**Pin Gate (Submarine)**:
- Best for: Round parts
- Pros: Auto-degating, hidden gate
- Cons: Higher pressure drop

**Hot Runner**:
- Best for: High volume (> 1M/year)
- Pros: No runner waste, faster cycle
- Cons: Higher tooling cost (+50-100%)

**Film Gate**:
- Best for: Large, flat parts
- Pros: Even filling, minimal warp
- Cons: Manual degating required

---

### 3. Injection Molding Process

**Process Parameters**:

| Parameter | Typical Range | Impact |
|-----------|---------------|--------|
| **Injection Pressure** | 10,000-20,000 psi | Fill quality, flash |
| **Injection Speed** | 1-10 in/sec | Surface finish, flow marks |
| **Melt Temperature** | Material-dependent | Viscosity, degradation |
| **Mold Temperature** | 30-100°C | Cooling time, warpage |
| **Cooling Time** | 10-60 sec | Cycle time, cost |
| **Hold Pressure** | 5,000-15,000 psi | Shrinkage, sink marks |
| **Screw Speed** | 50-150 RPM | Melt uniformity |

**Material-Specific Settings** (Examples):

**Polypropylene (PP)**:
```
Melt Temperature: 200-280°C
Mold Temperature: 20-60°C
Injection Pressure: 10,000-15,000 psi
Cooling Time: 15-30 sec
Shrinkage: 1.5-2.5%
```

**ABS**:
```
Melt Temperature: 200-260°C
Mold Temperature: 40-80°C
Injection Pressure: 12,000-18,000 psi
Cooling Time: 20-40 sec
Shrinkage: 0.4-0.7%
```

**PET**:
```
Melt Temperature: 260-290°C
Mold Temperature: 10-50°C (cold) or 120-140°C (hot)
Injection Pressure: 15,000-25,000 psi
Cooling Time: 10-25 sec
Shrinkage: 0.2-0.5%
```

---

### 4. Cooling System Design

**Cooling Time Calculation**:
```
t_cool = (s² / α) × ln((T_melt - T_mold) / (T_eject - T_mold))

Where:
s = wall thickness (mm)
α = thermal diffusivity (mm²/s)
T_melt = melt temperature (°C)
T_mold = mold temperature (°C)
T_eject = ejection temperature (°C)
```

**Cooling Channel Design**:
- **Diameter**: 8-12mm (typical)
- **Pitch**: 3-5× channel diameter
- **Distance to cavity**: 1.5-2× channel diameter
- **Layout**: Follow part contour, uniform cooling

**Cooling Methods**:
1. **Water cooling** (most common)
2. **Baffles** (for deep cores)
3. **Bubblers** (for small cores)
4. **Thermal pins** (for tight spots)
5. **Conformal cooling** (3D-printed molds)

---

### 5. Ejection Systems

**Ejector Pin Design**:
- **Diameter**: 3-10mm (typical)
- **Location**: Uniform distribution, avoid stress concentration
- **Quantity**: Sufficient to overcome suction
- **Ejection force**: F = P × A (pressure × surface area)

**Ejection Methods**:

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **Ejector Pins** | General | Simple, reliable | Pin marks |
| **Sleeve Ejectors** | Round parts | No internal marks | Complex |
| **Stripper Plates** | Deep parts | Large area | Higher cost |
| **Air Ejection** | Cups, bottles | No marks | Compressed air needed |

**Undercut Solutions**:
- **Side cores** (manual/hydraulic)
- **Lifters** (cam-actuated)
- **Collapsible cores**
- **Unscrewing mechanism** (threads)

---

### 6. Mold Materials

**Mold Steel Selection**:

| Steel Grade | Hardness | Applications | Cost |
|-------------|----------|--------------|------|
| **P20** | 28-32 HRC | General purpose, prototype | $ |
| **H13** | 48-52 HRC | High-volume, abrasive materials | $$ |
| **S7** | 54-58 HRC | Very high volume, wear resistance | $$$ |
| **420 SS** | 48-52 HRC | Corrosive materials (PVC) | $$$ |
| **Beryllium Copper** | 38-42 HRC | Cooling inserts | $$$$ |

**Surface Treatments**:
- **Nitriding**: Wear resistance
- **Chrome plating**: Corrosion resistance, easy release
- **Nickel plating**: PET molds (prevents AA formation)
- **Texturing**: SPI finish levels (A-1 to D-3)

---

### 7. Defect Troubleshooting

**Common Defects & Solutions**:

| Defect | Cause | Solution |
|--------|-------|----------|
| **Short shot** | Low pressure, cold melt | Increase pressure/temp, enlarge gates |
| **Flash** | Excessive pressure, worn mold | Reduce pressure, repair parting line |
| **Sink marks** | Thick walls, inadequate packing | Reduce wall thickness, increase hold pressure |
| **Warpage** | Uneven cooling, residual stress | Balance cooling, optimize gate location |
| **Flow lines** | Low melt temp, slow injection | Increase temperature/speed |
| **Burn marks** | Trapped air, high speed | Add venting, reduce speed |
| **Weld lines** | Multiple gates, slow flow | Increase temp, adjust gate locations |
| **Jetting** | High speed through small gate | Reduce speed, enlarge gate |

**Diagnostic Process**:
1. Identify defect type
2. Review process parameters
3. Inspect mold (wear, damage)
4. Adjust parameters (one at a time)
5. Validate with DOE (Design of Experiments)

---

### 8. Mold Cost Breakdown

**Tooling Cost Components**:

```
Total Mold Cost = Base + Cavities + Features + Complexity

Base Mold (1-cav):        $5,000-$10,000
Additional Cavities:      +$2,000-$5,000 each
Side Actions:             +$1,000-$3,000 each
Hot Runner System:        +$10,000-$50,000
Texturing:                +$500-$2,000 per cavity
```

**Example** (4-cavity, 2 side actions, textured):
```
Base: $8,000
Cavities (3 additional): $12,000
Side actions (2): $4,000
Texturing: $3,000
Total: $27,000
```

**Cost Reduction Strategies**:
1. Reduce cavity count (if volume allows)
2. Eliminate undercuts (design change)
3. Use standard components (DME, Hasco)
4. Simplify cooling layout
5. Avoid hot runners for low volume
6. Use aluminum for prototype molds

---

### 9. Mold Maintenance

**Preventive Maintenance Schedule**:

| Interval | Tasks |
|----------|-------|
| **Every Shift** | Clean mold faces, check for flash/wear |
| **Weekly** | Lubricate ejector pins, check water flow |
| **Monthly** | Deep clean, inspect for cracks/wear |
| **10K shots** | Polish cavities, check dimensions |
| **50K shots** | Replace wear components (ejector pins) |
| **100K shots** | Full overhaul, re-chrome surfaces |

**Common Wear Areas**:
- Gate orifice (abrasion)
- Ejector pins (galling)
- Parting line (flash formation)
- Cooling channels (scale buildup)

**Mold Life Expectancy**:
- Aluminum: 5,000-100,000 shots
- P20 steel: 100,000-500,000 shots
- Hardened steel (H13): 1M-5M+ shots

---

### 10. Industry Standards & Certifications

**Quality Standards**:
- **ISO 9001**: Quality management
- **ISO 13485**: Medical devices
- **IATF 16949**: Automotive
- **PPAP**: Production Part Approval Process
- **IMDS**: International Material Data System

**Documentation**:
- Mold drawing (2D/3D)
- Bill of Materials (BOM)
- Process parameter sheet
- Maintenance log
- First Article Inspection Report (FAIR)

**Testing & Validation**:
- FAI (First Article Inspection)
- PPAP submission (automotive)
- Capability study (Cpk ≥ 1.33)
- Gage R&R (< 10%)

---

## Best Practices

1. **Design for Manufacturability (DFM)**
   - Uniform wall thickness
   - Adequate draft angles
   - Avoid sharp corners
   - Minimize undercuts

2. **Material Selection**
   - Match material to application
   - Consider shrinkage, warpage
   - Evaluate cost vs. performance

3. **Process Optimization**
   - Scientific molding approach
   - DOE for parameter optimization
   - SPC for process control

4. **Mold Maintenance**
   - Regular cleaning & inspection
   - Preventive maintenance schedule
   - Spare parts inventory

---

## MCP Integration

**GitHub MCP** → CAD file version control, collaboration
**Filesystem MCP** → Design file management, mold library

---

## Related Skills

- **pcb-expert** - Enclosure design integration
- **production-expert** - Manufacturing optimization
- **manufacturing-expert** - Quality systems

---

**Version**: 1.0.0 | **Status**: Production Ready | **License**: MIT
