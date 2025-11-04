#!/usr/bin/env python3
"""
Phase 2 Benchmark Monitor Dashboard - Flask Web Interface

Real-time monitoring dashboard for 15-worker benchmark validation crawl.
Access at: http://localhost:5555

Features:
- Real-time worker status and progress
- Overall statistics and completion tracking
- Quality metrics comparison
- ETA calculation
"""

from flask import Flask, render_template_string
import json
from pathlib import Path
from datetime import datetime
import os

app = Flask(__name__)

# Configuration
BENCHMARK_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/benchmark')
PROGRESS_DIR = BENCHMARK_DIR / 'progress'
TOTAL_WORKERS = 14
TOTAL_PRODUCTS = 22901

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Phase 2 Benchmark Monitor</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="3">
    <style>
        body {
            font-family: 'Monaco', 'Courier New', monospace;
            background-color: #1a1a1a;
            color: #00ff00;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        h1 {
            color: #00ffff;
            text-align: center;
            border-bottom: 2px solid #00ff00;
            padding-bottom: 15px;
            font-size: 32px;
        }
        .purpose-box {
            background: #2a2a2a;
            border: 2px solid #ffff00;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #ffff00;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-box {
            background: #2a2a2a;
            border: 2px solid #00ff00;
            border-radius: 8px;
            padding: 15px;
        }
        .stat-label {
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
        }
        .stat-value {
            color: #00ffff;
            font-size: 28px;
            font-weight: bold;
            margin-top: 5px;
        }
        .progress-bar {
            width: 100%;
            height: 40px;
            background: #333;
            border-radius: 20px;
            overflow: hidden;
            margin: 20px 0;
            border: 2px solid #00ff00;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff00, #00ffff);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-weight: bold;
            font-size: 18px;
        }
        .worker-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }
        .worker-card {
            background: #2a2a2a;
            border: 2px solid #555;
            border-radius: 5px;
            padding: 12px;
        }
        .worker-card.running {
            border-color: #00ff00;
        }
        .worker-card.completed {
            border-color: #00ffff;
            opacity: 0.7;
        }
        .worker-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .worker-stat {
            font-size: 12px;
            color: #aaa;
            margin: 3px 0;
        }
        .status-running {
            color: #00ff00;
        }
        .status-completed {
            color: #00ffff;
        }
        .status-idle {
            color: #666;
        }
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
        .quality-comparison {
            background: #2a2a2a;
            border: 2px solid #00ffff;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }
        .quality-comparison h3 {
            color: #00ffff;
            margin-top: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 PHASE 2 BENCHMARK VALIDATION MONITOR</h1>

        <div class="purpose-box">
            <strong>🎯 PURPOSE:</strong> Validate existing packaging extraction by re-crawling all 22,901 unique products
            <br>
            <strong>📊 MODE:</strong> Text-only extraction (no images) with 15 parallel workers
            <br>
            <strong>✅ GOAL:</strong> Compare new extraction with existing data to verify quality
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-label">Overall Progress</div>
                <div class="stat-value">{{ "%.1f"|format(overall_progress) }}%</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Products Processed</div>
                <div class="stat-value">{{ "{:,}".format(total_products_done) }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Active Workers</div>
                <div class="stat-value">{{ active_workers }}/{{ total_workers }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Completed Workers</div>
                <div class="stat-value">{{ completed_workers }}/{{ total_workers }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Success Rate</div>
                <div class="stat-value">{{ "%.1f"|format(success_rate) }}%</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Extraction Rate</div>
                <div class="stat-value">{{ rate }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Estimated Time Remaining</div>
                <div class="stat-value">{{ eta }}</div>
            </div>
        </div>

        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ overall_progress }}%">
                {{ "%.1f"|format(overall_progress) }}%
            </div>
        </div>

        {% if quality_metrics %}
        <div class="quality-comparison">
            <h3>📊 Quality Metrics</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                <div>
                    <div style="color: #888; font-size: 12px;">Total Fields Extracted</div>
                    <div style="color: #00ffff; font-size: 20px;">{{ "{:,}".format(quality_metrics.total_fields) }}</div>
                </div>
                <div>
                    <div style="color: #888; font-size: 12px;">Product Names</div>
                    <div style="color: #00ffff; font-size: 20px;">{{ "{:,}".format(quality_metrics.product_names) }}</div>
                </div>
                <div>
                    <div style="color: #888; font-size: 12px;">Specifications</div>
                    <div style="color: #00ffff; font-size: 20px;">{{ "{:,}".format(quality_metrics.specifications) }}</div>
                </div>
                <div>
                    <div style="color: #888; font-size: 12px;">Company Info</div>
                    <div style="color: #00ffff; font-size: 20px;">{{ "{:,}".format(quality_metrics.company_info) }}</div>
                </div>
                <div>
                    <div style="color: #888; font-size: 12px;">Image URLs</div>
                    <div style="color: #00ffff; font-size: 20px;">{{ "{:,}".format(quality_metrics.images) }}</div>
                </div>
            </div>
        </div>
        {% endif %}

        <h2 style="margin-top: 30px; color: #00ffff;">Worker Status ({{ total_workers }} workers)</h2>

        <div class="worker-grid">
            {% for worker in workers %}
            <div class="worker-card {{ worker.status_class }}">
                <div class="worker-title">
                    Worker {{ "%02d"|format(worker.id) }}
                    <span class="status-{{ worker.status_class }}">{{ worker.status }}</span>
                </div>
                <div class="worker-stat">Range: {{ "{:,}".format(worker.start) }}-{{ "{:,}".format(worker.end) }}</div>
                <div class="worker-stat">Processed: {{ "{:,}".format(worker.products_done) }}/{{ "{:,}".format(worker.total_products) }}</div>
                <div class="worker-stat">Success: {{ "{:,}".format(worker.success) }} | Failed: {{ worker.failed }}</div>
                {% if worker.progress_pct > 0 %}
                <div class="worker-stat">Progress: {{ "%.1f"|format(worker.progress_pct) }}%</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>

        <div class="timestamp">
            Last updated: {{ current_time }}
            <br>
            Page auto-refreshes every 3 seconds
        </div>
    </div>
</body>
</html>
"""

def get_worker_progress():
    """Read all worker progress files"""
    workers = []
    PRODUCTS_PER_WORKER = (TOTAL_PRODUCTS + TOTAL_WORKERS - 1) // TOTAL_WORKERS

    for worker_id in range(TOTAL_WORKERS):
        start_product = worker_id * PRODUCTS_PER_WORKER
        end_product = min((worker_id + 1) * PRODUCTS_PER_WORKER, TOTAL_PRODUCTS)
        total_products = end_product - start_product

        progress_file = PROGRESS_DIR / f'worker_{worker_id:04d}_progress.json'

        worker_data = {
            'id': worker_id,
            'start': start_product,
            'end': end_product,
            'total_products': total_products,
            'products_done': 0,
            'success': 0,
            'failed': 0,
            'status': 'Idle',
            'status_class': 'idle',
            'progress_pct': 0.0
        }

        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    worker_data['products_done'] = data.get('products_processed', 0)
                    worker_data['success'] = data.get('products_success', 0)
                    worker_data['failed'] = data.get('products_failed', 0)

                    if total_products > 0:
                        worker_data['progress_pct'] = (worker_data['products_done'] / total_products) * 100

                    if worker_data['products_done'] >= total_products:
                        worker_data['status'] = 'Completed'
                        worker_data['status_class'] = 'completed'
                    elif worker_data['products_done'] > 0:
                        worker_data['status'] = 'Running'
                        worker_data['status_class'] = 'running'
            except:
                pass

        workers.append(worker_data)

    return workers

def calculate_stats(workers):
    """Calculate overall statistics"""
    total_products_done = sum(w['products_done'] for w in workers)
    total_success = sum(w['success'] for w in workers)
    total_failed = sum(w['failed'] for w in workers)
    active_workers = sum(1 for w in workers if w['status_class'] == 'running')
    completed_workers = sum(1 for w in workers if w['status_class'] == 'completed')

    overall_progress = (total_products_done / TOTAL_PRODUCTS) * 100 if TOTAL_PRODUCTS > 0 else 0
    success_rate = (total_success / total_products_done * 100) if total_products_done > 0 else 0

    # Calculate ETA
    if total_products_done > 0 and overall_progress < 100:
        products_remaining = TOTAL_PRODUCTS - total_products_done
        if active_workers > 0:
            avg_rate = total_products_done / max(active_workers, 1)  # products per worker
            time_remaining_seconds = products_remaining / active_workers * 1.5  # ~1.5 sec per product
            hours = int(time_remaining_seconds // 3600)
            minutes = int((time_remaining_seconds % 3600) // 60)
            eta = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            rate = f"{total_products_done / (time_remaining_seconds / 60):.0f}/min"
        else:
            eta = "N/A"
            rate = "N/A"
    else:
        eta = "Complete!" if overall_progress >= 100 else "Starting..."
        rate = "N/A"

    # Quality metrics
    quality_metrics = None
    if total_products_done > 0:
        total_fields = 0
        product_names = 0
        specifications = 0
        company_info = 0
        images = 0

        for worker_id in range(TOTAL_WORKERS):
            progress_file = PROGRESS_DIR / f'worker_{worker_id:04d}_progress.json'
            if progress_file.exists():
                try:
                    with open(progress_file, 'r') as f:
                        data = json.load(f)
                        fields = data.get('fields_extracted', {})
                        product_names += fields.get('product_name', 0)
                        specifications += sum(v for k, v in fields.items() if k.startswith('spec_'))
                        company_info += sum(v for k, v in fields.items() if 'company' in k or k in ['phone', 'fax', 'email'])
                        images += fields.get('images', 0)
                except:
                    pass

        total_fields = product_names + specifications + company_info + images
        quality_metrics = {
            'total_fields': total_fields,
            'product_names': product_names,
            'specifications': specifications,
            'company_info': company_info,
            'images': images
        }

    return {
        'total_products_done': total_products_done,
        'active_workers': active_workers,
        'completed_workers': completed_workers,
        'overall_progress': overall_progress,
        'success_rate': success_rate,
        'eta': eta,
        'rate': rate,
        'quality_metrics': quality_metrics
    }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    workers = get_worker_progress()
    stats = calculate_stats(workers)

    return render_template_string(
        HTML_TEMPLATE,
        workers=workers,
        total_workers=TOTAL_WORKERS,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        **stats
    )

def main():
    print("="*80)
    print("🔍 PHASE 2 BENCHMARK MONITOR DASHBOARD")
    print("="*80)
    print()
    print("📊 Dashboard starting on http://localhost:5555")
    print()
    print("Features:")
    print("  - Real-time worker status (15 workers)")
    print("  - Progress tracking and ETA")
    print("  - Quality metrics")
    print("  - Auto-refresh every 3 seconds")
    print()
    print("🌐 Open in browser: http://localhost:5555")
    print()
    print("Press Ctrl+C to stop the monitor")
    print("="*80)
    print()

    app.run(host='0.0.0.0', port=5555, debug=False)

if __name__ == '__main__':
    main()
