"""
Exploratory Data Analysis (EDA) implementation.

Provides comprehensive data analysis capabilities including summary statistics,
data type analysis, correlation analysis, distribution analysis, outlier detection,
and missing data analysis.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class ExplorerAnalysis:
    """Perform exploratory data analysis on datasets.

    This class provides a comprehensive set of tools for analyzing datasets,
    including statistical summaries, data type analysis, correlation analysis,
    distribution analysis, outlier detection, and missing data analysis.

    Attributes:
        data: The pandas DataFrame to analyze.
    """

    def __init__(self, data: pd.DataFrame) -> None:
        """Initialize ExplorerAnalysis with a DataFrame.

        Args:
            data: The pandas DataFrame to analyze.

        Raises:
            ValueError: If the input is not a pandas DataFrame.
            TypeError: If the input is None.
        """
        if data is None:
            raise TypeError("Data cannot be None")
        if not isinstance(data, pd.DataFrame):
            raise ValueError(f"Expected pandas DataFrame, got {type(data).__name__}")
        self.data = data
        logger.info(
            "ExplorerAnalysis initialized with DataFrame of shape %s",
            data.shape,
        )

    def summary_statistics(self) -> dict[str, Any]:
        """Generate summary statistics for the dataset.

        Returns:
            A dictionary containing:
                - shape: Tuple of (rows, columns)
                - column_count: Total number of columns
                - row_count: Total number of rows
                - numeric_stats: Summary statistics for numeric columns
                - categorical_stats: Value counts for categorical columns
                - memory_usage: Memory usage in bytes
                - dtypes: Data type distribution
        """
        logger.debug("Generating summary statistics")
        try:
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = self.data.select_dtypes(
                include=["object", "category", "bool"]
            ).columns.tolist()

            result: dict[str, Any] = {
                "shape": self.data.shape,
                "column_count": self.data.shape[1],
                "row_count": self.data.shape[0],
                "numeric_stats": {},
                "categorical_stats": {},
                "memory_usage": int(self.data.memory_usage(deep=True).sum()),
                "dtypes": {
                    str(dtype): int(count)
                    for dtype, count in self.data.dtypes.value_counts().items()
                },
            }

            if numeric_cols:
                desc = self.data[numeric_cols].describe()
                result["numeric_stats"] = {
                    col: {
                        "count": float(desc[col]["count"]),
                        "mean": float(desc[col]["mean"]),
                        "std": float(desc[col]["std"]),
                        "min": float(desc[col]["min"]),
                        "25%": float(desc[col]["25%"]),
                        "50%": float(desc[col]["50%"]),
                        "75%": float(desc[col]["75%"]),
                        "max": float(desc[col]["max"]),
                    }
                    for col in numeric_cols
                }

            if categorical_cols:
                for col in categorical_cols:
                    value_counts = self.data[col].value_counts()
                    result["categorical_stats"][col] = {
                        "unique_count": int(self.data[col].nunique()),
                        "top_values": {
                            str(k): int(v)
                            for k, v in value_counts.head(10).items()
                        },
                        "null_count": int(self.data[col].isnull().sum()),
                    }

            logger.debug("Summary statistics generated successfully")
            return result
        except Exception as e:
            logger.error("Failed to generate summary statistics: %s", str(e))
            raise

    def data_types(self) -> dict[str, Any]:
        """Analyze column data types and null counts.

        Returns:
            A dictionary containing:
                - columns: List of column information dicts with name, dtype,
                  null_count, null_percentage, and unique_count
                - dtype_summary: Count of columns by data type
                - total_nulls: Total number of null values
                - total_null_percentage: Percentage of null values
        """
        logger.debug("Analyzing data types")
        try:
            columns_info = []
            total_nulls = 0

            for col in self.data.columns:
                null_count = int(self.data[col].isnull().sum())
                total_nulls += null_count
                unique_count = int(self.data[col].nunique())

                columns_info.append(
                    {
                        "name": col,
                        "dtype": str(self.data[col].dtype),
                        "null_count": null_count,
                        "null_percentage": round(
                            (null_count / len(self.data)) * 100, 2
                        )
                        if len(self.data) > 0
                        else 0.0,
                        "unique_count": unique_count,
                    }
                )

            total_elements = self.data.shape[0] * self.data.shape[1]
            result = {
                "columns": columns_info,
                "dtype_summary": {
                    str(dtype): int(count)
                    for dtype, count in self.data.dtypes.value_counts().items()
                },
                "total_nulls": total_nulls,
                "total_null_percentage": round(
                    (total_nulls / total_elements) * 100, 2
                )
                if total_elements > 0
                else 0.0,
            }

            logger.debug("Data type analysis completed")
            return result
        except Exception as e:
            logger.error("Failed to analyze data types: %s", str(e))
            raise

    def correlations(self) -> dict[str, Any]:
        """Compute correlation matrix for numeric columns.

        Calculates Pearson correlation coefficients between all numeric columns
        and identifies highly correlated pairs.

        Returns:
            A dictionary containing:
                - correlation_matrix: Dictionary representation of the correlation matrix
                - highly_correlated_pairs: List of column pairs with |correlation| > 0.7
                - numeric_columns: List of numeric column names
        """
        logger.debug("Computing correlations")
        try:
            numeric_data = self.data.select_dtypes(include=[np.number])

            if numeric_data.empty:
                logger.warning("No numeric columns found for correlation analysis")
                return {
                    "correlation_matrix": {},
                    "highly_correlated_pairs": [],
                    "numeric_columns": [],
                }

            corr_matrix = numeric_data.corr()
            corr_dict = corr_matrix.to_dict()

            highly_correlated = []
            cols = corr_matrix.columns.tolist()
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:
                        highly_correlated.append(
                            {
                                "column_1": cols[i],
                                "column_2": cols[j],
                                "correlation": round(float(corr_val), 4),
                            }
                        )

            result = {
                "correlation_matrix": {
                    col: {inner_col: round(float(val), 4) for inner_col, val in row.items()}
                    for col, row in corr_dict.items()
                },
                "highly_correlated_pairs": highly_correlated,
                "numeric_columns": cols,
            }

            logger.debug(
                "Correlation analysis completed, found %d highly correlated pairs",
                len(highly_correlated),
            )
            return result
        except Exception as e:
            logger.error("Failed to compute correlations: %s", str(e))
            raise

    def distributions(self, column: str) -> dict[str, Any]:
        """Analyze distribution of a column.

        Computes statistical measures and tests for normality on the specified column.

        Args:
            column: Name of the column to analyze.

        Returns:
            A dictionary containing:
                - column: Column name
                - count: Number of non-null values
                - mean: Mean value
                - std: Standard deviation
                - min: Minimum value
                - max: Maximum value
                - skewness: Distribution skewness
                - kurtosis: Distribution kurtosis
                - is_normal: Whether distribution is approximately normal (Shapiro-Wilk test)
                - percentiles: Dictionary of percentile values (1, 5, 10, 25, 50, 75, 90, 95, 99)
                - histogram_bins: Bin edges and counts for histogram visualization

        Raises:
            KeyError: If the column doesn't exist in the DataFrame.
            ValueError: If the column is not numeric.
        """
        logger.debug("Analyzing distribution for column: %s", column)
        try:
            if column not in self.data.columns:
                raise KeyError(f"Column '{column}' not found in DataFrame")

            series = self.data[column].dropna()

            if series.empty:
                raise ValueError(f"Column '{column}' contains no non-null values")

            if not pd.api.types.is_numeric_dtype(series):
                raise ValueError(f"Column '{column}' is not numeric")

            values = series.values.astype(float)

            skewness = float(stats.skew(values))
            kurtosis_val = float(stats.kurtosis(values))

            is_normal = False
            if len(values) >= 3 and len(values) <= 5000:
                try:
                    _, p_value = stats.shapiro(values)
                    is_normal = p_value > 0.05
                except Exception:
                    is_normal = False

            hist_counts, bin_edges = np.histogram(values, bins=30)

            percentiles = {
                f"{p}%": round(float(np.percentile(values, p)), 4)
                for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]
            }

            result = {
                "column": column,
                "count": int(len(values)),
                "mean": round(float(np.mean(values)), 4),
                "std": round(float(np.std(values)), 4),
                "min": round(float(np.min(values)), 4),
                "max": round(float(np.max(values)), 4),
                "skewness": round(skewness, 4),
                "kurtosis": round(kurtosis_val, 4),
                "is_normal": is_normal,
                "percentiles": percentiles,
                "histogram": {
                    "bin_edges": [round(float(e), 4) for e in bin_edges],
                    "counts": [int(c) for c in hist_counts],
                },
            }

            logger.debug("Distribution analysis completed for column: %s", column)
            return result
        except (KeyError, ValueError) as e:
            logger.error("Distribution analysis failed: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in distribution analysis: %s", str(e))
            raise

    def detect_outliers(
        self, columns: list[str] | None = None
    ) -> dict[str, Any]:
        """Detect outliers using the IQR (Interquartile Range) method.

        Identifies outliers as values falling below Q1 - 1.5*IQR or above Q3 + 1.5*IQR.

        Args:
            columns: Optional list of column names to analyze. If None, all numeric
                     columns are analyzed.

        Returns:
            A dictionary containing:
                - column_outliers: Dict mapping column names to outlier information
                - total_outliers: Total count of outlier values across all columns
                - columns_analyzed: List of columns that were analyzed

        Raises:
            KeyError: If any specified column doesn't exist in the DataFrame.
        """
        logger.debug("Detecting outliers")
        try:
            if columns is None:
                columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
            else:
                for col in columns:
                    if col not in self.data.columns:
                        raise KeyError(f"Column '{col}' not found in DataFrame")
                columns = [
                    col for col in columns if pd.api.types.is_numeric_dtype(self.data[col])
                ]

            column_outliers = {}
            total_outliers = 0

            for col in columns:
                series = self.data[col].dropna()
                if series.empty:
                    continue

                q1 = float(series.quantile(0.25))
                q3 = float(series.quantile(0.75))
                iqr = q3 - q1

                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                outlier_mask = (series < lower_bound) | (series > upper_bound)
                outlier_count = int(outlier_mask.sum())
                total_outliers += outlier_count

                column_outliers[col] = {
                    "outlier_count": outlier_count,
                    "outlier_percentage": round(
                        (outlier_count / len(series)) * 100, 2
                    )
                    if len(series) > 0
                    else 0.0,
                    "lower_bound": round(lower_bound, 4),
                    "upper_bound": round(upper_bound, 4),
                    "q1": round(q1, 4),
                    "q3": round(q3, 4),
                    "iqr": round(iqr, 4),
                    "outlier_values": [
                        round(float(v), 4) for v in series[outlier_mask].head(10).values
                    ],
                }

            result = {
                "column_outliers": column_outliers,
                "total_outliers": total_outliers,
                "columns_analyzed": columns,
            }

            logger.debug(
                "Outlier detection completed, found %d total outliers",
                total_outliers,
            )
            return result
        except KeyError as e:
            logger.error("Outlier detection failed: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in outlier detection: %s", str(e))
            raise

    def missing_analysis(self) -> dict[str, Any]:
        """Analyze missing data patterns.

        Provides comprehensive analysis of missing values including counts,
        percentages, and patterns.

        Returns:
            A dictionary containing:
                - column_missing: Dict with null count and percentage for each column
                - total_missing: Total number of missing values
                - total_percentage: Percentage of missing values
                - complete_rows: Number of rows with no missing values
                - incomplete_rows: Number of rows with at least one missing value
                - missing_patterns: List of missing data patterns (rows with same columns missing)
                - columns_with_missing: List of columns that have missing values
                - columns_without_missing: List of columns with no missing values
        """
        logger.debug("Analyzing missing data patterns")
        try:
            column_missing = {}
            columns_with_missing = []
            columns_without_missing = []

            for col in self.data.columns:
                null_count = int(self.data[col].isnull().sum())
                null_percentage = round(
                    (null_count / len(self.data)) * 100, 2
                ) if len(self.data) > 0 else 0.0

                column_missing[col] = {
                    "null_count": null_count,
                    "null_percentage": null_percentage,
                }

                if null_count > 0:
                    columns_with_missing.append(col)
                else:
                    columns_without_missing.append(col)

            total_missing = int(self.data.isnull().sum().sum())
            total_elements = self.data.shape[0] * self.data.shape[1]
            total_percentage = round(
                (total_missing / total_elements) * 100, 2
            ) if total_elements > 0 else 0.0

            missing_mask = self.data.isnull()
            complete_rows = int((~missing_mask.any(axis=1)).sum())
            incomplete_rows = int(missing_mask.any(axis=1).sum())

            pattern_groups = missing_mask.groupby(list(missing_mask.columns)).size()
            missing_patterns = []
            for pattern_idx, count in pattern_groups.items():
                if count > 0 and any(pattern_idx):
                    missing_cols = [
                        col
                        for col, is_missing in zip(missing_mask.columns, pattern_idx)
                        if is_missing
                    ]
                    missing_patterns.append(
                        {
                            "columns_missing": missing_cols,
                            "row_count": int(count),
                            "percentage": round(
                                (count / len(self.data)) * 100, 2
                            )
                            if len(self.data) > 0
                            else 0.0,
                        }
                    )

            missing_patterns.sort(key=lambda x: x["row_count"], reverse=True)

            result = {
                "column_missing": column_missing,
                "total_missing": total_missing,
                "total_percentage": total_percentage,
                "complete_rows": complete_rows,
                "incomplete_rows": incomplete_rows,
                "missing_patterns": missing_patterns[:10],
                "columns_with_missing": columns_with_missing,
                "columns_without_missing": columns_without_missing,
            }

            logger.debug(
                "Missing data analysis completed, found %d columns with missing data",
                len(columns_with_missing),
            )
            return result
        except Exception as e:
            logger.error("Failed to analyze missing data: %s", str(e))
            raise
