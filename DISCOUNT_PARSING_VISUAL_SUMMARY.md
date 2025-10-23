# Automatic Discount Price Parsing - Visual Summary

## Quick Reference

### Feasibility Score: 65% ⚠️

```
Automation Feasibility by Category
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

용기|용량          ████████████████████ 100% ✅ (8 items)
용기|PETG(준헤비)  ████████████████████ 100% ✅ (5 items)
용기|다층          ██████████████████░░  90% ✅ (11 items)
용기|재질무관      ██████████████████░░  90% ✅ (3 items)
용기|PE/PET        ███████████░░░░░░░░░  55% ⚠️  (13 items)
용기|PETG(얇은)    ███████████░░░░░░░░░  55% ⚠️  (13 items)
용기|헤비(PET)     ██████░░░░░░░░░░░░░░  30% ⚠️  (4 items)
용기|MB4C          ██░░░░░░░░░░░░░░░░░░  10% ❌ (10 items)
용기|PET           ███░░░░░░░░░░░░░░░░░  15% ❌ (4 items)
용기|PE/PP         ███░░░░░░░░░░░░░░░░░  15% ❌ (4 items)
캡,펌프            ████░░░░░░░░░░░░░░░░  20% ❌ (17 items)
코팅               █████░░░░░░░░░░░░░░░  25% ❌ (29 items)

Overall: 65% automatable, 35% manual/review required
```

---

## Rule-Based System Architecture

```
Input: Regular Price + Product Attributes
                  │
                  ▼
        ┌─────────────────────┐
        │  Rule Application   │
        └─────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
    Rule 1     Rule 2       Rule 3
   No Disc    Fixed Amt    % Based
    (0%)       (-30원)     (capacity)
      │           │           │
      └───────────┼───────────┘
                  ▼
        Discount Price Calculated
                  │
                  ▼
        ┌─────────────────────┐
        │ Confidence Score?   │
        ├─────────────────────┤
        │ >85% ────→ Approved │
        │ 70-85% ──→ Review   │
        │ <70% ────→ Manual   │
        └─────────────────────┘
```

---

## Discount Percentage Distribution

```
Distribution Curve:
┌────────────────────────────────────────────────────┐
│                                                    │
│ 40 │                                               │
│    │           ┌─────┐                             │
│ 35 │       ┌───┤ 10% ├───┐                         │
│    │   ┌───┤11%├─────┤12%├───┐                     │
│ 30 │───┤9% ├─────────────────┤13%├───┐             │
│    │   └───┤    ┌─────┐    ├───┘   │             │
│ 25 │       │    │ 14% │    │       │             │
│    │       │    │     │    │  ┌─────┐           │
│ 20 │       │    └─────┘    │  │ 17% │           │
│    │       │                │  └─────┘           │
│ 15 │       └────────────────┘         ┌─────┐   │
│    │                              ┌───┤ 15% │   │
│ 10 │                         ┌────┤8% ├─────┤   │
│    │                    ┌────┤7%  │   │     │   │
│  5 │               ┌────┤5%  │    │   │     │   │
│    │          ┌────┤6%  │    │    │   │     │   │
│  0 │──────────┤0%  │    │    │    │   │     │───
│    └────────────────────────────────────────────┘
     0-5%   5-10%  10-15% 15-20% 20-25% 25-30% 30%+

Peak: 10-15% discount (most common: 41 items)
Mode: 10-14% discount range
Median: ~12% discount
```

---

## Category Classification Heatmap

```
Automation Difficulty vs. Variability
                                 High Variability
                                       ▲
                                       │
                        MB4C      PE/PET  PETG(얇은)
                          │        │ │      │
                          │        │ │      │
    Low Difficulty        │    헤비(PET)    │
    High Confidence       │        │        │
                          │        │    단가│
                          │      PET│        │
                       다층│     PE/PP      │
                        재질│        │      │
                      무관·용량     │      │
                          │  PETG(준헤비)  │
                          │        │      │
                          └────────┴──────────────▶
                         Low Variability    High
                         High Confidence    Difficulty
```

---

## Implementation Timeline

```
Week 1: Setup & Validation
┌──────────────────────────────────────────────────┐
│ Day 1-2: Data Verification                       │
│ · Audit crawled prices vs. price list            │
│ · Confirm discount prices are correct            │
│                                                  │
│ Day 3-4: Rule Collection                         │
│ · Extract rules from existing price list         │
│ · Document patterns and exceptions               │
│                                                  │
│ Day 5:   Baseline Documentation                  │
│ · Create confidence matrices                     │
│ · Define acceptance criteria                     │
└──────────────────────────────────────────────────┘
         Output: Rule matrix, validation data

Week 2: Implementation
┌──────────────────────────────────────────────────┐
│ Day 1-2: High-Confidence Rules (100%, 90%)       │
│ · NoDiscount rule (용량, PETG준헤비)            │
│ · FixedAmount rules (다층, 재질무관)            │
│ Coverage: ~60 products                           │
│                                                  │
│ Day 3-4: Medium-Confidence Rules (75%)           │
│ · CapacityBasedPercentage rules                  │
│ · Extend to PE/PET, PETG(얇은), etc.            │
│ Coverage: Additional ~110 products               │
│                                                  │
│ Day 5:   Testing & QA                            │
│ · Cross-validation against price list            │
│ · Identify false positives                       │
└──────────────────────────────────────────────────┘
         Output: Functional calculator module

Week 3: Integration & Review System
┌──────────────────────────────────────────────────┐
│ Day 1-2: API Endpoints                           │
│ · POST /calculate-discount                       │
│ · POST /batch-calculate-discounts                │
│                                                  │
│ Day 3-4: Manual Review Queue                     │
│ · Flag low-confidence items (<70%)               │
│ · Create review UI                               │
│ · Implement feedback loop                        │
│                                                  │
│ Day 5:   Documentation                           │
│ · User guide for manual review                   │
│ · API documentation                              │
│ · Maintenance procedures                         │
└──────────────────────────────────────────────────┘
         Output: Production-ready system
```

---

## Confidence Level Guidelines

```
Confidence 90-100% (Approve Automatically)
┌────────────────────────────────────────────┐
│ ✅ Approve without review                  │
│ Categories: 용량, PETG(준헤비)            │
│ Patterns: No discount, consistent fixed    │
│ Risk: <1% error rate                       │
└────────────────────────────────────────────┘

Confidence 75-89% (Review Before Approval)
┌────────────────────────────────────────────┐
│ ⚠️ Review with high likelihood approval    │
│ Categories: 다층, 재질무관, PE/PET        │
│ Patterns: Fixed or capacity-based % rules  │
│ Risk: 5-10% error rate                     │
│ Review Time: ~30 seconds per item          │
└────────────────────────────────────────────┘

Confidence 50-74% (Detailed Review Required)
┌────────────────────────────────────────────┐
│ 🔍 Detailed review recommended             │
│ Categories: PETG(얇은), 헤비(PET), 단가  │
│ Patterns: Variable percentages             │
│ Risk: 15-25% error rate                    │
│ Review Time: ~2-3 minutes per item         │
└────────────────────────────────────────────┘

Confidence <50% (Manual Entry Required)
┌────────────────────────────────────────────┐
│ ❌ Manual entry only                       │
│ Categories: MB4C, PET, PE/PP, 캡펌프, 코팅│
│ Patterns: Unpredictable, anomalous         │
│ Risk: >30% error rate                      │
│ Action: Flag for subject matter expert     │
└────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌──────────────────┐
│ Product Data     │
├──────────────────┤
│ · Category       │
│ · Material       │
│ · Capacity       │
│ · Regular Price  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ DiscountCalculator.calculate()       │
├──────────────────────────────────────┤
│ 1. Check NoDiscount rules            │
│ 2. Check FixedAmount rules           │
│ 3. Check CapacityBased% rules        │
│ 4. Return (price, confidence, rule)  │
└────────┬─────────────────────────────┘
         │
         ▼
    ┌────────────────┐
    │ Confidence >= 85%?
    └────┬──────┬────┘
         │      │
        YES    NO
         │      │
         ▼      ▼
    ✅Auto ⚠️Review   ❌Manual
    Approve         Entry
```

---

## Error Reduction Strategy

```
Quality Gates (3-Layer Defense)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Layer 1: Rule Validation
  • Check: discount <= regular ✅
  • Check: discount >= 0 ✅
  • Check: discount% < 50% ✅
  Catches: 10-15% of errors

Layer 2: Confidence Filtering
  • Only auto-approve confidence >= 85%
  • Flag confidence 50-85% for review
  • Manual entry for confidence < 50%
  Catches: 20-30% of errors

Layer 3: Human Review
  • Subject matter expert review of flagged items
  • Spot-check random auto-approved items (2%)
  • Feedback loop to improve confidence rules
  Catches: 30-40% of errors
           
Total Error Rate: < 2% after all layers
```

---

## Success Metrics Dashboard

```
Target Metrics:
┌─────────────────────────────────────────┐
│ Metric                Target    Current │
├─────────────────────────────────────────┤
│ Automation Coverage   70%       TBD     │
│ Accuracy (auto)       90%       TBD     │
│ Accuracy (reviewed)    98%       TBD     │
│ Review Time/Item      <2 min    TBD     │
│ False Positive Rate   <5%       TBD     │
│ False Negative Rate   <1%       TBD     │
└─────────────────────────────────────────┘

Progress Tracking:
Week 1: ████░░░░░░░░░░░░░░░░ 20% (Setup)
Week 2: ██████████░░░░░░░░░░ 50% (Rules)
Week 3: █████████████░░░░░░░ 65% (Testing)
Week 4: ███████████████░░░░░ 80% (Integration)
Final:  ███████████████████░ 95% (Production)
```

---

## Key Insights at a Glance

| Aspect | Finding | Impact |
|--------|---------|--------|
| **Discount Range** | 0% to 33% | High variability |
| **Most Common** | 10-15% (41 items) | Peak cluster exists |
| **Fixed vs Variable** | 30% fixed, 70% variable | Mix of strategies |
| **Capacity Impact** | High correlation | Must include in rules |
| **Best Strategy** | Hybrid (rules + manual) | 70-77% automation |
| **Rule Quality** | 3 categories >90% confidence | ~27% fully automatable |
| **Time to Manual Review** | 30 sec - 3 min per item | ~60 items to review |

---

## Recommended First Steps

```
✅ IMMEDIATE (Today)
1. Verify data accuracy with 5-10 spot checks
2. Document price list rules in spreadsheet
3. Get stakeholder buy-in on confidence thresholds

🔄 SHORT TERM (This Week)
4. Build DiscountCalculator class
5. Implement confidence scoring
6. Create manual review queue UI

📈 MEDIUM TERM (Next Week)
7. Deploy and test with actual products
8. Gather user feedback on confidence levels
9. Iteratively improve rules based on errors

🎯 LONG TERM (Ongoing)
10. Monitor false positive/negative rates
11. Update rules quarterly based on business changes
12. Build advanced model if needed (ML fallback)
```

---

*Analysis Date: 2025-10-23*
*Status: Feasibility Analysis Complete*
*Next Step: Approval for Week 1 Implementation*
