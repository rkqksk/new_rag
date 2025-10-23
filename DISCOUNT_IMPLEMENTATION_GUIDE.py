"""
Discount Price Calculation Implementation Guide

This module provides practical implementation examples for the
automatic discount price parsing system based on feasibility analysis.
"""

from typing import Dict, Tuple, Optional, List
from enum import Enum
import json


class ConfidenceLevel(Enum):
    """Confidence levels for discount calculations"""
    VERY_HIGH = 100  # 90-100%
    HIGH = 90        # 80-90%
    MEDIUM = 75      # 70-80%
    LOW = 50         # 50-70%
    VERY_LOW = 25    # <50%


class DiscountRule:
    """Base class for discount rules"""
    
    def __init__(self, name: str, confidence: int):
        self.name = name
        self.confidence = confidence
    
    def apply(self, regular_price: int, **kwargs) -> Optional[int]:
        """
        Apply discount rule to regular price.
        Returns calculated discount price or None if rule doesn't apply.
        """
        raise NotImplementedError


class NoDiscountRule(DiscountRule):
    """Rule for products with no discount"""
    
    def __init__(self):
        super().__init__("No Discount", ConfidenceLevel.VERY_HIGH.value)
    
    def apply(self, regular_price: int, **kwargs) -> int:
        """Discount equals regular price"""
        return regular_price


class FixedAmountRule(DiscountRule):
    """Rule for fixed amount discounts"""
    
    def __init__(self, category: str, material: str, discount_amount: int):
        self.category = category
        self.material = material
        self.discount_amount = discount_amount
        confidence = ConfidenceLevel.HIGH.value if discount_amount > 0 else ConfidenceLevel.VERY_HIGH.value
        super().__init__(f"Fixed {discount_amount}원", confidence)
    
    def apply(self, regular_price: int, **kwargs) -> int:
        """Apply fixed amount discount"""
        return max(0, regular_price - self.discount_amount)


class CapacityBasedPercentageRule(DiscountRule):
    """Rule for capacity-dependent percentage discounts"""
    
    def __init__(self, category: str, material: str, capacity_rates: Dict[str, float]):
        self.category = category
        self.material = material
        self.capacity_rates = capacity_rates
        super().__init__("Capacity-Based %", ConfidenceLevel.MEDIUM.value)
    
    def apply(self, regular_price: int, capacity: Optional[str] = None, **kwargs) -> Optional[int]:
        """Apply capacity-based percentage discount"""
        if capacity is None or capacity not in self.capacity_rates:
            return None
        
        rate = self.capacity_rates[capacity]
        return int(regular_price * (1 - rate))


class DiscountCalculator:
    """Main discount calculator using rule-based approach"""
    
    def __init__(self):
        self.rules: List[Tuple[callable, DiscountRule]] = []
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize all discount rules from price list analysis"""
        
        # Rule 1: No discount categories
        self._add_rule(
            lambda cat, mat, **kw: (cat, mat) in [
                ('용기', '용량'),
                ('용기', 'PETG(준헤비)')
            ],
            NoDiscountRule()
        )
        
        # Rule 2: Fixed amount discounts
        fixed_discounts = {
            ('용기', '다층'): 30,
            ('용기', '재질무관'): 10,
        }
        for (cat, mat), amount in fixed_discounts.items():
            self._add_rule(
                lambda c, m, cat=cat, mat=mat, **kw: c == cat and m == mat,
                FixedAmountRule(cat, mat, amount)
            )
        
        # Rule 3: Capacity-based percentage discounts
        capacity_rates = {
            ('용기', 'PE/PET'): {
                '10-50': 0.29,
                '80': 0.19,
                '100': 0.28,
                '120': 0.25,
                '150': 0.25,
                '200': 0.30,
                '250': 0.26,
                '300': 0.23,
            },
            ('용기', 'PETG(얇은)'): {
                '10-50': 0.27,
                '80': 0.25,
                '100': 0.15,
                '120': 0.14,
                '150': 0.13,
                '200': 0.18,
                '250': 0.16,
                '300': 0.19,
            },
            ('용기', 'MB4C'): {
                '10-50': 0.18,
                '80': 0.21,
                '100': 0.33,
                '120': 0.23,
                '150': 0.24,
                '200': 0.29,
                '250': 0.31,
                '300': 0.21,
            },
            ('용기', '헤비(PET)'): {
                '10-50': 0.11,
                '100': 0.29,
                '150': 0.28,
                '200': 0.28,
                '250': 0.28,
            },
            ('용기', '단가'): {
                '10-50': 0.14,
                '80': 0.17,
                '100': 0.19,
                '120': 0.17,
                '150': 0.18,
                '200': 0.21,
                '250': 0.20,
            },
        }
        
        for (cat, mat), rates in capacity_rates.items():
            self._add_rule(
                lambda c, m, cat=cat, mat=mat, **kw: c == cat and m == mat,
                CapacityBasedPercentageRule(cat, mat, rates)
            )
    
    def _add_rule(self, condition: callable, rule: DiscountRule):
        """Add a discount rule"""
        self.rules.append((condition, rule))
    
    def calculate(
        self,
        category: str,
        material: str,
        regular_price: int,
        capacity: Optional[str] = None,
        **kwargs
    ) -> Tuple[Optional[int], int, str]:
        """
        Calculate discount price with confidence score.
        
        Returns:
            (discount_price, confidence, rule_name)
            discount_price: calculated price or None if no rule matches
            confidence: confidence percentage (25-100)
            rule_name: name of applied rule
        """
        
        # Try each rule in order
        for condition, rule in self.rules:
            if condition(category, material, **kwargs):
                result = rule.apply(
                    regular_price,
                    capacity=capacity,
                    category=category,
                    material=material,
                    **kwargs
                )
                if result is not None:
                    return (result, rule.confidence, rule.name)
        
        # No matching rule
        return (None, ConfidenceLevel.VERY_LOW.value, "No matching rule")
    
    def batch_calculate(self, items: List[Dict]) -> List[Dict]:
        """
        Calculate discounts for multiple items.
        
        Args:
            items: List of dicts with keys:
                   category, material, regular_price, capacity (optional)
        
        Returns:
            List of dicts with added keys:
            discount_price, discount_confidence, discount_rule
        """
        results = []
        for item in items:
            discount_price, confidence, rule = self.calculate(
                category=item.get('category'),
                material=item.get('material'),
                regular_price=item.get('regular_price'),
                capacity=item.get('capacity_ml'),
            )
            
            result_item = item.copy()
            result_item['calculated_discount_price'] = discount_price
            result_item['discount_confidence'] = confidence
            result_item['discount_rule'] = rule
            result_item['requires_review'] = confidence < 70
            
            results.append(result_item)
        
        return results


class QualityAssurance:
    """Quality assurance and validation for discount calculations"""
    
    @staticmethod
    def validate_price(regular: int, discount: int) -> Tuple[bool, str]:
        """Validate that discount price makes sense"""
        
        if discount > regular:
            return (False, "Discount price exceeds regular price")
        
        if discount < 0:
            return (False, "Discount price is negative")
        
        discount_pct = ((regular - discount) / regular) * 100
        if discount_pct > 50:
            return (False, f"Discount too high ({discount_pct:.1f}% > 50%)")
        
        return (True, "OK")
    
    @staticmethod
    def identify_anomalies(items: List[Dict]) -> List[Tuple[int, str]]:
        """Identify anomalous items that might need manual review"""
        anomalies = []
        
        for i, item in enumerate(items):
            discount = item.get('calculated_discount_price')
            confidence = item.get('discount_confidence', 0)
            
            if confidence < 50:
                anomalies.append((i, "Low confidence calculation"))
            elif discount is None:
                anomalies.append((i, "No rule matched"))
            else:
                is_valid, msg = QualityAssurance.validate_price(
                    item.get('regular_price'),
                    discount
                )
                if not is_valid:
                    anomalies.append((i, msg))
        
        return anomalies


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_single_calculation():
    """Example: Calculate discount for single product"""
    calc = DiscountCalculator()
    
    # Example 1: No discount category
    price, confidence, rule = calc.calculate(
        category='용기',
        material='용량',
        regular_price=100,
        capacity='10-50'
    )
    print(f"Example 1 (No Discount):")
    print(f"  Regular: 100원 → Discount: {price}원")
    print(f"  Confidence: {confidence}%, Rule: {rule}\n")
    
    # Example 2: Fixed amount discount
    price, confidence, rule = calc.calculate(
        category='용기',
        material='다층',
        regular_price=250,
        capacity='10-50'
    )
    print(f"Example 2 (Fixed Amount):")
    print(f"  Regular: 250원 → Discount: {price}원")
    print(f"  Confidence: {confidence}%, Rule: {rule}\n")
    
    # Example 3: Capacity-based percentage
    price, confidence, rule = calc.calculate(
        category='용기',
        material='PE/PET',
        regular_price=140,
        capacity='10-50'
    )
    print(f"Example 3 (Capacity-Based %):")
    print(f"  Regular: 140원 → Discount: {price}원")
    print(f"  Confidence: {confidence}%, Rule: {rule}\n")


def example_batch_calculation():
    """Example: Calculate discounts for multiple products"""
    calc = DiscountCalculator()
    
    items = [
        {'category': '용기', 'material': '용량', 'regular_price': 100, 'capacity_ml': '10-50'},
        {'category': '용기', 'material': '다층', 'regular_price': 250, 'capacity_ml': '10-50'},
        {'category': '용기', 'material': 'PE/PET', 'regular_price': 140, 'capacity_ml': '10-50'},
        {'category': '용기', 'material': 'MB4C', 'regular_price': 170, 'capacity_ml': '10-50'},
        {'category': '캡,펌프', 'material': None, 'regular_price': 100, 'capacity_ml': None},
    ]
    
    results = calc.batch_calculate(items)
    
    print("Batch Calculation Results:")
    print("-" * 100)
    for i, result in enumerate(results):
        print(f"{i+1}. {result['category']} | {result.get('material', 'N/A')}")
        print(f"   Regular: {result['regular_price']}원 → Discount: {result['calculated_discount_price']}원")
        print(f"   Confidence: {result['discount_confidence']}%, Rule: {result['discount_rule']}")
        if result['requires_review']:
            print(f"   ⚠️ REQUIRES MANUAL REVIEW")
        print()


def example_quality_check():
    """Example: Quality assurance check"""
    items = [
        {'regular_price': 140, 'calculated_discount_price': 100},
        {'regular_price': 100, 'calculated_discount_price': 120},  # Invalid
        {'regular_price': 300, 'calculated_discount_price': 100},  # Very high discount
    ]
    
    print("Quality Assurance Check:")
    print("-" * 60)
    for i, item in enumerate(items):
        is_valid, msg = QualityAssurance.validate_price(
            item['regular_price'],
            item['calculated_discount_price']
        )
        status = "✅" if is_valid else "❌"
        print(f"{i+1}. {item['regular_price']}원 → {item['calculated_discount_price']}원: {status} {msg}")


if __name__ == '__main__':
    print("=" * 100)
    print("DISCOUNT PRICE CALCULATION IMPLEMENTATION EXAMPLES")
    print("=" * 100)
    print()
    
    example_single_calculation()
    example_batch_calculation()
    example_quality_check()
    
    print("\n" + "=" * 100)
    print("END OF EXAMPLES")
    print("=" * 100)
