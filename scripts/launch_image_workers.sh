#!/bin/bash
#
# Launch multiple background image download workers for Onehago category 2
# Automatically splits 20,464 products across N workers
#

NUM_WORKERS=4  # Default: 4 workers
TOTAL_PRODUCTS=20464  # Total category 2 products

# Parse arguments
if [ "$1" != "" ]; then
    NUM_WORKERS=$1
fi

# Calculate products per worker
PRODUCTS_PER_WORKER=$((TOTAL_PRODUCTS / NUM_WORKERS))

echo "🚀 ONEHAGO IMAGE DOWNLOAD WORKERS LAUNCHER"
echo "=========================================="
echo ""
echo "📊 Configuration:"
echo "   Total category 2 products: $TOTAL_PRODUCTS"
echo "   Number of workers: $NUM_WORKERS"
echo "   Products per worker: ~$PRODUCTS_PER_WORKER"
echo ""
echo "📁 Source: /Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only"
echo "📁 Output: /Users/oypnus/Project/rag-enterprise/data/onehago/images/category_2/"
echo ""

# Launch workers
echo "🔄 Launching $NUM_WORKERS workers in background..."
echo ""

for ((i=0; i<NUM_WORKERS; i++)); do
    START=$((i * PRODUCTS_PER_WORKER))

    # Last worker gets any remainder
    if [ $i -eq $((NUM_WORKERS - 1)) ]; then
        END=$TOTAL_PRODUCTS
    else
        END=$(((i + 1) * PRODUCTS_PER_WORKER))
    fi

    echo "📦 Worker $i: Products $START - $END"

    # Launch worker in background
    nohup python3 /Users/oypnus/Project/rag-enterprise/scripts/onehago_image_worker.py $i $START $END > /dev/null 2>&1 &

    WORKER_PID=$!
    echo "   ✅ Started (PID: $WORKER_PID)"
    echo "   📝 Log: /tmp/onehago_image_worker_$(printf "%04d" $i).log"
    echo ""

    # Small delay between launches
    sleep 1
done

echo "=========================================="
echo "✅ All $NUM_WORKERS workers launched!"
echo ""
echo "📊 Monitor progress:"
echo "   tail -f /tmp/onehago_image_worker_0000.log"
echo "   tail -f /tmp/onehago_image_worker_0001.log"
echo "   ..."
echo ""
echo "📈 Check status:"
echo "   ps aux | grep onehago_image_worker"
echo ""
echo "🛑 Stop all workers:"
echo "   pkill -f onehago_image_worker"
echo ""
echo "📁 Download progress:"
echo "   ls -lh /Users/oypnus/Project/rag-enterprise/data/onehago/images/category_2/"
echo ""
echo "=========================================="
