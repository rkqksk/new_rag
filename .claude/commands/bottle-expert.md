---
name: bottle-expert
description: 화장품 용기 호환성 분석 및 최적 캡/펌프 추천
aliases: [용기추천]
---

# 용기 전문가 시스템

You are activating the **Bottle Expert** skill for comprehensive packaging compatibility analysis.

## Activation Context

The user has requested packaging compatibility analysis. Your task is to:

1. **Load Bottle Expert Skill**: Activate the `bottle-expert` skill for specialized knowledge
2. **Analyze Product Data**: Load and analyze product specifications from JSON files
3. **Recommend Compatible Components**: Match bottles with suitable caps/pumps
4. **Evaluate Chemical Compatibility**: Assess material suitability for cosmetic formulations
5. **Enhance Data Quality**: Update JSON files with analysis results for RAG improvement

## Task Execution

### Step 1: Parse User Request

Identify the analysis type:
- **Single Product**: `/용기추천 idx_657` → Analyze specific bottle by idx
- **Batch Analysis**: `/용기추천 --material=PET --capacity=50-150ml` → Analyze matching products
- **Comparison**: `/용기추천 compare idx_657 idx_660` → Side-by-side comparison
- **General Query**: `/용기추천 100ml 에센스 용기` → Search and recommend

### Step 2: Load Bottle Expert Skill

```
Use Skill tool to load: "bottle-expert"
```

This will provide:
- Compatibility analysis framework
- Material chemical properties
- Neck size matching logic
- Capacity-based recommendations
- Data enhancement procedures

### Step 3: Execute Analysis

Follow the workflow defined in the skill:
1. Load product data from `/Users/oypnus/Project/rag-enterprise/data/crawled_products_final/`
2. Extract specifications (capacity, neck size, material)
3. Find compatible caps/pumps using neck size matching
4. Evaluate chemical compatibility based on material
5. Recommend cosmetic applications

### Step 4: Generate Report

Produce structured analysis report including:
- 📦 Bottle specifications summary
- ✅ Compatible caps/pumps list with reasoning
- 💡 Recommended cosmetic applications
- 🔬 Material compatibility notes
- 📊 Data enhancement confirmation

### Step 5: Enhance Data

Update product JSON files with:
```json
{
  "compatibility_analysis": {
    "compatible_caps": [...],
    "compatible_pumps": [...],
    "recommended_applications": [...],
    "material_compatibility": {...},
    "analyzed_at": "ISO timestamp"
  }
}
```

## Expected Output Format

Use the standard analysis report format from the skill:

```markdown
# 용기 호환성 분석 보고서

## 📦 대상 용기 정보
[Bottle details]

## ✅ 호환 가능한 캡/펌프
[Ranked recommendations with rationale]

## 💡 추천 적용 제품군
[Application recommendations by capacity and material]

## 🔬 재질 화학적 특성
[Material compatibility details]

## 📊 데이터 보강 내역
[File update confirmation]
```

## Quality Checklist

Before completing the task, verify:
- ✅ Neck size compatibility accurately matched (치수 기반)
- ✅ Material safety evaluated against chemical properties
- ✅ Capacity ranges aligned with industry standards
- ✅ JSON files updated with `compatibility_analysis` field
- ✅ Analysis timestamp recorded
- ✅ Original data preserved (no modification of existing fields)

## Error Handling

If issues occur:
- **Product not found**: Search across all category directories
- **Missing specifications**: Report incomplete data and skip analysis
- **Invalid JSON**: Log error and continue with next product
- **Write permission**: Check file access and report if read-only

## Integration Notes

This analysis enhances RAG system performance by:
- Adding semantic metadata to product JSON files
- Enabling compatibility-based search queries
- Improving recommendation accuracy
- Providing domain-specific knowledge for LLM responses

## Examples

### Example 1: Single Product Analysis
```
User: /용기추천 idx_657

Action:
1. Load bottle-expert skill
2. Read idx_657.json from data/crawled_products_final/
3. Analyze: 100ml PETG bottle, Ø24 neck
4. Find compatible 24파이 pumps/caps
5. Recommend: essence, serum, toner applications
6. Update JSON with compatibility_analysis
7. Generate formatted report
```

### Example 2: Material-Based Batch Analysis
```
User: /용기추천 --material=PET --capacity=50-150ml

Action:
1. Load bottle-expert skill
2. Query all PET bottles in 50-150ml range
3. Analyze each bottle's specifications
4. Generate compatibility matrix
5. Export summary Excel report
6. Update all matching JSON files
```

### Example 3: Natural Language Query
```
User: /용기추천 100ml 에센스 용기 추천해줘

Action:
1. Load bottle-expert skill
2. Parse: capacity=100ml, application=essence
3. Filter: capacity 80-120ml, materials PET/PETG/PE
4. Rank by: transparency, neck size 20-24파이
5. Recommend top 5 with compatible pumps
6. Explain material suitability for essence formulations
```

## Post-Analysis Actions

After completing analysis:
1. ✅ Confirm JSON file updates
2. 📊 Log analysis to session notes (if note_management available)
3. 💡 Suggest next actions (e.g., pricing analysis, similar products)
4. 🔄 Offer batch analysis if single product requested

## Related Commands

- `/sc:analyze` - For code quality analysis
- `/sc:document` - For generating product documentation
- `note_management` skill - For recording analysis reports

---

**Remember**: Your primary goal is to enhance RAG system quality by enriching product data with compatibility analysis. Be thorough, accurate, and maintain data integrity.
