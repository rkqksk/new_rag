---
name: production-expert
description: Production Expert Skill
---

# Production Expert Skill

**Version**: 1.0.0
**Status**: Production Ready ✅
**Purpose**: Production planning, lean manufacturing, quality control, and operations optimization

> **Production management expertise** - Lean manufacturing, Six Sigma, capacity planning, inventory management, and continuous improvement.

---

## Quick Reference

### Commands

```bash
# Planning & Scheduling
production capacity-plan <product> --demand <units/month>   # Capacity planning
production schedule <orders> --resources <machines>         # Production scheduling
production bottleneck-analysis <process-map>                # Bottleneck identification
production lead-time <process> --target <days>              # Lead time optimization

# Lean Manufacturing
production takt-time <demand> --available-time <hours>      # Takt time calculation
production kanban-sizing <demand> --lead-time <days>        # Kanban system design
production 5s-audit <area>                                  # 5S workplace audit
production vsm <process>                                    # Value Stream Mapping

# Quality Control
production spc-chart <measurements> --type <x-bar-r>        # SPC chart generation
production cpk-analysis <data> --usl <val> --lsl <val>      # Process capability
production pareto-analysis <defects>                        # Defect prioritization
production fmea <process>                                   # FMEA analysis

# Performance Metrics
production oee <availability> <performance> <quality>       # OEE calculation
production kpi-dashboard <metrics>                          # KPI dashboard
production cost-variance <actual> --budget <planned>        # Cost analysis
```

---

## Core Expertise

### 1. Production Planning & Control

**Capacity Planning**:
```
Required Capacity = Demand / (Available Time × Efficiency)

Example:
Demand: 10,000 units/month
Available time: 176 hours/month (22 days × 8 hours)
Efficiency: 85%
Required capacity: 10,000 / (176 × 0.85) = 67 units/hour
```

**Production Scheduling Methods**:

| Method | Best For | Complexity |
|--------|----------|------------|
| **FIFO** | Simple, low variety | Low |
| **SPT** (Shortest Processing Time) | Minimize WIP | Medium |
| **EDD** (Earliest Due Date) | Meet deadlines | Medium |
| **Critical Ratio** | Dynamic prioritization | High |
| **TOC** (Theory of Constraints) | Bottleneck optimization | High |

**Material Requirements Planning (MRP)**:
```
Net Requirement = Gross Requirement - On-Hand Inventory - Scheduled Receipts + Safety Stock

Lead Time Offset:
Order Release Date = Due Date - Lead Time
```

---

### 2. Lean Manufacturing

**7 Wastes (TIMWOOD)**:
1. **T**ransportation - Unnecessary material movement
2. **I**nventory - Excess WIP, raw materials
3. **M**otion - Wasted operator movement
4. **W**aiting - Idle time
5. **O**verproduction - Making more than needed
6. **O**ver-processing - More than customer requires
7. **D**efects - Rework, scrap

**Lean Tools**:

**5S System**:
```
1. Sort (整理) - Remove unnecessary items
2. Set in Order (整頓) - Organize workspace
3. Shine (清掃) - Clean workspace
4. Standardize (清潔) - Create standards
5. Sustain (躾) - Maintain discipline
```

**Takt Time**:
```
Takt Time = Available Production Time / Customer Demand

Example:
Available time: 480 minutes/day
Demand: 240 units/day
Takt time: 480 / 240 = 2 minutes/unit
```

**Kanban System**:
```
Number of Kanbans = (Demand × Lead Time × (1 + Safety Factor)) / Container Size

Example:
Demand: 100 units/day
Lead time: 2 days
Safety factor: 20%
Container: 50 units
Kanbans: (100 × 2 × 1.2) / 50 = 4.8 ≈ 5 kanbans
```

**Value Stream Mapping (VSM)**:
- Map current state
- Identify waste
- Design future state
- Implement improvements

---

### 3. Six Sigma & Quality Control

**DMAIC Methodology**:
```
Define: Problem, goal, customer requirements
Measure: Collect data, baseline performance
Analyze: Root cause analysis (5 Whys, Fishbone)
Improve: Implement solutions, pilot test
Control: Monitor, sustain improvements
```

**Statistical Process Control (SPC)**:

**Control Charts**:
| Chart Type | Application | Formula |
|------------|-------------|---------|
| **X̄-R Chart** | Variable data (continuous) | UCL = X̄ + A₂R̄ |
| **P Chart** | Attribute data (proportion) | UCL = p̄ + 3√(p̄(1-p̄)/n) |
| **C Chart** | Count of defects | UCL = c̄ + 3√c̄ |

**Process Capability**:
```
Cp = (USL - LSL) / (6σ)  # Process potential
Cpk = min((USL - μ) / 3σ, (μ - LSL) / 3σ)  # Process performance

Target:
Cpk ≥ 1.33 (capable)
Cpk ≥ 1.67 (highly capable)
Cpk ≥ 2.00 (world-class)
```

**Sigma Levels**:
| Sigma | DPMO | Yield | Quality Level |
|-------|------|-------|---------------|
| 3σ | 66,807 | 93.3% | Poor |
| 4σ | 6,210 | 99.38% | Average |
| 5σ | 233 | 99.977% | Good |
| 6σ | 3.4 | 99.9997% | World-class |

---

### 4. Performance Metrics (KPIs)

**OEE (Overall Equipment Effectiveness)**:
```
OEE = Availability × Performance × Quality

Availability = Operating Time / Planned Production Time
Performance = (Actual Output / Theoretical Output)
Quality = Good Units / Total Units

Example:
Availability: 90% (18h operating / 20h planned)
Performance: 85% (170 units / 200 theoretical)
Quality: 95% (161 good / 170 total)
OEE = 0.90 × 0.85 × 0.95 = 72.7%

World-class OEE: ≥ 85%
```

**Other Key Metrics**:

| Metric | Formula | Target |
|--------|---------|--------|
| **On-Time Delivery** | (On-time orders / Total orders) × 100% | ≥ 95% |
| **First Pass Yield** | (Good units / Total units) × 100% | ≥ 95% |
| **Scrap Rate** | (Scrap units / Total units) × 100% | < 2% |
| **Cycle Time** | Time to produce one unit | Minimize |
| **Throughput** | Units produced / Time period | Maximize |
| **Inventory Turnover** | COGS / Average Inventory | ≥ 12× |

---

### 5. Inventory Management

**Inventory Types**:
- **Raw Materials** - Incoming materials
- **Work-in-Progress (WIP)** - Partially completed
- **Finished Goods** - Completed, awaiting shipment

**Economic Order Quantity (EOQ)**:
```
EOQ = √((2 × D × S) / H)

Where:
D = Annual demand
S = Ordering cost per order
H = Holding cost per unit per year

Example:
Demand: 10,000 units/year
Ordering cost: $100/order
Holding cost: $5/unit/year
EOQ = √((2 × 10,000 × 100) / 5) = 632 units
```

**Reorder Point**:
```
ROP = (Demand per day × Lead time) + Safety Stock

Example:
Demand: 100 units/day
Lead time: 10 days
Safety stock: 200 units
ROP = (100 × 10) + 200 = 1,200 units
```

**ABC Classification**:
- **A items**: 20% of items, 80% of value (tight control)
- **B items**: 30% of items, 15% of value (moderate control)
- **C items**: 50% of items, 5% of value (loose control)

---

### 6. Production Costing

**Cost Components**:
```
Total Production Cost = Direct Materials + Direct Labor + Manufacturing Overhead

Manufacturing Overhead Rate = Total Overhead / Direct Labor Hours

Product Cost = DM + DL + (DL Hours × OH Rate)
```

**Cost Analysis Example**:
```
Product: Plastic container

Direct Materials: $0.50/unit
Direct Labor: $0.30/unit (0.05 hours @ $6/hour)
Overhead: $0.20/unit (0.05 hours @ $4/hour)
Total Cost: $1.00/unit

Selling Price: $1.50/unit
Gross Margin: ($1.50 - $1.00) / $1.50 = 33%
```

**Break-Even Analysis**:
```
Break-Even Point = Fixed Costs / (Price - Variable Cost per Unit)

Example:
Fixed costs: $100,000/month
Price: $10/unit
Variable cost: $6/unit
BEP = $100,000 / ($10 - $6) = 25,000 units/month
```

---

### 7. Continuous Improvement

**Kaizen Events**:
- **Duration**: 3-5 days
- **Team**: Cross-functional (5-10 people)
- **Focus**: Specific problem area
- **Goal**: Rapid improvement (30-50%)
- **Follow-up**: 30-60-90 day reviews

**PDCA Cycle** (Plan-Do-Check-Act):
```
Plan: Identify problem, develop solution
Do: Implement on small scale (pilot)
Check: Measure results, compare to goal
Act: Standardize if successful, adjust if not

Repeat cycle for continuous improvement
```

**Root Cause Analysis (RCA)**:

**5 Whys**:
```
Problem: Machine stopped
Why? Overload, fuse blew
Why? Bearing inadequate lubrication
Why? Oil pump not working
Why? Pump shaft worn out
Why? No strainer, metal chips entered
Root cause: No strainer on pump
```

**Fishbone Diagram** (Ishikawa):
```
                    Man
                     |
    Machine -------- PROBLEM -------- Method
                     |
                  Material
```

---

### 8. Quality Management Systems

**ISO 9001 Requirements**:
1. Context of organization
2. Leadership commitment
3. Risk-based thinking
4. Process approach
5. Continual improvement
6. Customer focus
7. Evidence-based decisions

**Quality Documents**:
- **Level 1**: Quality manual
- **Level 2**: Procedures
- **Level 3**: Work instructions
- **Level 4**: Records, forms

**Audit Types**:
- **Internal**: By own organization
- **External** (2nd party): By customer
- **Certification** (3rd party): By certifying body

**CAPA (Corrective/Preventive Action)**:
```
1. Problem identification
2. Immediate containment
3. Root cause analysis
4. Corrective action plan
5. Implementation
6. Effectiveness verification
7. Standardization
```

---

### 9. Production Best Practices

**Workplace Organization**:
- Visual management (andon boards)
- Standard work procedures
- Quick changeover (SMED - Single-Minute Exchange of Die)
- Total Productive Maintenance (TPM)

**Operator Training**:
- Cross-training (flexibility)
- Standard work training
- Quality awareness
- Problem-solving skills

**Safety (OSHA)**:
- Machine guarding
- Lockout/Tagout (LOTO)
- Personal Protective Equipment (PPE)
- Emergency procedures

**Environmental (ISO 14001)**:
- Waste reduction
- Energy efficiency
- Hazardous material management
- Regulatory compliance

---

### 10. Industry 4.0 & Smart Manufacturing

**Key Technologies**:
- **IoT Sensors**: Real-time monitoring
- **Big Data Analytics**: Predictive maintenance
- **AI/ML**: Quality prediction, optimization
- **Robotics**: Automation, cobots
- **Digital Twin**: Virtual simulation
- **MES (Manufacturing Execution System)**: Shop floor control

**Benefits**:
- Reduced downtime (predictive maintenance)
- Improved quality (real-time SPC)
- Increased flexibility (agile manufacturing)
- Lower costs (waste reduction)

**Implementation Roadmap**:
1. Assess current state (maturity level)
2. Define vision & strategy
3. Pilot projects (quick wins)
4. Scale successful projects
5. Continuous optimization

---

## Best Practices

1. **Data-Driven Decision Making**
   - Collect accurate data
   - Analyze with statistical tools
   - Base decisions on facts

2. **Employee Empowerment**
   - Train operators in problem-solving
   - Encourage suggestions
   - Recognize contributions

3. **Customer Focus**
   - Understand customer requirements
   - Deliver on-time, quality products
   - Continuous feedback loop

4. **Waste Elimination**
   - Identify non-value-added activities
   - Implement lean tools
   - Measure improvements

---

## MCP Integration

**Filesystem MCP** → Production data analysis, report generation
**PostgreSQL MCP** → Production database, quality records

---

## Related Skills

- **manufacturing-expert** - Quality systems, inspection
- **mold-expert** - Tooling, process optimization
- **business-expert** - Strategic planning

---

**Version**: 1.0.0 | **Status**: Production Ready | **License**: MIT
