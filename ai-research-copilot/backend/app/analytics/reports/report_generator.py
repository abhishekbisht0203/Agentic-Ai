"""
Report generation implementation for analytics.

Provides report generation capabilities for usage analytics, performance analytics,
and data analysis reports from various data sources.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import UserActivity, AnalyticsReport, Visualization
from app.models.conversation import Conversation, Message
from app.models.document import Document
from app.models.workflow import Workflow, WorkflowExecution

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate analytics reports from data sources.

    Provides methods for generating usage reports, performance reports,
    and custom data analysis reports from database records.
    """

    async def generate_usage_report(
        self, user_id: uuid.UUID, db: AsyncSession
    ) -> dict[str, Any]:
        """Generate usage analytics report.

        Analyzes user activity patterns including conversation counts,
        document usage, workflow executions, and activity distribution.

        Args:
            user_id: The UUID of the user to generate the report for.
            db: Async database session for querying data.

        Returns:
            A dictionary containing:
                - user_id: The user's UUID string
                - report_type: "usage"
                - generated_at: ISO timestamp of report generation
                - conversations: Conversation usage statistics
                - documents: Document usage statistics
                - workflows: Workflow usage statistics
                - activities: Activity breakdown by type
                - summary: Overall usage summary metrics
        """
        logger.info("Generating usage report for user %s", user_id)
        try:
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)
            seven_days_ago = now - timedelta(days=7)

            conv_query = select(Conversation).where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.is_deleted == False,
                )
            )
            conv_result = await db.execute(conv_query)
            conversations = conv_result.scalars().all()

            total_conversations = len(conversations)
            active_conversations = sum(
                1 for c in conversations if c.status == "active"
            )

            total_messages = sum(c.message_count for c in conversations)
            total_tokens = sum(
                (c.token_usage or {}).get("total_tokens", 0)
                for c in conversations
            )

            recent_conversations = sum(
                1
                for c in conversations
                if c.created_at and c.created_at >= seven_days_ago
            )

            doc_query = select(Document).where(
                and_(
                    Document.user_id == user_id,
                    Document.is_deleted == False,
                )
            )
            doc_result = await db.execute(doc_query)
            documents = doc_result.scalars().all()

            total_documents = len(documents)
            processed_documents = sum(
                1 for d in documents if d.status == "completed"
            )
            total_file_size = sum(d.file_size for d in documents)
            total_chunks = sum(d.chunk_count for d in documents)

            recent_documents = sum(
                1
                for d in documents
                if d.created_at and d.created_at >= seven_days_ago
            )

            workflow_query = select(Workflow).where(
                and_(
                    Workflow.user_id == user_id,
                    Workflow.is_deleted == False,
                )
            )
            workflow_result = await db.execute(workflow_query)
            workflows = workflow_result.scalars().all()

            total_workflows = len(workflows)
            total_executions = sum(w.execution_count for w in workflows)

            execution_query = select(WorkflowExecution).where(
                and_(
                    WorkflowExecution.user_id == user_id,
                    WorkflowExecution.is_deleted == False,
                )
            )
            execution_result = await db.execute(execution_query)
            executions = execution_result.scalars().all()

            completed_executions = sum(
                1 for e in executions if e.status == "completed"
            )
            failed_executions = sum(
                1 for e in executions if e.status == "failed"
            )

            activity_query = select(
                UserActivity.activity_type,
                func.count(UserActivity.id),
            ).where(
                and_(
                    UserActivity.user_id == user_id,
                    UserActivity.created_at >= thirty_days_ago,
                    UserActivity.is_deleted == False,
                )
            ).group_by(UserActivity.activity_type)

            activity_result = await db.execute(activity_query)
            activity_breakdown = dict(activity_result.all())

            report = {
                "user_id": str(user_id),
                "report_type": "usage",
                "generated_at": now.isoformat(),
                "conversations": {
                    "total": total_conversations,
                    "active": active_conversations,
                    "total_messages": total_messages,
                    "total_tokens_used": total_tokens,
                    "recent_7_days": recent_conversations,
                    "avg_messages_per_conversation": round(
                        total_messages / total_conversations, 2
                    )
                    if total_conversations > 0
                    else 0.0,
                },
                "documents": {
                    "total": total_documents,
                    "processed": processed_documents,
                    "total_file_size_bytes": total_file_size,
                    "total_chunks": total_chunks,
                    "recent_7_days": recent_documents,
                },
                "workflows": {
                    "total": total_workflows,
                    "total_executions": total_executions,
                    "completed_executions": completed_executions,
                    "failed_executions": failed_executions,
                    "success_rate": round(
                        (completed_executions / total_executions) * 100, 2
                    )
                    if total_executions > 0
                    else 0.0,
                },
                "activities": {
                    "breakdown": activity_breakdown,
                    "total_30_days": sum(activity_breakdown.values()),
                },
                "summary": {
                    "total_conversations": total_conversations,
                    "total_documents": total_documents,
                    "total_workflows": total_workflows,
                    "total_executions": total_executions,
                    "total_tokens_used": total_tokens,
                    "activity_count_30_days": sum(activity_breakdown.values()),
                },
            }

            logger.info("Usage report generated for user %s", user_id)
            return report
        except Exception as e:
            logger.error(
                "Failed to generate usage report for user %s: %s",
                user_id,
                str(e),
            )
            raise

    async def generate_performance_report(
        self, user_id: uuid.UUID, db: AsyncSession
    ) -> dict[str, Any]:
        """Generate performance analytics report.

        Analyzes system performance metrics including workflow execution times,
        document processing times, and error rates.

        Args:
            user_id: The UUID of the user to generate the report for.
            db: Async database session for querying data.

        Returns:
            A dictionary containing:
                - user_id: The user's UUID string
                - report_type: "performance"
                - generated_at: ISO timestamp of report generation
                - workflow_performance: Workflow execution performance metrics
                - document_processing: Document processing performance metrics
                - error_analysis: Error rate and failure analysis
                - trends: Performance trends over time
                - recommendations: Performance improvement recommendations
        """
        logger.info("Generating performance report for user %s", user_id)
        try:
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)

            execution_query = select(WorkflowExecution).where(
                and_(
                    WorkflowExecution.user_id == user_id,
                    WorkflowExecution.created_at >= thirty_days_ago,
                    WorkflowExecution.is_deleted == False,
                )
            )
            execution_result = await db.execute(execution_query)
            executions = execution_result.scalars().all()

            completed_executions = [
                e for e in executions if e.status == "completed" and e.duration_ms
            ]
            failed_executions = [e for e in executions if e.status == "failed"]

            avg_duration = 0.0
            max_duration = 0
            min_duration = 0
            if completed_executions:
                durations = [e.duration_ms for e in completed_executions]
                avg_duration = round(sum(durations) / len(durations), 2)
                max_duration = max(durations)
                min_duration = min(durations)

            execution_success_rate = round(
                (len(completed_executions) / len(executions)) * 100, 2
            ) if executions else 0.0

            error_messages = [e.error_message for e in failed_executions if e.error_message]
            error_categories: dict[str, int] = {}
            for msg in error_messages:
                category = msg[:50] if msg else "Unknown"
                error_categories[category] = error_categories.get(category, 0) + 1

            doc_query = select(Document).where(
                and_(
                    Document.user_id == user_id,
                    Document.created_at >= thirty_days_ago,
                    Document.is_deleted == False,
                )
            )
            doc_result = await db.execute(doc_query)
            documents = doc_result.all()

            total_docs = len(documents)
            failed_docs = sum(1 for d in documents if d.status == "failed")
            processing_errors = [
                d.processing_error for d in documents if d.processing_error
            ]

            hourly_distributions: dict[int, int] = {}
            for e in executions:
                if e.created_at:
                    hour = e.created_at.hour
                    hourly_distributions[hour] = hourly_distributions.get(hour, 0) + 1

            recommendations = []
            if execution_success_rate < 90:
                recommendations.append(
                    "Consider investigating workflow failures - success rate is below 90%"
                )
            if avg_duration > 60000:
                recommendations.append(
                    "Workflow execution times are high - consider optimizing step logic"
                )
            if failed_docs > total_docs * 0.1:
                recommendations.append(
                    "Document processing failure rate is above 10% - check file formats"
                )
            if not recommendations:
                recommendations.append("System performance is within normal parameters")

            report = {
                "user_id": str(user_id),
                "report_type": "performance",
                "generated_at": now.isoformat(),
                "workflow_performance": {
                    "total_executions_30_days": len(executions),
                    "completed_executions": len(completed_executions),
                    "failed_executions": len(failed_executions),
                    "success_rate": execution_success_rate,
                    "avg_duration_ms": avg_duration,
                    "max_duration_ms": max_duration,
                    "min_duration_ms": min_duration,
                },
                "document_processing": {
                    "total_documents": total_docs,
                    "failed_documents": failed_docs,
                    "success_rate": round(
                        ((total_docs - failed_docs) / total_docs) * 100, 2
                    )
                    if total_docs > 0
                    else 100.0,
                    "processing_errors": processing_errors[:10],
                },
                "error_analysis": {
                    "total_errors": len(failed_executions),
                    "error_categories": error_categories,
                    "most_common_error": (
                        max(error_categories, key=error_categories.get)
                        if error_categories
                        else None
                    ),
                },
                "trends": {
                    "hourly_distribution": hourly_distributions,
                },
                "recommendations": recommendations,
            }

            logger.info("Performance report generated for user %s", user_id)
            return report
        except Exception as e:
            logger.error(
                "Failed to generate performance report for user %s: %s",
                user_id,
                str(e),
            )
            raise

    def generate_data_report(
        self, data: dict[str, Any], report_type: str
    ) -> dict[str, Any]:
        """Generate report from data.

        Creates a structured report from raw data, supporting various
        report types including EDA, statistics, and custom analysis.

        Args:
            data: Raw data dictionary to generate the report from.
            report_type: Type of report to generate (e.g., "eda", "statistics",
                        "summary").

        Returns:
            A dictionary containing:
                - report_type: The type of report generated
                - generated_at: ISO timestamp of report generation
                - summary: Overall data summary
                - insights: Key findings and insights
                - data_quality: Data quality assessment
                - visualizations: Recommended visualizations
        """
        logger.info("Generating %s data report", report_type)
        try:
            now = datetime.now(timezone.utc)

            record_count = data.get("record_count", 0)
            column_count = data.get("column_count", 0)
            missing_percentage = data.get("missing_percentage", 0.0)
            numeric_columns = data.get("numeric_columns", [])
            categorical_columns = data.get("categorical_columns", [])
            correlations = data.get("correlations", {})
            distributions = data.get("distributions", {})

            insights: list[str] = []
            if record_count > 0:
                insights.append(f"Dataset contains {record_count} records across {column_count} columns")

            if missing_percentage > 0:
                insights.append(
                    f"Data has {missing_percentage:.1f}% missing values"
                )

            if numeric_columns:
                insights.append(
                    f"Found {len(numeric_columns)} numeric columns: {', '.join(numeric_columns[:5])}"
                )

            if categorical_columns:
                insights.append(
                    f"Found {len(categorical_columns)} categorical columns: {', '.join(categorical_columns[:5])}"
                )

            if correlations.get("highly_correlated_pairs"):
                pairs = correlations["highly_correlated_pairs"]
                insights.append(
                    f"Found {len(pairs)} highly correlated column pairs"
                )

            data_quality_score = 100.0
            if missing_percentage > 0:
                data_quality_score -= missing_percentage * 0.5
            data_quality_score = max(0.0, data_quality_score)

            quality_assessment = "excellent"
            if data_quality_score < 50:
                quality_assessment = "poor"
            elif data_quality_score < 70:
                quality_assessment = "fair"
            elif data_quality_score < 90:
                quality_assessment = "good"

            visualization_recommendations: list[dict[str, str]] = []
            if numeric_columns:
                visualization_recommendations.append({
                    "type": "histogram",
                    "description": f"Distribution of {numeric_columns[0]}",
                    "column": numeric_columns[0],
                })
                if len(numeric_columns) >= 2:
                    visualization_recommendations.append({
                        "type": "scatter",
                        "description": f"{numeric_columns[0]} vs {numeric_columns[1]}",
                        "x_column": numeric_columns[0],
                        "y_column": numeric_columns[1],
                    })

            if categorical_columns:
                visualization_recommendations.append({
                    "type": "bar",
                    "description": f"Value counts of {categorical_columns[0]}",
                    "column": categorical_columns[0],
                })

            if correlations.get("correlation_matrix"):
                visualization_recommendations.append({
                    "type": "heatmap",
                    "description": "Correlation matrix heatmap",
                })

            report = {
                "report_type": report_type,
                "generated_at": now.isoformat(),
                "summary": {
                    "record_count": record_count,
                    "column_count": column_count,
                    "numeric_columns": len(numeric_columns),
                    "categorical_columns": len(categorical_columns),
                    "missing_percentage": round(missing_percentage, 2),
                },
                "insights": insights,
                "data_quality": {
                    "score": round(data_quality_score, 2),
                    "assessment": quality_assessment,
                    "missing_percentage": round(missing_percentage, 2),
                },
                "visualizations": visualization_recommendations,
            }

            logger.info("Data report generated: %s", report_type)
            return report
        except Exception as e:
            logger.error("Failed to generate data report: %s", str(e))
            raise
