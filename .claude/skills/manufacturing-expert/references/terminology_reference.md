# Manufacturing Expert - Terminology Reference

Comprehensive reference for manufacturing terminology, standards, and quality metrics.

---

## Document Classification Types

### 1. SOP (Standard Operating Procedure)
- **Indicators**: procedure, instruction, standard operating, work instruction
- **Examples**: Assembly procedures, testing protocols, operational guidelines
- **Categories**: process, compliance, quality

### 2. Equipment Specification
- **Indicators**: equipment, machine, specification, capacity, technical data
- **Examples**: CNC machine specs, injection molding equipment, test equipment
- **Categories**: equipment, specifications, technical

### 3. Control Plan (FMEA)
- **Indicators**: control plan, FMEA, risk assessment, failure mode, process control
- **Examples**: Process FMEA, Design FMEA, Control plans
- **Categories**: quality, risk, planning

### 4. Defect Analysis
- **Indicators**: root cause, 8D, defect, failure, investigation, corrective action
- **Examples**: 8D reports, Root cause analysis, Corrective action reports
- **Categories**: quality, analysis, improvement

### 5. Maintenance Records
- **Indicators**: maintenance, preventive, calibration, repair, service
- **Examples**: PM schedules, Calibration records, Repair logs
- **Categories**: maintenance, equipment, compliance

### 6. Batch Records
- **Indicators**: batch, lot, production record, manufacturing record
- **Examples**: Production batch records, Lot traceability, Manufacturing logs
- **Categories**: production, traceability, compliance

### 7. Deviation Reports
- **Indicators**: deviation, non-conformance, NCR, exception, variance
- **Examples**: NCR reports, Deviation reports, Exception handling
- **Categories**: quality, compliance, investigation

### 8. General Manufacturing
- **Fallback**: Any manufacturing-related document not matching above types

---

## Quality Metrics

### Process Capability Indices

#### Cpk (Process Capability Index)
- **Pattern**: `Cpk`, `C_pk`, `cpk =`, `capability index`
- **Interpretation**:
  - Cpk ≥ 1.67: Excellent (5 sigma)
  - Cpk ≥ 1.33: Capable (4 sigma)
  - Cpk ≥ 1.00: Marginally capable (3 sigma)
  - Cpk < 1.00: Not capable
- **Formula**: `Cpk = min[(USL - μ)/(3σ), (μ - LSL)/(3σ)]`

#### Cp (Process Capability Ratio)
- **Pattern**: `Cp`, `C_p`, `cp =`
- **Interpretation**:
  - Cp ≥ 2.0: Excellent
  - Cp ≥ 1.33: Adequate
  - Cp < 1.0: Poor
- **Formula**: `Cp = (USL - LSL)/(6σ)`

### Overall Equipment Effectiveness (OEE)

- **Pattern**: `OEE`, `overall equipment effectiveness`, `equipment efficiency`
- **Interpretation**:
  - OEE ≥ 85%: World class
  - OEE ≥ 60%: Acceptable
  - OEE < 60%: Poor
- **Components**: `OEE = Availability × Performance × Quality`

### Defect Metrics

#### PPM (Parts Per Million)
- **Pattern**: `PPM`, `ppm`, `parts per million`, `defects per million`
- **Interpretation**:
  - PPM < 100: Excellent (6 sigma)
  - PPM < 1000: Good (4-5 sigma)
  - PPM > 10000: Poor

#### FPY (First Pass Yield)
- **Pattern**: `FPY`, `first pass yield`, `first time yield`
- **Interpretation**:
  - FPY ≥ 99%: Excellent
  - FPY ≥ 95%: Good
  - FPY < 90%: Poor

### Reliability Metrics

#### MTBF (Mean Time Between Failures)
- **Pattern**: `MTBF`, `mean time between failures`
- **Unit**: Hours
- **Higher is better**

#### MTTR (Mean Time To Repair)
- **Pattern**: `MTTR`, `mean time to repair`
- **Unit**: Hours
- **Lower is better**

### Production Metrics

#### Yield
- **Pattern**: `yield`, `production yield`, `process yield`
- **Formula**: `(Good units / Total units) × 100%`

#### Takt Time
- **Pattern**: `takt time`, `takt`, `customer demand rate`
- **Formula**: `Available time / Customer demand`

#### Cycle Time
- **Pattern**: `cycle time`, `process time`
- **Total time from start to finish**

---

## Standards and Compliance

### ISO Standards

#### ISO 9001 (Quality Management)
- **Pattern**: `ISO 9001`, `iso 9001`, `9001:2015`
- **Focus**: Quality management systems
- **Key Requirements**: Process approach, risk-based thinking, continuous improvement

#### ISO 13485 (Medical Devices)
- **Pattern**: `ISO 13485`, `iso 13485`, `13485:2016`
- **Focus**: Medical device quality management
- **Key Requirements**: Risk management, traceability, validation

#### ISO 14001 (Environmental)
- **Pattern**: `ISO 14001`, `iso 14001`, `14001:2015`
- **Focus**: Environmental management systems
- **Key Requirements**: Environmental policy, compliance, continual improvement

#### IATF 16949 (Automotive)
- **Pattern**: `IATF 16949`, `iatf 16949`, `16949:2016`
- **Focus**: Automotive quality management
- **Key Requirements**: Defect prevention, variation reduction, waste reduction

### FDA Regulations

#### FDA 21 CFR Part 11
- **Pattern**: `21 CFR Part 11`, `cfr 11`, `part 11`
- **Focus**: Electronic records and signatures
- **Key Requirements**: Validation, audit trails, electronic signatures

#### FDA 21 CFR Part 820
- **Pattern**: `21 CFR Part 820`, `cfr 820`, `part 820`, `QSR`
- **Focus**: Quality System Regulation (medical devices)
- **Key Requirements**: Design controls, CAPA, risk management

### GMP (Good Manufacturing Practice)
- **Pattern**: `GMP`, `cGMP`, `good manufacturing practice`
- **Focus**: Manufacturing quality and compliance
- **Key Requirements**: Personnel, facilities, equipment, processes, quality control

---

## Process Parameters

### Temperature
- **Patterns**: `°C`, `°F`, `temperature`, `temp`
- **Examples**: Process temperature, mold temperature, ambient temperature

### Pressure
- **Patterns**: `MPa`, `psi`, `bar`, `pressure`
- **Examples**: Injection pressure, hydraulic pressure, air pressure

### Time
- **Patterns**: `seconds`, `minutes`, `hours`, `cycle time`, `dwell time`
- **Examples**: Cooling time, cure time, process cycle time

### Speed
- **Patterns**: `rpm`, `m/min`, `mm/s`, `speed`, `rate`
- **Examples**: Spindle speed, feed rate, injection speed

### Flow Rate
- **Patterns**: `ml/min`, `L/min`, `gpm`, `flow rate`
- **Examples**: Material flow, coolant flow, air flow

---

## Production Methods

### Injection Molding
- **Keywords**: injection, mold, cavity, runner, gate, ejector
- **Parameters**: Temperature, pressure, cooling time, cycle time

### CNC Machining
- **Keywords**: CNC, milling, turning, drilling, tooling
- **Parameters**: Speed, feed rate, depth of cut, tool life

### Assembly
- **Keywords**: assembly, joining, fastening, installation
- **Methods**: Manual, automated, semi-automated

### Coating/Finishing
- **Keywords**: coating, painting, plating, anodizing
- **Methods**: Spray, dip, electrostatic, powder

---

## Quality Tools

### Statistical Process Control (SPC)
- **Tools**: Control charts, histograms, Pareto charts
- **Patterns**: `SPC`, `control chart`, `statistical process`

### Six Sigma
- **Methodology**: DMAIC (Define, Measure, Analyze, Improve, Control)
- **Patterns**: `Six Sigma`, `6 sigma`, `DMAIC`, `black belt`

### Lean Manufacturing
- **Tools**: 5S, Kaizen, Value Stream Mapping, Kanban
- **Patterns**: `lean`, `5S`, `kaizen`, `waste`, `muda`

### Root Cause Analysis
- **Tools**: 5 Why, Fishbone diagram, Fault tree analysis
- **Patterns**: `root cause`, `5 why`, `fishbone`, `ishikawa`

---

## Validation and Verification

### IQ (Installation Qualification)
- **Pattern**: `IQ`, `installation qualification`
- **Focus**: Equipment properly installed

### OQ (Operational Qualification)
- **Pattern**: `OQ`, `operational qualification`
- **Focus**: Equipment operates within specifications

### PQ (Performance Qualification)
- **Pattern**: `PQ`, `performance qualification`
- **Focus**: Process produces acceptable results

---

## Change Management

### ECO (Engineering Change Order)
- **Pattern**: `ECO`, `engineering change`, `design change`
- **Process**: Request → Evaluation → Approval → Implementation → Verification

### CAPA (Corrective and Preventive Action)
- **Pattern**: `CAPA`, `corrective action`, `preventive action`
- **Process**: Problem → Root cause → Corrective action → Preventive action → Verification

---

**Last Updated**: 2025-01-25
**Version**: 1.0
**Maintained By**: Manufacturing Expert SKILL
