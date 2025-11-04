#!/usr/bin/env python3
"""
Onehago Dual Orchestration Monitoring Dashboard Server

Provides comprehensive real-time monitoring of:
- Text Extraction Orchestrator (12 workers, product details)
- Image Download Orchestrator (10 workers, category 2 images)
- Batch validation process (validation & repair stats)

Single-page dashboard with auto-refresh capability.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import subprocess
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# Configuration
PHASE2_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/crawled/production/products_text_only')
IMAGE_OUTPUT_DIR = Path('/Users/oypnus/Project/rag-enterprise/data/onehago/images/category_2')
VALIDATION_PROGRESS_FILE = Path('/tmp/onehago_batch_validation_progress.json')
VALIDATION_LOG_FILE = Path('/tmp/onehago_batch_validation.log')

# HTML Template for Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Onehago Pipeline Monitor</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

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

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            font-size: 1.5em;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 12px;
            border-bottom: 1px solid #eee;
            transition: background 0.2s;
        }

        .stat-row:hover {
            background: #f8f9fa;
        }

        .stat-row:last-child {
            border-bottom: none;
        }

        .stat-label {
            font-weight: 600;
            color: #555;
        }

        .stat-value {
            color: #333;
            font-weight: bold;
        }

        .status-running {
            color: #28a745;
        }

        .status-stopped {
            color: #dc3545;
        }

        .status-pending {
            color: #ffc107;
        }

        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
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
            font-size: 0.9em;
        }

        .worker-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 15px;
        }

        .worker-card {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #dee2e6;
            transition: all 0.3s;
        }

        .worker-card.active {
            background: #d4edda;
            border-color: #28a745;
        }

        .worker-card.inactive {
            background: #f8d7da;
            border-color: #dc3545;
        }

        .worker-id {
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }

        .worker-progress {
            font-size: 0.85em;
            color: #666;
            margin-top: 5px;
        }

        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #dc3545;
        }

        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #28a745;
        }

        .log-preview {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 15px;
        }

        .log-preview::-webkit-scrollbar {
            width: 8px;
        }

        .log-preview::-webkit-scrollbar-track {
            background: #2d2d2d;
        }

        .log-preview::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 4px;
        }

        .metric-highlight {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            text-align: center;
            margin: 15px 0;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .loading {
            animation: pulse 1.5s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Onehago Pipeline Monitor</h1>
        <div class="update-info">
            Last updated: <span id="lastUpdate">Loading...</span> |
            Auto-refresh: <span id="autoRefresh">15s</span>
        </div>

        <!-- Validation Section -->
        <div class="grid">
            <div class="card">
                <h2>📊 Batch Validation Status</h2>
                <div id="validationStatus"></div>
            </div>

            <div class="card">
                <h2>📈 Validation Statistics</h2>
                <div id="validationStats"></div>
            </div>
        </div>

        <!-- Text Extraction Orchestrator Section -->
        <div class="card">
            <h2>📝 Text Extraction Orchestrator (12 Workers)</h2>
            <div id="textOrchestratorStatus"></div>
        </div>

        <!-- Image Download Orchestrator Section -->
        <div class="card">
            <h2>🖼️ Image Download Orchestrator (10 Workers)</h2>
            <div id="imageOrchestratorOverview"></div>
            <div class="worker-grid" id="imageWorkerGrid"></div>
        </div>

        <!-- Recent Activity Log -->
        <div class="card">
            <h2>📝 Recent Activity</h2>
            <div class="log-preview" id="recentActivity"></div>
        </div>
    </div>

    <script>
        // Auto-refresh every 15 seconds
        const REFRESH_INTERVAL = 15000;

        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateLastUpdateTime();
                    updateValidationStatus(data.validation);
                    updateTextOrchestrator(data.text_orchestrator);
                    updateImageOrchestrator(data.image_orchestrator);
                    updateRecentActivity(data.recent_logs);
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                });
        }

        function updateLastUpdateTime() {
            const now = new Date();
            document.getElementById('lastUpdate').textContent = now.toLocaleTimeString();
        }

        function updateValidationStatus(validation) {
            const statusDiv = document.getElementById('validationStatus');
            const statsDiv = document.getElementById('validationStats');

            if (validation.running) {
                statusDiv.innerHTML = `
                    <div class="success-message">
                        <strong>✅ Status:</strong> <span class="status-running">Running</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Process ID:</span>
                        <span class="stat-value">${validation.pid || 'N/A'}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Files Processed:</span>
                        <span class="stat-value">${validation.files_processed || 0}</span>
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="error-message">
                        <strong>⚠️ Status:</strong> <span class="status-stopped">Not Running</span>
                    </div>
                `;
            }

            // Statistics
            const stats = validation.stats || {};
            const total = stats.total_products || 0;
            const passed = stats.passed || 0;
            const failed = stats.failed || 0;
            const repaired = stats.repaired || 0;

            const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;
            const repairRate = failed > 0 ? ((repaired / failed) * 100).toFixed(1) : 0;

            statsDiv.innerHTML = `
                <div class="metric-highlight">${total.toLocaleString()}</div>
                <div style="text-align: center; color: #666; margin-bottom: 20px;">Total Products Processed</div>

                <div class="stat-row">
                    <span class="stat-label">✅ Passed:</span>
                    <span class="stat-value status-running">${passed.toLocaleString()} (${passRate}%)</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${passRate}%">${passRate}%</div>
                </div>

                <div class="stat-row">
                    <span class="stat-label">❌ Failed:</span>
                    <span class="stat-value status-stopped">${failed.toLocaleString()}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">🔧 Repaired:</span>
                    <span class="stat-value status-running">${repaired.toLocaleString()} (${repairRate}%)</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">⚠️ Repair Failed:</span>
                    <span class="stat-value">${stats.repair_failed || 0}</span>
                </div>
            `;
        }

        function updateImageWorkers(workers) {
            const overviewDiv = document.getElementById('imageWorkersOverview');
            const gridDiv = document.getElementById('workerGrid');

            const totalWorkers = workers.length;
            const activeWorkers = workers.filter(w => w.running).length;
            const totalDownloaded = workers.reduce((sum, w) => sum + (w.images_downloaded || 0), 0);
            const totalProducts = workers.reduce((sum, w) => sum + (w.products_processed || 0), 0);

            overviewDiv.innerHTML = `
                <div class="stat-row">
                    <span class="stat-label">Active Workers:</span>
                    <span class="stat-value status-running">${activeWorkers} / ${totalWorkers}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Products Processed:</span>
                    <span class="stat-value">${totalProducts.toLocaleString()}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Images Downloaded:</span>
                    <span class="stat-value">${totalDownloaded.toLocaleString()}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Target Products:</span>
                    <span class="stat-value">133,340 (Category 2)</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(totalProducts / 133340 * 100).toFixed(1)}%">
                        ${(totalProducts / 133340 * 100).toFixed(1)}%
                    </div>
                </div>
            `;

            // Worker grid
            gridDiv.innerHTML = workers.map(worker => `
                <div class="worker-card ${worker.running ? 'active' : 'inactive'}">
                    <div class="worker-id">Worker ${worker.id}</div>
                    <div class="worker-progress">
                        ${worker.products_processed || 0} products<br>
                        ${worker.images_downloaded || 0} images
                    </div>
                    <div style="font-size: 0.75em; color: ${worker.running ? '#28a745' : '#dc3545'}; margin-top: 5px;">
                        ${worker.running ? '● Running' : '○ Stopped'}
                    </div>
                </div>
            `).join('');
        }

        function updatePhase2Status(phase2) {
            const statusDiv = document.getElementById('phase2Status');

            if (phase2.running) {
                const progress = phase2.products_crawled || 0;
                const total = phase2.total_products || 2011553;
                const percentage = ((progress / total) * 100).toFixed(2);
                const activeWorkers = phase2.active_workers || 0;
                const totalWorkers = phase2.workers || 10;

                statusDiv.innerHTML = `
                    <div class="success-message">
                        <strong>✅ Status:</strong> <span class="status-running">Running</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Active Workers:</span>
                        <span class="stat-value status-running">${activeWorkers} / ${totalWorkers}</span>
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
                statusDiv.innerHTML = `
                    <div class="error-message">
                        <strong>⚠️ Status:</strong> <span class="status-stopped">Not Running</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Expected Workers:</span>
                        <span class="stat-value">10</span>
                    </div>
                    <p style="margin-top: 15px; color: #666;">Phase 2 crawling workers are not currently active.</p>
                `;
            }
        }

        function updateRecentActivity(logs) {
            const logDiv = document.getElementById('recentActivity');

            if (logs && logs.length > 0) {
                logDiv.innerHTML = logs.map(log =>
                    `<div>${escapeHtml(log)}</div>`
                ).join('');
                logDiv.scrollTop = logDiv.scrollHeight;
            } else {
                logDiv.innerHTML = '<div>No recent activity logs available.</div>';
            }
        }

        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }

        // Initial load
        updateDashboard();

        // Auto-refresh
        setInterval(updateDashboard, REFRESH_INTERVAL);
    </script>
</body>
</html>
"""

def get_validation_status() -> Dict:
    """Get batch validation status and statistics"""
    status = {
        'running': False,
        'pid': None,
        'files_processed': 0,
        'stats': {}
    }

    # Check if validation process is running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'onehago_batch_validator.py'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            status['running'] = True
            status['pid'] = result.stdout.strip().split('\n')[0]
    except:
        pass

    # Load progress file
    if VALIDATION_PROGRESS_FILE.exists():
        try:
            with open(VALIDATION_PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                status['files_processed'] = len(data.get('processed_files', []))
                status['stats'] = data.get('stats', {})
        except:
            pass

    return status

def get_image_workers_status() -> List[Dict]:
    """Get status of all 10 image workers (orchestrated)"""
    workers = []

    for worker_id in range(10):
        worker_info = {
            'id': worker_id,
            'running': False,
            'products_processed': 0,
            'images_downloaded': 0,
            'images_failed': 0
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
                    worker_info['images_failed'] = stats.get('images_failed', 0)
            except:
                pass

        workers.append(worker_info)

    return workers

def get_phase2_status() -> Dict:
    """Get Phase 2 crawling status (10 workers)"""
    status = {
        'running': False,
        'products_crawled': 0,
        'total_products': 2011553,
        'workers': 0,
        'active_workers': 0
    }

    # Check how many worker processes are running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'phase2.*worker'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            worker_pids = result.stdout.strip().split('\n')
            status['active_workers'] = len(worker_pids)
            status['running'] = True
    except:
        pass

    # Expected worker count
    status['workers'] = 10

    # Count crawled products
    if PHASE2_OUTPUT_DIR.exists():
        try:
            total_lines = 0
            for file in PHASE2_OUTPUT_DIR.glob('worker_*_output.jsonl'):
                result = subprocess.run(['wc', '-l', str(file)], capture_output=True, text=True)
                if result.returncode == 0:
                    total_lines += int(result.stdout.strip().split()[0])

            for file in PHASE2_OUTPUT_DIR.glob('batch_*.jsonl'):
                result = subprocess.run(['wc', '-l', str(file)], capture_output=True, text=True)
                if result.returncode == 0:
                    total_lines += int(result.stdout.strip().split()[0])

            status['products_crawled'] = total_lines
        except:
            pass

    return status

def get_recent_logs() -> List[str]:
    """Get recent activity logs"""
    logs = []

    # Get last 20 lines from validation log
    if VALIDATION_LOG_FILE.exists():
        try:
            result = subprocess.run(
                ['tail', '-20', str(VALIDATION_LOG_FILE)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logs = result.stdout.strip().split('\n')
        except:
            pass

    return logs

@app.route('/')
def index():
    """Serve the dashboard HTML"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/status')
def api_status():
    """API endpoint for dashboard data"""
    return jsonify({
        'validation': get_validation_status(),
        'image_workers': get_image_workers_status(),
        'phase2': get_phase2_status(),
        'recent_logs': get_recent_logs(),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Onehago Monitoring Dashboard Server...")
    print("=" * 60)
    print(f"📊 Dashboard URL: http://localhost:5555")
    print(f"🔄 Auto-refresh: Every 15 seconds")
    print(f"📁 Data sources:")
    print(f"   - Validation: {VALIDATION_PROGRESS_FILE}")
    print(f"   - Images: {IMAGE_OUTPUT_DIR}")
    print(f"   - Phase 2: {PHASE2_OUTPUT_DIR}")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print()

    # Run server
    app.run(host='0.0.0.0', port=5555, debug=False)
