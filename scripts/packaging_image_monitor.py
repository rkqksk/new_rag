#!/usr/bin/env python3
"""
Packaging Image Download Monitor Dashboard

Real-time web dashboard for monitoring 14-worker packaging image download system.
Access at: http://localhost:5555

Features:
- Real-time worker status
- Progress tracking per worker
- Overall statistics
- Storage estimation
- ETA calculation
"""
from flask import Flask, render_template_string, jsonify
import json
import glob
from pathlib import Path
from datetime import datetime
import subprocess

app = Flask(__name__)

# Configuration
IMAGE_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/images/packaging')
TOTAL_WORKERS = 14
TOTAL_PRODUCTS = 22457
PRODUCTS_PER_WORKER = (TOTAL_PRODUCTS + TOTAL_WORKERS - 1) // TOTAL_WORKERS

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Packaging Image Download Monitor</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">  <!-- Auto-refresh every 5 seconds -->
    <style>
        body {
            font-family: 'Monaco', 'Courier New', monospace;
            background-color: #1a1a1a;
            color: #00ff00;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #00ffff;
            text-align: center;
            border-bottom: 2px solid #00ff00;
            padding-bottom: 15px;
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
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #333;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
            border: 1px solid #00ff00;
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
        }
        .worker-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }
        .worker-card {
            background: #2a2a2a;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 10px;
        }
        .worker-card.active {
            border-color: #00ff00;
        }
        .worker-card.completed {
            border-color: #00ffff;
            opacity: 0.7;
        }
        .worker-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .worker-stat {
            font-size: 12px;
            color: #888;
            margin: 3px 0;
        }
        .status-running {
            color: #00ff00;
        }
        .status-completed {
            color: #00ffff;
        }
        .status-inactive {
            color: #666;
        }
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
        .optimization-note {
            background: #2a2a2a;
            border: 2px solid #ffff00;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #ffff00;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 PACKAGING IMAGE DOWNLOAD MONITOR</h1>

        <div class="optimization-note">
            <strong>⚡ STORAGE OPTIMIZED:</strong> Downloading first 3 images per product only
            <br>
            <strong>💾 Savings:</strong> ~6.4 GB vs ~33 GB (81% reduction)
            <br>
            <strong>📈 Images:</strong> 67,371 vs 345,803 (80% reduction)
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-label">Overall Progress</div>
                <div class="stat-value">{{ "%.1f"|format(overall_progress) }}%</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Active Workers</div>
                <div class="stat-value">{{ active_workers }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Completed Workers</div>
                <div class="stat-value">{{ completed_workers }}/{{ total_workers }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Products Processed</div>
                <div class="stat-value">{{ "{:,}".format(total_products_done) }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Images Downloaded</div>
                <div class="stat-value">{{ "{:,}".format(total_images_done) }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Estimated Storage</div>
                <div class="stat-value">{{ "%.2f"|format(estimated_storage_gb) }} GB</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Estimated Time Remaining</div>
                <div class="stat-value">{{ eta }}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Download Rate</div>
                <div class="stat-value">{{ rate }}</div>
            </div>
        </div>

        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ overall_progress }}%">
                {{ "%.1f"|format(overall_progress) }}%
            </div>
        </div>

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
                <div class="worker-stat">Images: {{ "{:,}".format(worker.images_done) }}</div>
                <div class="worker-stat">Failed: {{ worker.images_failed }}</div>
                {% if worker.progress_pct > 0 %}
                <div class="worker-stat">Progress: {{ "%.1f"|format(worker.progress_pct) }}%</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>

        <div class="timestamp">
            Last updated: {{ current_time }}
            <br>
            Page auto-refreshes every 5 seconds
        </div>
    </div>
</body>
</html>
"""

def get_worker_progress():
    """Read all worker progress files"""
    workers = []

    for worker_id in range(TOTAL_WORKERS):
        start_product = worker_id * PRODUCTS_PER_WORKER
        end_product = min((worker_id + 1) * PRODUCTS_PER_WORKER, TOTAL_PRODUCTS)
        total_products = end_product - start_product

        progress_file = IMAGE_OUTPUT_DIR / f'worker_{worker_id:04d}_progress.json'

        worker_data = {
            'id': worker_id,
            'start': start_product,
            'end': end_product,
            'total_products': total_products,
            'products_done': 0,
            'images_done': 0,
            'images_failed': 0,
            'status': 'Inactive',
            'status_class': 'inactive',
            'progress_pct': 0.0
        }

        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    stats = data.get('stats', {})
                    worker_data['products_done'] = stats.get('products_processed', 0)
                    worker_data['images_done'] = stats.get('images_downloaded', 0)
                    worker_data['images_failed'] = stats.get('images_failed', 0)

                    # Calculate progress
                    if total_products > 0:
                        worker_data['progress_pct'] = (worker_data['products_done'] / total_products) * 100

                    # Determine status
                    if worker_data['products_done'] >= total_products:
                        worker_data['status'] = 'Completed'
                        worker_data['status_class'] = 'completed'
                    elif worker_data['products_done'] > 0:
                        worker_data['status'] = 'Running'
                        worker_data['status_class'] = 'active'
                    else:
                        worker_data['status'] = 'Starting'
                        worker_data['status_class'] = 'active'
            except:
                pass

        workers.append(worker_data)

    return workers

def calculate_stats(workers):
    """Calculate overall statistics"""
    total_products_done = sum(w['products_done'] for w in workers)
    total_images_done = sum(w['images_done'] for w in workers)
    active_workers = sum(1 for w in workers if w['status_class'] == 'active')
    completed_workers = sum(1 for w in workers if w['status_class'] == 'completed')

    overall_progress = (total_products_done / TOTAL_PRODUCTS) * 100 if TOTAL_PRODUCTS > 0 else 0
    estimated_storage_gb = (total_images_done * 100) / (1024 * 1024)  # 100KB per image

    # Calculate ETA
    if total_products_done > 0 and overall_progress < 100:
        # Assume current rate continues
        products_remaining = TOTAL_PRODUCTS - total_products_done
        avg_images_per_product = total_images_done / total_products_done if total_products_done > 0 else 3
        images_remaining = products_remaining * avg_images_per_product

        # Estimate: 0.5 seconds per image with active workers
        if active_workers > 0:
            time_remaining_seconds = (images_remaining * 0.5) / active_workers
            hours = int(time_remaining_seconds // 3600)
            minutes = int((time_remaining_seconds % 3600) // 60)
            eta = f"{hours}h {minutes}m"

            # Calculate rate
            images_per_second = (total_images_done / (60 * 30)) if total_products_done > 100 else 0  # Rough estimate
            rate = f"{images_per_second * 60:.1f}/min" if images_per_second > 0 else "Calculating..."
        else:
            eta = "N/A"
            rate = "N/A"
    else:
        eta = "Complete!" if overall_progress >= 100 else "Starting..."
        rate = "N/A"

    return {
        'total_products_done': total_products_done,
        'total_images_done': total_images_done,
        'active_workers': active_workers,
        'completed_workers': completed_workers,
        'overall_progress': overall_progress,
        'estimated_storage_gb': estimated_storage_gb,
        'eta': eta,
        'rate': rate
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

@app.route('/api/stats')
def api_stats():
    """JSON API for programmatic access"""
    workers = get_worker_progress()
    stats = calculate_stats(workers)

    return jsonify({
        'workers': workers,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    })

def main():
    print("=" * 80)
    print("🖼️  PACKAGING IMAGE DOWNLOAD MONITOR")
    print("=" * 80)
    print("")
    print("📊 Dashboard starting on http://localhost:5555")
    print("")
    print("Features:")
    print("  - Real-time worker status")
    print("  - Progress tracking")
    print("  - Storage estimation")
    print("  - ETA calculation")
    print("  - Auto-refresh every 5 seconds")
    print("")
    print("🌐 Open in browser: http://localhost:5555")
    print("")
    print("Press Ctrl+C to stop the monitor")
    print("=" * 80)
    print("")

    # Run Flask app
    app.run(host='0.0.0.0', port=5555, debug=False)

if __name__ == '__main__':
    main()
