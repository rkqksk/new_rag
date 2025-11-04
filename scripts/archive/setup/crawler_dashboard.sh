#!/bin/bash
# Live Crawler Dashboard
# Shows real-time progress of all 16 crawlers

clear

while true; do
    clear
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║          🚀 ONEHAGO TURBO CRAWLER DASHBOARD (16x)                 ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo ""

    # Check running crawlers
    RUNNING=$(ps aux | grep "onehago_complete_parallel" | grep -v grep | wc -l | tr -d ' ')
    echo "📊 Status: $RUNNING/16 crawlers running"
    echo ""

    # Categories completed
    COMPLETED=$(ls data/onehago/crawled/categories/*.json 2>/dev/null | wc -l | tr -d ' ')
    echo "✅ Categories completed: $COMPLETED/18"
    echo ""

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  #  │ Category │ Phase        │ Progress              │ Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Crawler 0 - Categories 2, 62
    LAST=$(tail -1 /tmp/onehago_turbo_0.log 2>/dev/null | grep -oE "Page [0-9]+" | grep -oE "[0-9]+" || echo "0")
    if grep -q "Category 2 complete" /tmp/onehago_turbo_0.log 2>/dev/null; then
        echo "  0  │   2,62   │ List         │ Cat 2: ✅ Done       │ 🔄 Cat 62"
    else
        echo "  0  │   2,62   │ List         │ Cat 2: Page $LAST/103 │ 🔄 Running"
    fi

    # Crawler 1 - Categories 3, 72
    LAST=$(tail -1 /tmp/onehago_turbo_1.log 2>/dev/null | grep -oE "Page [0-9]+" | grep -oE "[0-9]+" || tail -1 /tmp/onehago_turbo_1.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || echo "Page 0")
    if grep -q "Category 3 complete" /tmp/onehago_turbo_1.log 2>/dev/null; then
        echo "  1  │   3,72   │ Detail       │ Cat 3: ✅ Done       │ 🔄 Cat 72"
    else
        echo "  1  │   3,72   │ Detail/List  │ Cat 3: $LAST        │ 🔄 Running"
    fi

    # Crawler 2 - Category 4
    LAST=$(tail -1 /tmp/onehago_turbo_2.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_2.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 4 complete" /tmp/onehago_turbo_2.log 2>/dev/null; then
        echo "  2  │    4     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo "  2  │    4     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 3 - Category 5
    LAST=$(tail -1 /tmp/onehago_turbo_3.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_3.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 5 complete" /tmp/onehago_turbo_3.log 2>/dev/null; then
        echo "  3  │    5     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo "  3  │    5     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 4 - Category 7
    LAST=$(tail -1 /tmp/onehago_turbo_4.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_4.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 7 complete" /tmp/onehago_turbo_4.log 2>/dev/null; then
        echo "  4  │    7     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo "  4  │    7     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 5 - Category 8
    LAST=$(tail -1 /tmp/onehago_turbo_5.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_5.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 8 complete" /tmp/onehago_turbo_5.log 2>/dev/null; then
        echo "  5  │    8     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo "  5  │    8     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 6 - Category 12
    LAST=$(tail -1 /tmp/onehago_turbo_6.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]")
    if grep -q "Category 12 complete" /tmp/onehago_turbo_6.log 2>/dev/null; then
        echo "  6  │   12     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo "  6  │   12     │ Detail       │ $LAST               │ 🔄 Running"
    fi

    # Crawler 7 - Category 13
    LAST=$(tail -1 /tmp/onehago_turbo_7.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_7.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 13 complete" /tmp/onehago_turbo_7.log 2>/dev/null; then
        echo "  7  │   13     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo "  7  │   13     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 8 - Category 16
    LAST=$(tail -1 /tmp/onehago_turbo_8.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_8.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 16 complete" /tmp/onehago_turbo_8.log 2>/dev/null; then
        echo "  8  │   16     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo "  8  │   16     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 9 - Category 17
    LAST=$(tail -1 /tmp/onehago_turbo_9.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_9.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 17 complete" /tmp/onehago_turbo_9.log 2>/dev/null; then
        echo "  9  │   17     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo "  9  │   17     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 10 - Category 19
    LAST=$(tail -1 /tmp/onehago_turbo_10.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]")
    if grep -q "Category 19 complete" /tmp/onehago_turbo_10.log 2>/dev/null; then
        echo " 10  │   19     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo " 10  │   19     │ Detail       │ $LAST               │ 🔄 Running"
    fi

    # Crawler 11 - Category 25
    if grep -q "Category 25 complete" /tmp/onehago_turbo_11.log 2>/dev/null; then
        echo " 11  │   25     │ Complete     │ ✅ Complete          │ ✅ Done"
    else
        LAST=$(tail -1 /tmp/onehago_turbo_11.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || echo "Starting")
        echo " 11  │   25     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 12 - Category 26
    LAST=$(tail -1 /tmp/onehago_turbo_12.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_12.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 26 complete" /tmp/onehago_turbo_12.log 2>/dev/null; then
        echo " 12  │   26     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo " 12  │   26     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 13 - Category 27
    LAST=$(tail -1 /tmp/onehago_turbo_13.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_13.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 27 complete" /tmp/onehago_turbo_13.log 2>/dev/null; then
        echo " 13  │   27     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo " 13  │   27     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 14 - Category 30
    LAST=$(tail -1 /tmp/onehago_turbo_14.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]" || tail -1 /tmp/onehago_turbo_14.log 2>/dev/null | grep -oE "Page [0-9]+" | tail -1)
    if grep -q "Category 30 complete" /tmp/onehago_turbo_14.log 2>/dev/null; then
        echo " 14  │   30     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo " 14  │   30     │ Detail/List  │ $LAST               │ 🔄 Running"
    fi

    # Crawler 15 - Category 31
    LAST=$(tail -1 /tmp/onehago_turbo_15.log 2>/dev/null | grep -oE "\[[0-9]+/[0-9]+\]")
    if grep -q "Category 31 complete" /tmp/onehago_turbo_15.log 2>/dev/null; then
        echo " 15  │   31     │ Detail       │ ✅ Complete          │ ✅ Done"
    else
        echo " 15  │   31     │ Detail       │ $LAST               │ 🔄 Running"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Error check
    ERRORS=0
    for i in {0..15}; do
        if grep -qi "error\|failed\|timeout\|refused" /tmp/onehago_turbo_${i}.log 2>/dev/null; then
            ERRORS=$((ERRORS + 1))
        fi
    done

    if [ $ERRORS -gt 0 ]; then
        echo "⚠️  Errors detected in $ERRORS crawler(s)"
    else
        echo "✅ No errors detected"
    fi

    echo ""
    echo "📈 Performance:"

    # Calculate speed from one of the active crawlers
    if [ -f /tmp/onehago_turbo_15.log ]; then
        PRODUCTS=$(grep -oE "\[[0-9]+/" /tmp/onehago_turbo_15.log 2>/dev/null | tail -1 | grep -oE "[0-9]+" || echo "0")
        ELAPSED=$(($(date +%s) - $(stat -f %B /tmp/onehago_turbo_15.log 2>/dev/null || echo $(date +%s))))
        if [ $ELAPSED -gt 0 ] && [ $PRODUCTS -gt 0 ]; then
            RATE=$(( PRODUCTS * 60 / ELAPSED ))
            COMBINED=$(( RATE * 16 ))
            echo "   Speed: ~$RATE products/min per crawler (~$COMBINED combined)"

            # Estimate completion
            REMAINING=$(( 45000 - (PRODUCTS * 16) ))
            if [ $COMBINED -gt 0 ]; then
                ETA_MIN=$(( REMAINING / COMBINED ))
                ETA_HOURS=$(( ETA_MIN / 60 ))
                ETA_MIN_REMAINDER=$(( ETA_MIN % 60 ))
                echo "   ETA: ~${ETA_HOURS}h ${ETA_MIN_REMAINDER}m remaining"
            fi
        fi
    fi

    echo ""
    echo "🔄 Refresh: every 10 seconds (Ctrl+C to exit)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    sleep 10
done
