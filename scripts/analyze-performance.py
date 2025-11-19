#!/usr/bin/env python3
"""
Performance Analysis Tool
Analyzes benchmark results and generates recommendations
"""

import json
import os
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class PerformanceAnalyzer:
    """Analyzes performance benchmarks and generates insights"""

    # Performance thresholds
    THRESHOLDS = {
        'build_time_seconds': {'good': 60, 'warning': 120, 'critical': 300},
        'test_time_seconds': {'good': 30, 'warning': 60, 'critical': 120},
        'api_health_response_time': {'good': 0.1, 'warning': 0.5, 'critical': 1.0},
        'api_search_response_time': {'good': 0.5, 'warning': 2.0, 'critical': 5.0},
    }

    def __init__(self, reports_dir: str = "reports/performance"):
        self.reports_dir = Path(reports_dir)
        self.reports: List[Dict[str, Any]] = []

    def load_reports(self) -> None:
        """Load all benchmark reports"""
        report_files = sorted(glob.glob(str(self.reports_dir / "benchmark-*.json")))

        for report_file in report_files:
            with open(report_file, 'r') as f:
                self.reports.append(json.load(f))

        print(f"📊 Loaded {len(self.reports)} benchmark reports")

    def get_status(self, metric: str, value: float) -> str:
        """Get status (good/warning/critical) for a metric"""
        if metric not in self.THRESHOLDS:
            return 'unknown'

        thresholds = self.THRESHOLDS[metric]
        if value <= thresholds['good']:
            return 'good'
        elif value <= thresholds['warning']:
            return 'warning'
        else:
            return 'critical'

    def analyze_latest(self) -> Dict[str, Any]:
        """Analyze latest benchmark report"""
        if not self.reports:
            return {'error': 'No reports found'}

        latest = self.reports[-1]
        analysis = {
            'timestamp': latest.get('timestamp'),
            'metrics': {},
            'recommendations': []
        }

        # Analyze each metric
        for metric, value in latest.items():
            if metric in self.THRESHOLDS:
                # Convert string to float if needed
                if isinstance(value, str):
                    try:
                        value = float(value.rstrip('s'))
                    except ValueError:
                        continue

                status = self.get_status(metric, value)
                analysis['metrics'][metric] = {
                    'value': value,
                    'status': status,
                    'threshold_good': self.THRESHOLDS[metric]['good'],
                    'threshold_warning': self.THRESHOLDS[metric]['warning']
                }

                # Generate recommendations
                if status == 'critical':
                    analysis['recommendations'].append(
                        f"CRITICAL: {metric} ({value}) exceeds threshold. Immediate optimization required."
                    )
                elif status == 'warning':
                    analysis['recommendations'].append(
                        f"WARNING: {metric} ({value}) approaching threshold. Consider optimization."
                    )

        return analysis

    def compare_trends(self) -> Dict[str, Any]:
        """Compare trends across reports"""
        if len(self.reports) < 2:
            return {'error': 'Need at least 2 reports for trend analysis'}

        trends = {}
        metrics = ['build_time_seconds', 'test_time_seconds']

        for metric in metrics:
            values = []
            for report in self.reports[-5:]:  # Last 5 reports
                if metric in report:
                    val = report[metric]
                    if isinstance(val, (int, float)):
                        values.append(float(val))

            if len(values) >= 2:
                change = ((values[-1] - values[0]) / values[0]) * 100
                trends[metric] = {
                    'values': values,
                    'change_percent': round(change, 2),
                    'direction': 'improving' if change < 0 else 'degrading'
                }

        return trends

    def generate_report(self) -> str:
        """Generate comprehensive performance report"""
        analysis = self.analyze_latest()
        trends = self.compare_trends()

        report = []
        report.append("=" * 60)
        report.append("PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")

        # Latest metrics
        report.append(f"Timestamp: {analysis.get('timestamp', 'N/A')}")
        report.append("")
        report.append("LATEST METRICS:")
        report.append("-" * 60)

        for metric, data in analysis.get('metrics', {}).items():
            status_emoji = {
                'good': '✅',
                'warning': '⚠️',
                'critical': '❌'
            }.get(data['status'], '❓')

            report.append(
                f"{status_emoji} {metric}: {data['value']} "
                f"(threshold: {data['threshold_good']})"
            )

        # Recommendations
        if analysis.get('recommendations'):
            report.append("")
            report.append("RECOMMENDATIONS:")
            report.append("-" * 60)
            for rec in analysis['recommendations']:
                report.append(f"• {rec}")

        # Trends
        if not trends.get('error'):
            report.append("")
            report.append("TRENDS (Last 5 Reports):")
            report.append("-" * 60)
            for metric, data in trends.items():
                direction_emoji = '📈' if data['direction'] == 'degrading' else '📉'
                report.append(
                    f"{direction_emoji} {metric}: {data['change_percent']}% "
                    f"({data['direction']})"
                )

        # Optimization suggestions
        report.append("")
        report.append("OPTIMIZATION SUGGESTIONS:")
        report.append("-" * 60)
        report.append("• Build Time: Enable Turbo cache, optimize dependencies")
        report.append("• Bundle Size: Implement code splitting, lazy loading")
        report.append("• API Response: Add caching layer, optimize queries")
        report.append("• Database: Add indexes, use query optimization")
        report.append("• Memory: Profile memory leaks, optimize data structures")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def save_analysis(self, output_file: str = None) -> None:
        """Save analysis to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_file = self.reports_dir / f"analysis-{timestamp}.txt"

        report = self.generate_report()

        with open(output_file, 'w') as f:
            f.write(report)

        print(f"💾 Analysis saved to: {output_file}")
        print("")
        print(report)

def main():
    """Main execution"""
    print("🔍 Performance Analysis")
    print("=" * 60)
    print("")

    # Create reports directory if it doesn't exist
    Path("reports/performance").mkdir(parents=True, exist_ok=True)

    # Initialize analyzer
    analyzer = PerformanceAnalyzer()

    # Load and analyze reports
    analyzer.load_reports()

    if not analyzer.reports:
        print("⚠️  No benchmark reports found. Run ./scripts/benchmark.sh first.")
        return

    # Generate and save analysis
    analyzer.save_analysis()

if __name__ == "__main__":
    main()
