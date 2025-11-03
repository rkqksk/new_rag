#!/bin/bash
#
# Real-time Onehago Pipeline Monitor
# Tracks: Validation Daemon, Phase 2 Crawling, Image Download Workers
#
# Usage: bash monitor_onehago_pipeline.sh [refresh_interval]
#        Default refresh interval: 5 seconds
#

REFRESH_INTERVAL=${1:-5}

# Directories
PHASE2_DIR="/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only"
REPAIRED_DIR="/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/repaired"
IMAGE_DIR="/Users/oypnus/Project/rag-enterprise/data/onehago/images/category_2"

# Log files
VALIDATION_LOG="/tmp/onehago_validation_daemon.log"
VALIDATION_STATE="/tmp/onehago_validation_daemon_state.json"
PHASE2_LOG="/tmp/onehago_12workers_IMAGES.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to format numbers with commas
format_number() {
    printf "%'d" $1 2>/dev/null || echo $1
}

# Function to calculate percentage
calc_percentage() {
    local num=$1
    local total=$2
    if [ $total -eq 0 ]; then
        echo "0.0"
    else
        echo "scale=1; $num * 100 / $total" | bc
    fi
}

# Clear screen and show header
show_header() {
    clear
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║             ONEHAGO PIPELINE REAL-TIME MONITOR                                 ║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${BOLD}Last Update: $(date '+%Y-%m-%d %H:%M:%S')${NC} | Refresh: ${REFRESH_INTERVAL}s | Press Ctrl+C to exit"
    echo ""
}

# Check Validation Daemon Status
check_validation_daemon() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  VALIDATION DAEMON${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Check if daemon is running
    if ps aux | grep -v grep | grep "onehago_validation_daemon.py" > /dev/null; then
        echo -e "  Status: ${GREEN}● RUNNING${NC}"

        # Get PID
        local pid=$(ps aux | grep -v grep | grep "onehago_validation_daemon.py" | awk '{print $2}')
        echo -e "  PID: ${pid}"

        # Parse state file if exists
        if [ -f "$VALIDATION_STATE" ]; then
            local total_validated=$(cat "$VALIDATION_STATE" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats'].get('total_validated', 0))" 2>/dev/null || echo "0")
            local passed=$(cat "$VALIDATION_STATE" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats'].get('passed', 0))" 2>/dev/null || echo "0")
            local failed=$(cat "$VALIDATION_STATE" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats'].get('failed', 0))" 2>/dev/null || echo "0")
            local repaired=$(cat "$VALIDATION_STATE" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats'].get('repaired', 0))" 2>/dev/null || echo "0")
            local repair_failed=$(cat "$VALIDATION_STATE" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats'].get('repair_failed', 0))" 2>/dev/null || echo "0")

            echo ""
            echo -e "  ${BOLD}Statistics:${NC}"
            echo -e "    Total Validated:  $(format_number $total_validated)"
            echo -e "    ${GREEN}✓${NC} Passed:          $(format_number $passed)"
            echo -e "    ${RED}✗${NC} Failed:          $(format_number $failed)"
            echo -e "    ${GREEN}🔧${NC} Repaired:        $(format_number $repaired)"
            echo -e "    ${RED}⚠${NC}  Repair Failed:   $(format_number $repair_failed)"

            if [ $total_validated -gt 0 ]; then
                local pass_rate=$(calc_percentage $passed $total_validated)
                local repair_rate=$(calc_percentage $repaired $failed)
                echo ""
                echo -e "  ${BOLD}Rates:${NC}"
                echo -e "    Pass Rate:        ${GREEN}${pass_rate}%${NC}"
                if [ $failed -gt 0 ]; then
                    echo -e "    Repair Success:   ${YELLOW}${repair_rate}%${NC}"
                fi
            fi
        fi

        # Show recent activity
        if [ -f "$VALIDATION_LOG" ]; then
            echo ""
            echo -e "  ${BOLD}Recent Activity (last 3 lines):${NC}"
            tail -3 "$VALIDATION_LOG" | sed 's/^/    /'
        fi
    else
        echo -e "  Status: ${RED}● STOPPED${NC}"
        echo ""
        echo -e "  ${YELLOW}Start daemon:${NC}"
        echo -e "    nohup python3 scripts/onehago_validation_daemon.py > /dev/null 2>&1 &"
    fi
    echo ""
}

# Check Phase 2 Crawling Progress
check_phase2_progress() {
    echo -e "${BOLD}${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${MAGENTA}  PHASE 2 CRAWLING (Text Extraction)${NC}"
    echo -e "${BOLD}${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Count products extracted
    local worker_count=0
    local batch_count=0

    if [ -d "$PHASE2_DIR" ]; then
        worker_count=$(find "$PHASE2_DIR" -name "worker_*_output.jsonl" -type f 2>/dev/null | wc -l | tr -d ' ')
        batch_count=$(find "$PHASE2_DIR" -name "batch_*.jsonl" -type f 2>/dev/null | wc -l | tr -d ' ')

        echo -e "  Output Directory: ${PHASE2_DIR}"
        echo -e "  Worker Files:     ${worker_count}"
        echo -e "  Batch Files:      ${batch_count}"
        echo ""

        # Count total products
        local total_products=0
        for file in "$PHASE2_DIR"/worker_*_output.jsonl "$PHASE2_DIR"/batch_*.jsonl; do
            if [ -f "$file" ]; then
                local count=$(wc -l < "$file" | tr -d ' ')
                total_products=$((total_products + count))
            fi
        done

        # Count category 2 products
        local cat2_count=0
        for file in "$PHASE2_DIR"/worker_*_output.jsonl "$PHASE2_DIR"/batch_*.jsonl; do
            if [ -f "$file" ]; then
                local count=$(grep -o '"category_id": 2' "$file" 2>/dev/null | wc -l | tr -d ' ')
                cat2_count=$((cat2_count + count))
            fi
        done

        # Count detail_crawled status
        local detail_true=0
        local detail_false=0
        for file in "$PHASE2_DIR"/worker_*_output.jsonl "$PHASE2_DIR"/batch_*.jsonl; do
            if [ -f "$file" ]; then
                local true_count=$(grep -o '"detail_crawled": true' "$file" 2>/dev/null | wc -l | tr -d ' ')
                local false_count=$(grep -o '"detail_crawled": false' "$file" 2>/dev/null | wc -l | tr -d ' ')
                detail_true=$((detail_true + true_count))
                detail_false=$((detail_false + false_count))
            fi
        done

        echo -e "  ${BOLD}Products Extracted:${NC}"
        echo -e "    Total:            $(format_number $total_products)"
        echo -e "    Category 2:       $(format_number $cat2_count) ${CYAN}(packaging)${NC}"
        echo ""

        echo -e "  ${BOLD}Extraction Status:${NC}"
        echo -e "    ${GREEN}✓${NC} Success:        $(format_number $detail_true)"
        echo -e "    ${RED}✗${NC} Failed:         $(format_number $detail_false)"

        if [ $total_products -gt 0 ]; then
            local success_rate=$(calc_percentage $detail_true $total_products)
            echo -e "    Success Rate:     ${GREEN}${success_rate}%${NC}"
        fi

        # Disk usage
        local disk_usage=$(du -sh "$PHASE2_DIR" 2>/dev/null | awk '{print $1}')
        echo ""
        echo -e "  ${BOLD}Storage:${NC}"
        echo -e "    Disk Usage:       ${disk_usage}"
    else
        echo -e "  ${RED}Directory not found: ${PHASE2_DIR}${NC}"
    fi
    echo ""
}

# Check Image Download Workers
check_image_workers() {
    echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${YELLOW}  IMAGE DOWNLOAD WORKERS${NC}"
    echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Count running workers
    local worker_pids=$(ps aux | grep -v grep | grep "onehago_image_worker.py" | awk '{print $2}')
    local worker_count=$(echo "$worker_pids" | grep -v '^$' | wc -l | tr -d ' ')

    echo -e "  Active Workers:   ${worker_count}"

    if [ $worker_count -gt 0 ]; then
        echo -e "  PIDs:             $(echo $worker_pids | tr '\n' ' ')"
        echo ""

        # Aggregate statistics from all workers
        local total_products_processed=0
        local total_images_downloaded=0
        local total_images_failed=0
        local total_images_skipped=0

        for progress_file in "$IMAGE_DIR"/worker_*_progress.json; do
            if [ -f "$progress_file" ]; then
                local products=$(cat "$progress_file" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats'].get('products_processed', 0))" 2>/dev/null || echo "0")
                local downloaded=$(cat "$progress_file" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats'].get('images_downloaded', 0))" 2>/dev/null || echo "0")
                local failed=$(cat "$progress_file" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats'].get('images_failed', 0))" 2>/dev/null || echo "0")
                local skipped=$(cat "$progress_file" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats'].get('images_skipped', 0))" 2>/dev/null || echo "0")

                total_products_processed=$((total_products_processed + products))
                total_images_downloaded=$((total_images_downloaded + downloaded))
                total_images_failed=$((total_images_failed + failed))
                total_images_skipped=$((total_images_skipped + skipped))
            fi
        done

        echo -e "  ${BOLD}Overall Progress:${NC}"
        echo -e "    Products:         $(format_number $total_products_processed) / 20,464"
        echo -e "    ${GREEN}✓${NC} Downloaded:      $(format_number $total_images_downloaded)"
        echo -e "    ${RED}✗${NC} Failed:          $(format_number $total_images_failed)"
        echo -e "    ${CYAN}⊘${NC} Skipped:         $(format_number $total_images_skipped)"

        if [ $total_products_processed -gt 0 ]; then
            local progress_pct=$(calc_percentage $total_products_processed 20464)
            echo -e "    Progress:         ${GREEN}${progress_pct}%${NC}"
        fi

        # Disk usage
        if [ -d "$IMAGE_DIR" ]; then
            local image_disk=$(du -sh "$IMAGE_DIR" 2>/dev/null | awk '{print $1}')
            local product_dirs=$(find "$IMAGE_DIR" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
            local image_files=$(find "$IMAGE_DIR" -type f -name "*.jpg" -o -name "*.png" 2>/dev/null | wc -l | tr -d ' ')

            echo ""
            echo -e "  ${BOLD}Storage:${NC}"
            echo -e "    Disk Usage:       ${image_disk}"
            echo -e "    Product Folders:  $(format_number $product_dirs)"
            echo -e "    Image Files:      $(format_number $image_files)"
        fi

        # Show individual worker status
        echo ""
        echo -e "  ${BOLD}Worker Details:${NC}"
        for i in {0..7}; do
            local log_file="/tmp/onehago_image_worker_$(printf "%04d" $i).log"
            if [ -f "$log_file" ]; then
                local last_line=$(tail -1 "$log_file" 2>/dev/null)
                if [ ! -z "$last_line" ]; then
                    echo -e "    Worker $i: ${last_line:0:60}..."
                fi
            fi
        done
    else
        echo -e "  ${YELLOW}No workers running${NC}"
        echo ""
        echo -e "  ${CYAN}Start workers:${NC}"
        echo -e "    bash scripts/launch_image_workers.sh 4"
    fi
    echo ""
}

# Check System Resources
check_system_resources() {
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${GREEN}  SYSTEM RESOURCES${NC}"
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Disk space
    local disk_info=$(df -h /Users/oypnus/Project/rag-enterprise 2>/dev/null | tail -1)
    local disk_usage=$(echo "$disk_info" | awk '{print $5}')
    local disk_avail=$(echo "$disk_info" | awk '{print $4}')

    echo -e "  Disk Available:   ${disk_avail}"
    echo -e "  Disk Usage:       ${disk_usage}"

    # Memory (macOS)
    local mem_info=$(vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-16s % 16.2f Mi\n", "$1:", $2 * $size / 1048576);' 2>/dev/null | head -5)
    if [ ! -z "$mem_info" ]; then
        echo ""
        echo -e "  ${BOLD}Memory:${NC}"
        echo "$mem_info" | sed 's/^/    /'
    fi

    echo ""
}

# Main monitoring loop
echo -e "${CYAN}Starting Onehago Pipeline Monitor...${NC}"
echo -e "${CYAN}Press Ctrl+C to stop${NC}"
sleep 2

while true; do
    show_header
    check_validation_daemon
    check_phase2_progress
    check_image_workers
    check_system_resources

    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}Refreshing in ${REFRESH_INTERVAL} seconds... (Ctrl+C to exit)${NC}"
    echo ""

    sleep $REFRESH_INTERVAL
done
