#!/usr/bin/env python3
"""
Onehago Dual Orchestration Monitoring Dashboard

Tracks both orchestration systems:
1. Text Extraction Orchestrator (12 workers) - Product details extraction
2. Image Download Orchestrator (10 workers) - Category 2 image downloads

Real-time monitoring at http://localhost:5555
"""
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# Configuration
TEXT_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only')
IMAGE_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/images/category_2')

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Onehago Dual Orchestrator Monitor</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .update-info {
            text-align: center;
            color: rgba(255,255,255,0.9);
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        .stat-row:last-child { border-bottom: none; }
        .stat-label { font-weight: 600; color: #555; }
        .stat-value { color: #333; font-weight: bold; }
        .status-running { color: #28a745; }
        .status-stopped { color: #dc3545; }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        .worker-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
            margin-top: 15px;
        }
        .worker-card {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #dee2e6;
        }
        .worker-card.active {
            background: #d4edda;
            border-color: #28a745;
        }
        .worker-card.inactive {
            background: #f8d7da;
            border-color: #dc3545;
        }
        .metric-highlight {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            text-align: center;
            margin: 15px 0;
        }
        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #28a745;
        }
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Onehago Dual Orchestrator Monitor</h1>
        <div class="update-info">
            Last updated: <span id="lastUpdate">Loading...</span> | Auto-refresh: 15s
        </div>

        <!-- Text Extraction Orchestrator -->
        <div class="card">
            <h2>📝 Text Extraction Orchestrator (12 Workers)</h2>
            <div id="textOrchestrator"></div>
        </div>

        <!-- Image Download Orchestrator -->
        <div class="card">
            <h2>🖼️ Image Download Orchestrator (10 Workers)</h2>
            <div id="imageOrchestrator"></div>
            <div class="worker-grid" id="imageWorkerGrid"></div>
        </div>
    </div>

    <script>
        const REFRESH_INTERVAL = 15000;

        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                    updateTextOrchestrator(data.text_orchestrator);
                    updateImageOrchestrator(data.image_orchestrator);
                })
                .catch(error => console.error('Error:', error));
        }

        function updateTextOrchestrator(data) {
            const div = document.getElementById('textOrchestrator');
            const progress = data.products_crawled || 0;
            const total = data.total_products || 2011553;
            const percentage = ((progress / total) * 100).toFixed(2);
            const activeWorkers = data.active_workers || 0;

            if (data.running) {
                div.innerHTML = `
                    <div class="success-message">
                        <strong>✅ Status:</strong> <span class="status-running">Running</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Active Workers:</span>
                        <span class="stat-value status-running">${activeWorkers} / 12</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Products Crawled:</span>
                        <span class="stat-value">${progress.toLocaleString()} / ${total.toLocaleString()}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${percentage}%">${percentage}%</div>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Avg per Worker:</span>
                        <span class="stat-value">${activeWorkers > 0 ? Math.floor(progress / activeWorkers).toLocaleString() : 0} products</span>
                    </div>
                `;
            } else {
                div.innerHTML = `
                    <div class="error-message">
                        <strong>⚠️ Status:</strong> <span class="status-stopped">Not Running</span>
                    </div>
                    <p style="margin-top: 15px; color: #666;">Text extraction orchestrator is not currently active.</p>
                `;
            }
        }

        function updateImageOrchestrator(data) {
            const div = document.getElementById('imageOrchestrator');
            const gridDiv = document.getElementById('imageWorkerGrid');

            const workers = data.workers || [];
            const activeWorkers = workers.filter(w => w.running).length;
            const totalProducts = workers.reduce((sum, w) => sum + (w.products_processed || 0), 0);
            const totalImages = workers.reduce((sum, w) => sum + (w.images_downloaded || 0), 0);
            const targetProducts = 136062;
            const percentage = ((totalProducts / targetProducts) * 100).toFixed(2);

            if (data.running) {
                div.innerHTML = `
                    <div class="success-message">
                        <strong>✅ Status:</strong> <span class="status-running">Running</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Active Workers:</span>
                        <span class="stat-value status-running">${activeWorkers} / 10</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Products Processed:</span>
                        <span class="stat-value">${totalProducts.toLocaleString()} / ${targetProducts.toLocaleString()}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Images Downloaded:</span>
                        <span class="stat-value">${totalImages.toLocaleString()}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${percentage}%">${percentage}%</div>
                    </div>
                `;

                gridDiv.innerHTML = workers.map(w => `
                    <div class="worker-card ${w.running ? 'active' : 'inactive'}">
                        <div style="font-weight: bold; color: #667eea;">Worker ${w.id}</div>
                        <div style="font-size: 0.85em; margin-top: 5px;">
                            ${w.products_processed || 0} products<br>
                            ${w.images_downloaded || 0} images
                        </div>
                        <div style="font-size: 0.75em; color: ${w.running ? '#28a745' : '#dc3545'}; margin-top: 5px;">
                            ${w.running ? '● Running' : '○ Stopped'}
                        </div>
                    </div>
                `).join('');
            } else {
                div.innerHTML = `
                    <div class="error-message">
                        <strong>⚠️ Status:</strong> <span class="status-stopped">Not Running</span>
                    </div>
                    <p style="margin-top: 15px; color: #666;">Image download orchestrator is not currently active.</p>
                `;
                gridDiv.innerHTML = '';
            }
        }

        updateDashboard();
        setInterval(updateDashboard, REFRESH_INTERVAL);
    </script>
</body>
</html>
"""

def get_text_orchestrator_status() -> Dict:
    """Get text extraction orchestrator status (12 workers)"""
    status = {
        'running': False,
        'products_crawled': 0,
        'total_products': 2011553,
        'active_workers': 0
    }

    # Check if orchestrator is running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'onehago_orchestrator_continuous.py'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            status['running'] = True
    except:
        pass

    # Check worker processes
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'onehago_worker.py'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            worker_pids = result.stdout.strip().split('\n')
            status['active_workers'] = len(worker_pids)
    except:
        pass

    # Count crawled products from output files
    if TEXT_OUTPUT_DIR.exists():
        try:
            total_lines = 0
            for file in TEXT_OUTPUT_DIR.glob('worker_*_output.jsonl'):
                result = subprocess.run(['wc', '-l', str(file)], capture_output=True, text=True)
                if result.returncode == 0:
                    total_lines += int(result.stdout.strip().split()[0])

            for file in TEXT_OUTPUT_DIR.glob('batch_*.jsonl'):
                result = subprocess.run(['wc', '-l', str(file)], capture_output=True, text=True)
                if result.returncode == 0:
                    total_lines += int(result.stdout.strip().split()[0])

            status['products_crawled'] = total_lines
        except:
            pass

    return status

def get_image_orchestrator_status() -> Dict:
    """Get image download orchestrator status (10 workers)"""
    status = {
        'running': False,
        'workers': []
    }

    # Check if orchestrator is running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'onehago_image_orchestrator.py'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            status['running'] = True
    except:
        pass

    # Check each worker (0-9)
    for worker_id in range(10):
        worker_info = {
            'id': worker_id,
            'running': False,
            'products_processed': 0,
            'images_downloaded': 0
        }

        # Check if worker is running
        try:
            result = subprocess.run(
                ['pgrep', '-f', f'onehago_image_worker.py {worker_id}'],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                worker_info['running'] = True
        except:
            pass

        # Load progress file
        progress_file = IMAGE_OUTPUT_DIR / f'worker_{worker_id:04d}_progress.json'
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                    stats = data.get('stats', {})
                    worker_info['products_processed'] = stats.get('products_processed', 0)
                    worker_info['images_downloaded'] = stats.get('images_downloaded', 0)
            except:
                pass

        status['workers'].append(worker_info)

    return status

@app.route('/')
def index():
    """Serve the dashboard HTML"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/status')
def api_status():
    """API endpoint for dashboard data"""
    return jsonify({
        'text_orchestrator': get_text_orchestrator_status(),
        'image_orchestrator': get_image_orchestrator_status(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Onehago Dual Orchestrator Monitoring Dashboard...")
    print("=" * 60)
    print(f"📊 Dashboard URL: http://localhost:5555")
    print(f"🔄 Auto-refresh: Every 15 seconds")
    print(f"📁 Monitoring:")
    print(f"   - Text Orchestrator: {TEXT_OUTPUT_DIR}")
    print(f"   - Image Orchestrator: {IMAGE_OUTPUT_DIR}")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print()

    app.run(host='0.0.0.0', port=5555, debug=False)
