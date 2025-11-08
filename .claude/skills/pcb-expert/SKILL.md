---
name: pcb-expert
description: PCB Expert Skill
---

# PCB Expert Skill

**Version**: 1.0.0
**Status**: Production Ready ✅
**Purpose**: PCB design, manufacturing, assembly, testing, and quality control

> **PCB design & manufacturing expertise** - Circuit design, layout, fabrication, assembly (SMT/THT), testing, and industry standards (IPC).

---

## Quick Reference

### Commands

```bash
# Design & Layout
pcb design-review <schematic>                  # Design rule check (DRC)
pcb stackup <layers> --impedance <target>      # Layer stackup calculation
pcb trace-width <current> --thickness <oz>     # Trace width calculator

# Manufacturing
pcb fab-specs <design> --class <1-3>          # Fabrication specifications
pcb cost-estimate <qty> --layers <num>         # Cost estimation
pcb dfm-check <gerber>                         # Design for Manufacturing check

# Assembly
pcb bom-optimize <components>                  # BOM cost optimization
pcb placement-check <design>                   # Component placement review
pcb solder-paste <aperture>                    # Solder paste stencil design

# Testing
pcb test-strategy <design>                     # Test strategy development
pcb aoi-programming <components>               # AOI program creation
pcb ict-fixture <testpoints>                   # ICT fixture design
```

---

## Core Expertise

### 1. PCB Design Standards

**IPC Standards**:
- **IPC-2221**: Generic PCB design
- **IPC-2222**: Rigid organic PCBs
- **IPC-6012**: Qualification & performance
- **IPC-A-600**: Acceptability of PCBs
- **IPC-A-610**: Acceptability of assemblies

**Design Classes**:
| Class | Application | Trace/Space | Reliability |
|-------|-------------|-------------|-------------|
| Class 1 | Consumer | 6/6 mil | General |
| Class 2 | Industrial | 5/5 mil | Dedicated service |
| Class 3 | High reliability | 4/4 mil | Continued performance |

---

### 2. Layer Stackup Design

**Common Stackups**:

**2-Layer** (Simple):
```
Top (Signal)
Core (FR-4, 1.6mm)
Bottom (Signal + Ground)
```

**4-Layer** (Standard):
```
Top (Signal)
GND (Plane)
PWR (Plane)
Bottom (Signal)
```

**6-Layer** (High-speed):
```
Top (Signal)
GND (Plane)
Signal (Inner)
Signal (Inner)
PWR (Plane)
Bottom (Signal)
```

**Impedance Control**:
- 50Ω single-ended (typical)
- 100Ω differential pairs
- Calculation: Z = 87/√(εr+1.41) × ln(5.98h/(0.8w+t))

---

### 3. Manufacturing Process

**Fabrication Steps**:
1. **Inner Layer** - Image transfer, etch
2. **Lamination** - Press layers together
3. **Drilling** - Mechanical/laser drilling
4. **Plating** - Copper plating (PTH)
5. **Outer Layer** - Pattern plating
6. **Solder Mask** - Coating application
7. **Silkscreen** - Legend printing
8. **Surface Finish** - HASL, ENIG, OSP
9. **Routing** - Board cutting
10. **Testing** - Electrical test, AOI

**Lead Times**:
- Prototype (2-layer): 24-48 hours
- Standard (4-layer): 5-7 days
- Complex (6+ layer): 10-15 days

---

### 4. Assembly Methods

**SMT (Surface Mount Technology)**:
- **Process**: Solder paste → Pick & Place → Reflow
- **Pitch**: Down to 0.4mm (fine pitch)
- **Speed**: 20,000-80,000 CPH
- **Accuracy**: ±0.05mm

**THT (Through-Hole Technology)**:
- **Process**: Component insertion → Wave soldering
- **Applications**: Connectors, high-power
- **Reliability**: Higher mechanical strength

**Mixed Assembly**:
1. SMT bottom side → Reflow
2. SMT top side → Reflow
3. THT components → Wave/selective solder

---

### 5. Quality Control

**Inspection Methods**:

| Method | Type | Coverage | Defect Detection |
|--------|------|----------|------------------|
| **AOI** | Optical | 100% | 95-98% |
| **AXI** | X-ray | Samples | BGA, hidden joints |
| **ICT** | Electrical | Test points | Opens, shorts, values |
| **FCT** | Functional | 100% | Actual operation |

**Defect Types**:
- Solder bridges
- Insufficient solder
- Tombstoning
- Solder balls
- Component misalignment
- Missing components
- Wrong polarity

**Acceptance Criteria** (IPC-A-610):
- Class 1: Cosmetic defects acceptable
- Class 2: Limited defects
- Class 3: Zero defects

---

### 6. Design for Manufacturing (DFM)

**Key Rules**:

**Spacing**:
- Trace-to-trace: ≥ 6 mil (Class 1)
- Pad-to-trace: ≥ 8 mil
- Via-to-via: ≥ 25 mil

**Sizes**:
- Minimum trace width: 6 mil
- Minimum via diameter: 12 mil
- Minimum annular ring: 4 mil

**Component Placement**:
- Orientation: Same direction
- Spacing: ≥ 0.5mm (SMT)
- Keepout: 5mm from edge
- Thermal relief: For power planes

**Panelization**:
- Panel size: 18" × 24" (standard)
- Breakaway tabs: V-groove or routing
- Fiducials: 3 per panel

---

### 7. Cost Optimization

**Cost Drivers**:
1. **Layer count** (+30% per 2 layers)
2. **Board size** (Price breaks: 100×100, 150×150)
3. **Surface finish** (HASL < ENIG < Gold)
4. **Quantity** (Economies of scale)
5. **Lead time** (Rush = 2-3x cost)

**Cost Reduction Strategies**:
- Reduce layer count
- Standardize panel sizes
- Use common materials (FR-4)
- Batch similar designs
- Optimize BOM (standard parts)

**Example Pricing** (4-layer, 100×100mm):
```
Qty 5:    $50-100 each
Qty 50:   $10-20 each
Qty 500:  $3-5 each
Qty 5000: $1-2 each
```

---

### 8. High-Speed Design

**Signal Integrity Considerations**:

**Impedance Matching**:
- Source impedance = Trace impedance = Load impedance
- Reduces reflections, ringing

**Via Optimization**:
- Minimize via count (signal path)
- Back-drilling for high-speed
- Via-in-pad for BGA

**Crosstalk Reduction**:
- 3W rule (3× trace width spacing)
- Ground planes between layers
- Guard traces with GND

**EMI/EMC**:
- Continuous ground plane
- Decoupling capacitors
- Shielding (if needed)

---

### 9. Testing Strategies

**Test Coverage**:

**Bare Board Testing**:
- Flying probe (prototype)
- Bed of nails fixture (production)
- Tests: Opens, shorts, impedance

**Assembly Testing**:
- AOI: Visual defects
- ICT: Electrical values
- FCT: Functional operation
- Burn-in: Reliability (optional)

**Test Economics**:
```
ICT Fixture Cost: $5,000-$20,000
Amortized over: 10,000-50,000 boards
Cost per board: $0.10-$2.00

Flying Probe:
Setup cost: $500-$1,000
Cost per board: $5-$20
Best for: < 500 boards
```

---

### 10. Industry Trends (2025)

**Emerging Technologies**:
- **HDI** (High-Density Interconnect) - Finer features
- **Flex/Rigid-Flex** - 3D packaging
- **Embedded Components** - Passive integration
- **Advanced Materials** - High-frequency (Rogers, Teflon)

**Market Growth**:
- Global PCB market: $89B (2025)
- CAGR: 4.3% (2025-2030)
- Asia-Pacific: 90% production

---

## MCP Integration

**GitHub MCP** → Version control for design files, collaboration
**Filesystem MCP** → Gerber file management, design library

---

## Related Skills

- **mold-expert** - Plastic enclosures for PCBs
- **production-expert** - Manufacturing optimization
- **manufacturing-expert** - Quality systems

---

**Version**: 1.0.0 | **Status**: Production Ready | **License**: MIT
