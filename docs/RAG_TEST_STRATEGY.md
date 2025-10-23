# RAG Service Integration Testing Strategy
**Created**: 2025-10-22
**Status**: Design Phase
**Embedding Progress**: Running (PID 54810)

## Test Architecture

### Test Pyramid
```
    /\
   /  \  E2E Integration Tests (5%)
  /____\
 /      \ API Integration Tests (20%)
/__________\ Unit Tests (75%)
```

## 1. Capacity Query Tests (High Priority)

### 1.1 Exact Match Tests
**Purpose**: Verify exact capacity filtering works correctly

```python
test_cases = [
    {
        "query": "50ml 용기 추천해줘",
        "expected_capacity": 50,
        "tolerance": 0,
        "min_results": 5,
        "category_filter": None,
        "validation": {
            "all_results_have_50ml": True,
            "response_time_ms": 2000,
            "confidence_min": 0.7
        }
    },
    {
        "query": "100ml PET 병",
        "expected_capacity": 100,
        "material": "PET",
        "category": "Bottle",
        "validation": {
            "all_results_pet": True,
            "all_results_100ml": True
        }
    },
    {
        "query": "정확히 30ml 크림 용기",
        "expected_capacity": 30,
        "category": "Jar",
        "validation": {
            "exact_match_only": True,
            "no_fuzzy_results": True
        }
    }
]
```

### 1.2 Fuzzy Match Tests
**Purpose**: Verify tolerance-based capacity matching

```python
fuzzy_test_cases = [
    {
        "query": "대략 50ml 병",
        "target_capacity": 50,
        "tolerance_ml": 5,  # Accept 45-55ml
        "expected_range": (45, 55),
        "validation": {
            "results_in_range": True,
            "sorted_by_proximity": True
        }
    },
    {
        "query": "50ml 정도 되는 용기",
        "target": 50,
        "tolerance_percent": 10,  # Accept 45-55ml
        "validation": {
            "closest_first": True,
            "max_deviation_ml": 5
        }
    }
]
```

### 1.3 Edge Cases
```python
edge_cases = [
    {
        "query": "1ml 샘플 용기",
        "expected": "smallest_available",
        "notes": "Test minimum capacity handling"
    },
    {
        "query": "1000ml 대용량 병",
        "expected": "largest_available",
        "notes": "Test maximum capacity"
    },
    {
        "query": "15ml과 30ml 용기",
        "expected": "multiple_capacities",
        "validation": {
            "returns_both_sizes": True
        }
    },
    {
        "query": "ml 없는 쿼리",  # No capacity specified
        "expected": "general_recommendation",
        "validation": {
            "no_filtering": True,
            "relevance_based": True
        }
    }
]
```

## 2. Material Query Tests

### 2.1 Single Material Tests
```python
material_tests = [
    {
        "query": "PET 재질 병",
        "expected_material": "PET",
        "category": "Bottle",
        "validation": {
            "all_results_pet": True,
            "no_other_materials": True
        }
    },
    {
        "query": "PP 펌프",
        "expected_material": "PP",
        "category": "CapPump",
        "notes": "Multi-material assembly - may return 'Other'"
    },
    {
        "query": "PETG 화장품 용기",
        "expected_material": "PETG",
        "validation": {
            "all_petg": True,
            "cosmetic_grade": True
        }
    }
]
```

### 2.2 Multi-Material Comparison
```python
comparison_tests = [
    {
        "query": "PET vs PETG 병 비교",
        "expected": {
            "materials": ["PET", "PETG"],
            "comparison_mode": True
        },
        "validation": {
            "returns_both_materials": True,
            "explains_differences": True
        }
    }
]
```

## 3. Category Query Tests

### 3.1 Category Filtering
```python
category_tests = [
    {
        "query": "병 추천",
        "expected_category": "Bottle",
        "validation": {
            "only_bottles": True,
            "diversity_across_materials": True
        }
    },
    {
        "query": "펌프 용기",
        "expected_category": "CapPump",
        "notes": "Should include 11 applicators moved from 특별폴더"
    },
    {
        "query": "크림 jar",
        "expected_category": "Jar",
        "validation": {
            "wide_opening": True,
            "suitable_for_creams": True
        }
    }
]
```

### 3.2 Applicator-Specific Tests (New)
```python
applicator_tests = [
    {
        "query": "트리거 스프레이",
        "expected": {
            "category": "CapPump",
            "material": "Other",
            "product_ids": ["idx_697", "idx_698", "..."]  # From 특별폴더
        },
        "validation": {
            "includes_moved_products": True,
            "category_label_cappump": True
        }
    },
    {
        "query": "미스트 펌프",
        "expected_category": "CapPump",
        "notes": "idx_925, idx_926 from moved set"
    },
    {
        "query": "건스프레이",
        "expected": "idx_697",  # 28파이 건스프레이
        "validation": {
            "material_other": True,
            "category_cappump": True
        }
    }
]
```

## 4. Combined Filter Tests

### 4.1 Capacity + Material
```python
combined_tests = [
    {
        "query": "50ml PET 병",
        "filters": {
            "capacity": 50,
            "material": "PET",
            "category": "Bottle"
        },
        "validation": {
            "all_criteria_met": True,
            "ranked_by_relevance": True
        }
    },
    {
        "query": "30ml PETG 크림 용기",
        "filters": {
            "capacity": 30,
            "material": "PETG",
            "category": "Jar"
        },
        "expected_products": "specific_jars",
        "validation": {
            "exact_match_preferred": True
        }
    }
]
```

### 4.2 Korean + English Mixed
```python
mixed_language_tests = [
    {
        "query": "50ml bottle PET 재질",
        "expected": "handles_mixed_language",
        "validation": {
            "understands_both": True,
            "same_as_korean_only": True
        }
    }
]
```

## 5. Special Cases (특별폴더 Products)

### 5.1 Moved Product Verification
```python
moved_products_tests = [
    {
        "product_ids": [
            "idx_697", "idx_698", "idx_699", "idx_700",
            "idx_701", "idx_702", "idx_821", "idx_925",
            "idx_926", "idx_946", "idx_950"
        ],
        "validation": {
            "all_in_cappump_category": True,
            "category_label_cappump": True,
            "material_other": True,
            "searchable": True
        },
        "test": "Direct lookup by idx"
    },
    {
        "query": "applicator",
        "expected": "includes_moved_products",
        "validation": {
            "returns_pumps_triggers": True,
            "no_special_category_label": True
        }
    }
]
```

## 6. Performance Tests

### 6.1 Response Time
```python
performance_tests = [
    {
        "query": "50ml 용기",
        "max_response_time_ms": 2000,
        "percentiles": {
            "p50": 1000,
            "p95": 1800,
            "p99": 2000
        }
    },
    {
        "concurrent_queries": 10,
        "max_avg_response_ms": 3000,
        "notes": "Load test with parallel requests"
    }
]
```

### 6.2 Embedding Quality
```python
embedding_quality_tests = [
    {
        "test": "semantic_similarity",
        "query_pairs": [
            ("50ml 병", "50ml 용기"),  # Should be very similar
            ("PET 재질", "PET material"),  # Cross-language
            ("크림 jar", "크림 용기")  # Synonym handling
        ],
        "min_similarity": 0.85
    }
]
```

## 7. Negative Tests

### 7.1 Invalid Inputs
```python
negative_tests = [
    {
        "query": "",
        "expected": "error_or_general_results",
        "validation": {
            "no_crash": True,
            "helpful_message": True
        }
    },
    {
        "query": "9999ml 용기",
        "expected": "no_results_or_largest",
        "validation": {
            "handles_out_of_range": True
        }
    },
    {
        "query": "존재하지않는재질 병",
        "expected": "graceful_fallback",
        "validation": {
            "returns_relevant_anyway": True
        }
    }
]
```

## 8. Packaging Designer Skill Integration Tests

### 8.1 Heavy Blow Technology Queries
```python
packaging_skill_tests = [
    {
        "query": "헤비브로우 50ml jar",
        "expected": {
            "skill_activation": "packaging_designer",
            "product_results": True,
            "consultation": {
                "heavy_blow_explanation": True,
                "wall_thickness": "2.5-5mm",
                "cost_analysis": True,
                "printable_area_calc": True
            }
        }
    },
    {
        "query": "glass-like 럭셔리 용기",
        "expected": {
            "recommends_heavy_blow": True,
            "material": "PETG",
            "products": "heavy_blow_candidates"
        }
    }
]
```

### 8.2 Material Consultation
```python
material_consultation_tests = [
    {
        "query": "cosmetic cream에 적합한 재질",
        "expected": {
            "skill_response": True,
            "materials": ["PETG", "PP", "PET"],
            "reasoning": True,
            "product_recommendations": True
        }
    }
]
```

## 9. Production Engineer Skill Integration Tests

### 9.1 Manufacturing Process Queries
```python
production_skill_tests = [
    {
        "query": "injection molding 50ml jar",
        "expected": {
            "skill_activation": "production_engineer",
            "process_details": True,
            "parameters": {
                "temperature": True,
                "pressure": True,
                "cycle_time": True
            },
            "product_matches": True
        }
    },
    {
        "query": "EBM process bottle",
        "expected": {
            "manufacturing_method": "Extrusion Blow Molding",
            "suitable_products": "PE bottles",
            "process_explanation": True
        }
    }
]
```

### 9.2 Defect Troubleshooting
```python
defect_tests = [
    {
        "query": "sink mark 문제 해결",
        "expected": {
            "skill_response": True,
            "diagnosis": True,
            "solutions": True,
            "related_products": "thick_wall_products"
        }
    }
]
```

## 10. Test Execution Plan

### Phase 1: Unit Tests (Week 1)
- [ ] Capacity filtering logic
- [ ] Material extraction from specs
- [ ] Category classification
- [ ] Embedding generation

### Phase 2: Integration Tests (Week 2)
- [ ] Qdrant query accuracy
- [ ] FastAPI endpoint responses
- [ ] Skill activation logic
- [ ] Multi-filter combinations

### Phase 3: E2E Tests (Week 3)
- [ ] Full user journey tests
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Edge case validation

### Phase 4: 특별폴더 Migration Validation (Immediate)
- [ ] Verify all 11 products in CapPump/Other
- [ ] Confirm category_label = "cappump"
- [ ] Test applicator queries return moved products
- [ ] Validate image paths still work

## 11. Success Criteria

### Must Have ✅
- [ ] **Capacity filtering accuracy**: >95% for exact matches
- [ ] **Material filtering accuracy**: >90%
- [ ] **Response time**: <2s for p95
- [ ] **All 846 products searchable**: Including 11 moved applicators
- [ ] **No crashes on invalid input**: Graceful error handling

### Should Have 🎯
- [ ] **Fuzzy capacity matching**: ±10% tolerance working
- [ ] **Skill integration**: Packaging designer + production engineer active
- [ ] **Multi-language support**: Korean + English queries
- [ ] **Synonym handling**: "병" = "bottle" = "용기"

### Nice to Have 🌟
- [ ] **Conversational memory**: Multi-turn query refinement
- [ ] **Image search**: Visual similarity (currently disabled)
- [ ] **Printable area calculation**: Real-time from Parasolid data

## 12. Test Data Preparation

### 12.1 Known Good Products
```python
test_product_set = {
    "50ml_bottles": {
        "PET": ["idx_XXX", "idx_YYY"],
        "PETG": ["idx_ZZZ"],
        "expected_count": 15
    },
    "applicators": {
        "triggers": ["idx_697", "idx_698", "idx_699"],
        "mist_pumps": ["idx_925", "idx_926"],
        "all_moved": 11
    },
    "heavy_blow_candidates": {
        "material": "PETG",
        "wall_thickness": ">2.5mm",
        "weight": ">80g"
    }
}
```

## 13. Monitoring & Metrics

### 13.1 Quality Metrics
- **Precision**: Relevant results / Total returned
- **Recall**: Relevant returned / Total relevant
- **F1 Score**: Harmonic mean of precision & recall
- **MRR (Mean Reciprocal Rank)**: First relevant result position

### 13.2 Performance Metrics
- **Latency**: p50, p95, p99 response times
- **Throughput**: Queries per second
- **Error Rate**: Failed requests / Total requests
- **Cache Hit Rate**: Redis cache effectiveness

## 14. Test Automation

### 14.1 Continuous Testing
```bash
# Run after each code change
pytest tests/integration/test_rag_queries.py -v

# Performance regression tests
pytest tests/performance/ --benchmark

# Moved products validation
pytest tests/migration/test_special_folder_move.py
```

### 14.2 Test Reports
- HTML coverage report: `htmlcov/index.html`
- Performance trends: Grafana dashboard
- Quality metrics: Weekly email report

---

## Next Steps

**IMMEDIATE** (While embeddings run):
1. Implement basic capacity filtering tests
2. Create test fixtures for 11 moved applicators
3. Set up test database with known products

**AFTER EMBEDDINGS COMPLETE** (~9:00 AM):
1. Run smoke tests on all 846 products
2. Validate moved products searchable
3. Execute Phase 1 test suite
4. Generate test report

**BLOCKED UNTIL**:
- Embeddings complete (PID 54810)
- FastAPI service started
- Ollama service verified

---

**Test Strategy Owner**: Claude
**Review Required**: User approval before Phase 2
**Estimated Test Development**: 2-3 days
**Estimated Test Execution**: 1 day (after embeddings)
