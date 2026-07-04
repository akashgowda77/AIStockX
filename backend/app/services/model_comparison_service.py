"""
Model Comparison Service

Compares all available ML models and recommends
the best model based on multiple evaluation metrics.

Current Supported Models
-------------------------
- Linear Regression
- LSTM

Future Models
-------------
- Random Forest
- XGBoost
- Prophet
- ARIMA
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..ml.linear_regression_model import LinearRegressionModel
from ..ml.lstm_model import LSTMModel


# ============================================================
# Data Container
# ============================================================

@dataclass
class ModelResult:
    """
    Standard container representing one trained model.
    Every model returns exactly this structure.
    """

    model_name: str
    predicted_price: float
    actual_price: Optional[float]
    confidence_score: float
    metrics: Dict[str, float]
    ai_score: float = 0.0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Model Comparison Service
# ============================================================

class ModelComparisonService:
    """
    Compare all trained ML models using weighted AI scoring.

    Responsibilities
    ----------------
    1. Evaluate each model
    2. Calculate AI score using weighted raw metrics
    3. Find winners for every metric
    4. Generate strengths and weaknesses
    5. Recommend best model with explanation
    6. Return leaderboard and metadata
    """

    # ============================================================
    # Scoring Weights
    # ============================================================

    WEIGHTS = {
        "prediction_accuracy": 0.30,
        "rmse": 0.20,
        "mae": 0.15,
        "mape": 0.10,
        "direction_accuracy": 0.10,
        "r2_score": 0.10,
        "confidence": 0.05,
    }

    # ============================================================
    # Initialization
    # ============================================================

    def __init__(self) -> None:
        pass

    # ============================================================
    # Model Evaluation
    # ============================================================

    def _evaluate_linear(self, symbol: str) -> Optional[ModelResult]:
        """
        Evaluate trained Linear Regression model.

        Args:
            symbol: Stock ticker symbol

        Returns:
            ModelResult if model exists, None otherwise
        """

        model = LinearRegressionModel(symbol)

        if not model.model_manager.model_exists(model._model_name):
            return None

        model.load_model()

        prediction = model.predict_next_close(
            include_actual=True,
        )

        return ModelResult(
            model_name=model.model_name(),
            predicted_price=prediction.predicted_price,
            actual_price=prediction.actual_price,
            confidence_score=prediction.confidence_score,
            metrics=dict(prediction.metrics),
            metadata=self._extract_linear_metadata(model, prediction),
        )

    def _evaluate_lstm(self, symbol: str) -> Optional[ModelResult]:
        """
        Evaluate trained LSTM model.

        Args:
            symbol: Stock ticker symbol

        Returns:
            ModelResult if model exists, None otherwise
        """

        model = LSTMModel(symbol)

        # LSTM uses .keras instead of joblib
        if not os.path.exists(model._keras_model_path()):
            return None

        model.load_model()

        prediction = model.predict_next_close()

        return ModelResult(
            model_name=model.model_name(),
            predicted_price=prediction.predicted_price,
            actual_price=prediction.actual_price,
            confidence_score=prediction.confidence_score,
            metrics=dict(prediction.metrics),
            metadata=self._extract_lstm_metadata(model, prediction),
        )

    # ============================================================
    # Metadata Extraction
    # ============================================================

    def _extract_linear_metadata(
        self, model: LinearRegressionModel, prediction: Any
    ) -> Dict[str, Any]:
        """
        Extract metadata from Linear Regression model.

        Args:
            model: Linear Regression model instance
            prediction: Prediction result

        Returns:
            Dictionary containing model metadata
        """

        return {
            "training_date": getattr(model, "_training_date", None),
            "training_rows": getattr(model, "_training_rows", None),
            "feature_count": getattr(model, "_feature_count", None),
            "rmse": prediction.metrics.get("rmse"),
            "mae": prediction.metrics.get("mae"),
            "mape": prediction.metrics.get("mape"),
            "r2_score": prediction.metrics.get("r2_score"),
            "confidence": prediction.confidence_score,
        }

    def _extract_lstm_metadata(
        self, model: LSTMModel, prediction: Any
    ) -> Dict[str, Any]:
        """
        Extract metadata from LSTM model.

        Args:
            model: LSTM model instance
            prediction: Prediction result

        Returns:
            Dictionary containing model metadata
        """

        return {
            "training_date": getattr(model, "_training_date", None),
            "training_rows": getattr(model, "_training_rows", None),
            "feature_count": getattr(model, "_feature_count", None),
            "epochs": getattr(model, "_epochs", None),
            "lookback": getattr(model, "_lookback", None),
            "training_duration": getattr(model, "_training_duration", None),
            "rmse": prediction.metrics.get("rmse"),
            "mae": prediction.metrics.get("mae"),
            "mape": prediction.metrics.get("mape"),
            "r2_score": prediction.metrics.get("r2_score"),
            "confidence": prediction.confidence_score,
        }

    # ============================================================
    # AI Score Calculation
    # ============================================================

    def _calculate_ai_scores(self, results: List[ModelResult]) -> None:
        """
        Calculate AI scores for all models using weighted raw metrics.

        Scoring Formula:
        - prediction_accuracy_score = prediction_accuracy_percent
        - rmse_score = max(0, 100 - rmse)
        - mae_score = max(0, 100 - mae)
        - mape_score = max(0, 100 - mape)
        - direction_score = direction_accuracy
        - r2_score = 0 if r2 < 0, 100 if r2 > 1, else r2 * 100
        - confidence_score = confidence

        Final AI Score = weighted sum of all scores (0-100)

        Args:
            results: List of model results to score
        """

        if not results:
            return

        for result in results:
            # Extract raw metrics
            prediction_accuracy = result.metrics.get("prediction_accuracy_percent", 0.0)
            rmse = result.metrics.get("rmse", 9999.0)
            mae = result.metrics.get("mae", 9999.0)
            mape = result.metrics.get("mape", 9999.0)
            direction_accuracy = result.metrics.get("direction_accuracy", 0.0)
            r2 = result.metrics.get("r2_score", 0.0)
            confidence = result.confidence_score

            # Calculate individual scores
            prediction_score = prediction_accuracy
            rmse_score = max(0.0, 100.0 - rmse)
            mae_score = max(0.0, 100.0 - mae)
            mape_score = max(0.0, 100.0 - mape)
            direction_score = direction_accuracy

            # R² score normalization
            if r2 < 0:
                r2_score = 0.0
            elif r2 > 1:
                r2_score = 100.0
            else:
                r2_score = r2 * 100.0

            confidence_score = confidence

            # Calculate weighted AI score
            ai_score = round(
                (
                    prediction_score * self.WEIGHTS["prediction_accuracy"]
                    + rmse_score * self.WEIGHTS["rmse"]
                    + mae_score * self.WEIGHTS["mae"]
                    + mape_score * self.WEIGHTS["mape"]
                    + direction_score * self.WEIGHTS["direction_accuracy"]
                    + r2_score * self.WEIGHTS["r2_score"]
                    + confidence_score * self.WEIGHTS["confidence"]
                ),
                2,
            )

            result.ai_score = ai_score

    # ============================================================
    # Metric Winners
    # ============================================================

    def _find_metric_winners(self, results: List[ModelResult]) -> Dict[str, str]:
        """
        Determine which model performs best for every metric.

        Args:
            results: List of model results

        Returns:
            Dictionary mapping metric names to winning model names
        """

        if not results:
            return {}

        def higher_is_better(metric: str) -> str:
            """Find model with highest value for metric."""
            values = [r.metrics.get(metric, 0.0) for r in results]

            if len(set(values)) == 1:
                return "Tie"

            winner = max(results, key=lambda r: r.metrics.get(metric, 0.0))
            return winner.model_name

        def lower_is_better(metric: str) -> str:
            """Find model with lowest value for metric."""
            values = [r.metrics.get(metric, 9999.0) for r in results]

            if len(set(values)) == 1:
                return "Tie"

            winner = min(results, key=lambda r: r.metrics.get(metric, 9999.0))
            return winner.model_name

        return {
            "Prediction Accuracy": higher_is_better("prediction_accuracy_percent"),
            "Direction Accuracy": higher_is_better("direction_accuracy"),
            "RMSE": lower_is_better("rmse"),
            "MAE": lower_is_better("mae"),
            "MAPE": lower_is_better("mape"),
            "R²": higher_is_better("r2_score"),
            "Confidence": higher_is_better("confidence_score"),
        }

    # ============================================================
    # Strengths & Weaknesses
    # ============================================================

    def _calculate_strengths_weaknesses(
        self, results: List[ModelResult], metric_winners: Dict[str, str]
    ) -> None:
        """
        Calculate strengths and weaknesses for each model.

        Args:
            results: List of model results
            metric_winners: Dictionary of metric winners
        """

        for result in results:
            strengths = []
            weaknesses = []

            # Find metrics where this model wins
            for metric, winner in metric_winners.items():
                if winner == result.model_name:
                    strengths.append(metric)

            # Find metrics where this model loses
            for metric, winner in metric_winners.items():
                if winner != "Tie" and winner != result.model_name:
                    if metric in ["RMSE", "MAE", "MAPE"]:
                        weaknesses.append(f"Higher {metric}")
                    else:
                        weaknesses.append(f"Lower {metric}")

            result.strengths = strengths
            result.weaknesses = weaknesses

    # ============================================================
    # AI Recommendation Engine
    # ============================================================

    def _generate_recommendation(
        self,
        winner: ModelResult,
        metric_winners: Dict[str, str],
    ) -> str:
        """
        Generate professional recommendation explaining why the model was selected.

        Args:
            winner: Best performing model
            metric_winners: Dictionary of metric winners

        Returns:
            Professional recommendation string
        """

        # Find winning metrics for the recommended model
        winning_metrics = [
            metric for metric, model in metric_winners.items()
            if model == winner.model_name
        ]

        # Build recommendation
        if winning_metrics:
            metrics_list = ", ".join(winning_metrics[:-1])
            if len(winning_metrics) > 1:
                metrics_list += f" and {winning_metrics[-1]}"
            else:
                metrics_list = winning_metrics[0]

            recommendation = (
                f"{winner.model_name} is recommended because it achieved the highest "
                f"{metrics_list}. "
                f"Overall AI Score: {winner.ai_score:.2f}/100."
            )
        else:
            recommendation = (
                f"{winner.model_name} is recommended based on its overall "
                f"AI Score of {winner.ai_score:.2f}/100."
            )

        return recommendation

    # ============================================================
    # Recommendation
    # ============================================================

    def _recommend(self, results: List[ModelResult]) -> ModelResult:
        """
        Return the highest-scoring model.

        Args:
            results: List of model results

        Returns:
            ModelResult with highest AI score
        """

        return max(results, key=lambda r: r.ai_score)

    # ============================================================
    # Public API
    # ============================================================

    def compare(self, symbol: str) -> Dict[str, Any]:
        """
        Compare every trained model for a stock.

        Workflow
        --------
        1. Evaluate all available models
        2. Calculate AI scores using weighted raw metrics
        3. Determine metric winners
        4. Calculate strengths and weaknesses
        5. Recommend the best model
        6. Return a rich comparison payload

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary containing complete comparison results

        Raises:
            RuntimeError: If no trained models are available
        """

        results: List[ModelResult] = []

        # --------------------------------------------------------
        # Evaluate Linear Regression
        # --------------------------------------------------------

        linear = self._evaluate_linear(symbol)

        if linear is not None:
            results.append(linear)

        # --------------------------------------------------------
        # Evaluate LSTM
        # --------------------------------------------------------

        lstm = self._evaluate_lstm(symbol)

        if lstm is not None:
            results.append(lstm)

        # --------------------------------------------------------
        # Validate results
        # --------------------------------------------------------

        if not results:
            raise RuntimeError(
                "No trained prediction models available."
            )

        # --------------------------------------------------------
        # Calculate AI scores
        # --------------------------------------------------------

        self._calculate_ai_scores(results)

        # --------------------------------------------------------
        # Find metric winners
        # --------------------------------------------------------

        metric_winners = self._find_metric_winners(results)

        # --------------------------------------------------------
        # Calculate strengths and weaknesses
        # --------------------------------------------------------

        self._calculate_strengths_weaknesses(results, metric_winners)

        # --------------------------------------------------------
        # Rank models by AI score
        # --------------------------------------------------------

        results.sort(key=lambda r: r.ai_score, reverse=True)

        winner = results[0]

        # --------------------------------------------------------
        # Generate recommendation
        # --------------------------------------------------------

        recommendation = self._generate_recommendation(winner, metric_winners)

        # --------------------------------------------------------
        # Build response objects
        # --------------------------------------------------------

        comparison: Dict[str, Any] = {}
        leaderboard: List[Dict[str, Any]] = []
        metadata: Dict[str, Any] = {}

        for rank, result in enumerate(results, start=1):
            # Comparison details
            comparison[result.model_name] = {
                "predicted_price": result.predicted_price,
                "actual_price": result.actual_price,
                "confidence_score": result.confidence_score,
                "ai_score": result.ai_score,
                "metrics": result.metrics,
                "strengths": result.strengths,
                "weaknesses": result.weaknesses,
            }

            # Leaderboard entry
            leaderboard.append({
                "rank": rank,
                "model": result.model_name,
                "ai_score": result.ai_score,
                "confidence": result.confidence_score,
                "prediction_accuracy": result.metrics.get("prediction_accuracy_percent"),
                "rmse": result.metrics.get("rmse"),
            })

            # Model metadata
            metadata[result.model_name] = result.metadata

        # --------------------------------------------------------
        # Return complete response
        # --------------------------------------------------------

        return {
            "symbol": symbol,
            "recommended_model": winner.model_name,
            "recommendation_reason": recommendation,
            "leaderboard": leaderboard,
            "metric_winners": metric_winners,
            "comparison": comparison,
            "metadata": metadata,
        }