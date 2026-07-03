"""
Analytics module for data analysis and visualization.

Provides exploratory data analysis, chart generation, and report generation
capabilities for the AI Research Copilot platform.
"""

from app.analytics.eda.exploratory import ExplorerAnalysis
from app.analytics.charts.chart_generator import ChartGenerator
from app.analytics.reports.report_generator import ReportGenerator

__all__ = ["ExplorerAnalysis", "ChartGenerator", "ReportGenerator"]
