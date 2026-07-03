"""
Chart generation implementation using matplotlib.

Provides static methods for generating various types of charts as base64-encoded
PNG images for embedding in web applications and reports.
"""

import io
import logging
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

plt.style.use("seaborn-v0_8-whitegrid")

COLORS = [
    "#2196F3",
    "#FF9800",
    "#4CAF50",
    "#F44336",
    "#9C27B0",
    "#00BCD4",
    "#FFEB3B",
    "#795548",
    "#607D8B",
    "#E91E63",
]


class ChartGenerator:
    """Generate charts from data.

    All chart generation methods return base64-encoded PNG strings that can
    be embedded directly in HTML or used in API responses.
    """

    @staticmethod
    def bar_chart(
        x: list[Any],
        y: list[Any],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
    ) -> str:
        """Generate a bar chart.

        Args:
            x: List of x-axis values (categories).
            y: List of y-axis values (heights).
            title: Chart title.
            xlabel: X-axis label.
            ylabel: Y-axis label.

        Returns:
            Base64-encoded PNG string of the chart.

        Raises:
            ValueError: If x and y have different lengths.
        """
        logger.debug("Generating bar chart with %d bars", len(x))
        try:
            if len(x) != len(y):
                raise ValueError(
                    f"x and y must have the same length, got {len(x)} and {len(y)}"
                )

            fig, ax = plt.subplots(figsize=(10, 6))

            colors = [COLORS[i % len(COLORS)] for i in range(len(x))]
            bars = ax.bar(range(len(x)), y, color=colors, edgecolor="white", linewidth=0.5)

            ax.set_xticks(range(len(x)))
            ax.set_xticklabels([str(v) for v in x], rotation=45, ha="right")
            ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)

            for bar, val in zip(bars, y):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(y) * 0.01,
                    str(val),
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            plt.tight_layout()
            result = ChartGenerator._fig_to_base64(fig)
            plt.close(fig)

            logger.debug("Bar chart generated successfully")
            return result
        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to generate bar chart: %s", str(e))
            plt.close("all")
            raise

    @staticmethod
    def line_chart(
        x: list[Any],
        y: list[Any],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
    ) -> str:
        """Generate a line chart.

        Args:
            x: List of x-axis values.
            y: List of y-axis values.
            title: Chart title.
            xlabel: X-axis label.
            ylabel: Y-axis label.

        Returns:
            Base64-encoded PNG string of the chart.

        Raises:
            ValueError: If x and y have different lengths.
        """
        logger.debug("Generating line chart with %d points", len(x))
        try:
            if len(x) != len(y):
                raise ValueError(
                    f"x and y must have the same length, got {len(x)} and {len(y)}"
                )

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.plot(
                range(len(x)),
                y,
                color=COLORS[0],
                linewidth=2,
                marker="o",
                markersize=4,
                markerfacecolor="white",
                markeredgecolor=COLORS[0],
                markeredgewidth=2,
            )

            ax.set_xticks(range(len(x)))
            ax.set_xticklabels([str(v) for v in x], rotation=45, ha="right")
            ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            plt.tight_layout()
            result = ChartGenerator._fig_to_base64(fig)
            plt.close(fig)

            logger.debug("Line chart generated successfully")
            return result
        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to generate line chart: %s", str(e))
            plt.close("all")
            raise

    @staticmethod
    def pie_chart(
        labels: list[str],
        values: list[Any],
        title: str = "",
    ) -> str:
        """Generate a pie chart.

        Args:
            labels: List of label strings for each slice.
            values: List of numeric values for each slice.
            title: Chart title.

        Returns:
            Base64-encoded PNG string of the chart.

        Raises:
            ValueError: If labels and values have different lengths or are empty.
        """
        logger.debug("Generating pie chart with %d slices", len(labels))
        try:
            if len(labels) != len(values):
                raise ValueError(
                    f"labels and values must have the same length, got {len(labels)} and {len(values)}"
                )
            if not labels:
                raise ValueError("labels and values cannot be empty")

            fig, ax = plt.subplots(figsize=(10, 8))

            colors = [COLORS[i % len(COLORS)] for i in range(len(labels))]
            wedges, texts, autotexts = ax.pie(
                values,
                labels=None,
                colors=colors,
                autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct/100.*sum(values)))})",
                startangle=90,
                pctdistance=0.85,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5},
            )

            for autotext in autotexts:
                autotext.set_fontsize(9)

            ax.legend(
                wedges,
                [str(l) for l in labels],
                title="Categories",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1),
                fontsize=10,
            )

            ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

            plt.tight_layout()
            result = ChartGenerator._fig_to_base64(fig)
            plt.close(fig)

            logger.debug("Pie chart generated successfully")
            return result
        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to generate pie chart: %s", str(e))
            plt.close("all")
            raise

    @staticmethod
    def scatter_plot(
        x: list[Any],
        y: list[Any],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
    ) -> str:
        """Generate a scatter plot.

        Args:
            x: List of x-axis values.
            y: List of y-axis values.
            title: Chart title.
            xlabel: X-axis label.
            ylabel: Y-axis label.

        Returns:
            Base64-encoded PNG string of the chart.

        Raises:
            ValueError: If x and y have different lengths.
        """
        logger.debug("Generating scatter plot with %d points", len(x))
        try:
            if len(x) != len(y):
                raise ValueError(
                    f"x and y must have the same length, got {len(x)} and {len(y)}"
                )

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.scatter(
                range(len(x)),
                y,
                color=COLORS[0],
                alpha=0.7,
                edgecolors="white",
                linewidth=0.5,
                s=60,
            )

            z = np.polyfit(range(len(x)), y, 1)
            p = np.poly1d(z)
            ax.plot(range(len(x)), p(range(len(x))), "--", color=COLORS[1], alpha=0.8)

            ax.set_xticks(range(len(x)))
            ax.set_xticklabels([str(v) for v in x], rotation=45, ha="right")
            ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            plt.tight_layout()
            result = ChartGenerator._fig_to_base64(fig)
            plt.close(fig)

            logger.debug("Scatter plot generated successfully")
            return result
        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to generate scatter plot: %s", str(e))
            plt.close("all")
            raise

    @staticmethod
    def histogram(
        data: list[Any],
        bins: int = 30,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
    ) -> str:
        """Generate a histogram.

        Args:
            data: List of numeric values.
            bins: Number of bins for the histogram.
            title: Chart title.
            xlabel: X-axis label.
            ylabel: Y-axis label.

        Returns:
            Base64-encoded PNG string of the chart.

        Raises:
            ValueError: If data is empty.
        """
        logger.debug("Generating histogram with %d data points", len(data))
        try:
            if not data:
                raise ValueError("data cannot be empty")

            fig, ax = plt.subplots(figsize=(10, 6))

            n, bin_edges, patches = ax.hist(
                data,
                bins=bins,
                color=COLORS[0],
                edgecolor="white",
                linewidth=0.5,
                alpha=0.8,
            )

            for patch in patches:
                patch.set_facecolor(COLORS[0])
                patch.set_alpha(0.8)

            mean_val = np.mean(data)
            std_val = np.std(data)
            ax.axvline(
                mean_val,
                color=COLORS[1],
                linestyle="--",
                linewidth=2,
                label=f"Mean: {mean_val:.2f}",
            )
            ax.axvline(
                mean_val + std_val,
                color=COLORS[3],
                linestyle=":",
                linewidth=1.5,
                label=f"±1 Std: {std_val:.2f}",
            )
            ax.axvline(
                mean_val - std_val,
                color=COLORS[3],
                linestyle=":",
                linewidth=1.5,
            )

            ax.legend(fontsize=10)
            ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
            ax.set_xlabel(xlabel or "Value", fontsize=12)
            ax.set_ylabel(ylabel or "Frequency", fontsize=12)

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            plt.tight_layout()
            result = ChartGenerator._fig_to_base64(fig)
            plt.close(fig)

            logger.debug("Histogram generated successfully")
            return result
        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to generate histogram: %s", str(e))
            plt.close("all")
            raise

    @staticmethod
    def heatmap(
        data: dict[str, dict[str, float]],
        title: str = "",
    ) -> str:
        """Generate a heatmap from a correlation or similarity matrix.

        Args:
            data: Dictionary of dictionaries representing the matrix.
                  Outer keys are row labels, inner keys are column labels.
            title: Chart title.

        Returns:
            Base64-encoded PNG string of the chart.

        Raises:
            ValueError: If data is empty or has inconsistent dimensions.
        """
        logger.debug("Generating heatmap")
        try:
            if not data:
                raise ValueError("data cannot be empty")

            row_labels = list(data.keys())
            col_labels = list(next(iter(data.values())).keys())

            matrix = np.array(
                [[data[row][col] for col in col_labels] for row in row_labels]
            )

            fig, ax = plt.subplots(
                figsize=(max(8, len(col_labels) * 1.2), max(6, len(row_labels) * 0.8))
            )

            im = ax.imshow(matrix, cmap="RdBu_r", aspect="auto", vmin=-1, vmax=1)

            ax.set_xticks(range(len(col_labels)))
            ax.set_yticks(range(len(row_labels)))
            ax.set_xticklabels(col_labels, rotation=45, ha="right")
            ax.set_yticklabels(row_labels)

            for i in range(len(row_labels)):
                for j in range(len(col_labels)):
                    color = "white" if abs(matrix[i, j]) > 0.5 else "black"
                    ax.text(
                        j,
                        i,
                        f"{matrix[i, j]:.2f}",
                        ha="center",
                        va="center",
                        color=color,
                        fontsize=8,
                    )

            ax.set_title(title, fontsize=14, fontweight="bold", pad=15)

            plt.colorbar(im, ax=ax, shrink=0.8, label="Correlation")

            plt.tight_layout()
            result = ChartGenerator._fig_to_base64(fig)
            plt.close(fig)

            logger.debug("Heatmap generated successfully")
            return result
        except ValueError:
            raise
        except Exception as e:
            logger.error("Failed to generate heatmap: %s", str(e))
            plt.close("all")
            raise

    @staticmethod
    def _fig_to_base64(fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64 string.

        Args:
            fig: The matplotlib figure to convert.

        Returns:
            Base64-encoded PNG string.
        """
        import base64

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        buffer.close()
        return image_base64
