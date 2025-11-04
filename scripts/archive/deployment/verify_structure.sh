#!/bin/bash
# Verify the hierarchical Category → Material → products structure

BASE_DIR="data/crawled_products_final"

echo "================================================================================"
echo "Product Organization Verification: Category → Material → products/"
echo "================================================================================"

for category in Bottle CapPump Jar; do
    echo ""
    echo "📦 $category:"

    for material in PE PET PETG PP Other; do
        dir="$BASE_DIR/$category/$material/products"

        if [ -d "$dir" ]; then
            count=$(ls "$dir" 2>/dev/null | wc -l | tr -d ' ')
            if [ "$count" -gt 0 ]; then
                echo "  ✓ $material: $count products"
            fi
        fi
    done
done

echo ""
echo "================================================================================"
echo "Summary"
echo "================================================================================"

total=0
for category in Bottle CapPump Jar; do
    category_total=0
    for material in PE PET PETG PP Other; do
        dir="$BASE_DIR/$category/$material/products"
        if [ -d "$dir" ]; then
            count=$(ls "$dir" 2>/dev/null | wc -l | tr -d ' ')
            category_total=$((category_total + count))
        fi
    done
    echo "$category: $category_total products"
    total=$((total + category_total))
done

echo "================================================================================"
echo "TOTAL: $total products organized"
echo "================================================================================"
