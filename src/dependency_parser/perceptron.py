"""An averaged structured perceptron over transition decisions.

The policy scores each candidate transition as the dot product of the active
feature vector with a per transition weight vector. Training follows the gold
oracle sequence with teacher forcing: at every decision point the highest scoring
legal transition is compared with the oracle transition, and on a mistake the
weights are nudged toward the oracle and away from the prediction. Collins style
weight averaging is applied lazily with update timestamps so the final model is
the mean of every intermediate weight vector, which markedly reduces variance.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

Key = tuple[str, str]


@dataclass
class AveragedPerceptron:
    """Sparse linear weights keyed by (feature, transition) with lazy averaging."""

    weights: dict[Key, float] = field(default_factory=dict)
    _totals: dict[Key, float] = field(default_factory=lambda: defaultdict(float))
    _timestamps: dict[Key, int] = field(default_factory=lambda: defaultdict(int))
    _steps: int = 0

    def score(self, features: list[str], actions: list[str]) -> dict[str, float]:
        scores: dict[str, float] = dict.fromkeys(actions, 0.0)
        for feature in features:
            for action in actions:
                weight = self.weights.get((feature, action))
                if weight:
                    scores[action] += weight
        return scores

    def predict(self, features: list[str], actions: list[str]) -> str:
        scores = self.score(features, actions)
        return max(actions, key=lambda action: (scores[action], action))

    def _nudge(self, key: Key, delta: float) -> None:
        self._totals[key] += (self._steps - self._timestamps[key]) * self.weights.get(key, 0.0)
        self._timestamps[key] = self._steps
        self.weights[key] = self.weights.get(key, 0.0) + delta

    def update(self, features: list[str], predicted: str, gold: str) -> None:
        self._steps += 1
        if predicted == gold:
            return
        for feature in features:
            self._nudge((feature, gold), 1.0)
            self._nudge((feature, predicted), -1.0)

    def finalize(self) -> None:
        """Replace the weights with their average over all training steps.

        Each weight is held from the step it was last set through the final step,
        inclusive, so the interval spans ``_steps - timestamp + 1`` steps. Omitting
        the ``+ 1`` would exclude the step on which the weight was set and average
        the pre-update weights (w0..w(T-1)) rather than the post-update weights
        (w1..wT) that Collins averaging specifies.
        """

        if self._steps == 0:
            return
        averaged: dict[Key, float] = {}
        for key, weight in self.weights.items():
            total = self._totals[key] + (self._steps - self._timestamps[key] + 1) * weight
            mean = total / self._steps
            if mean:
                averaged[key] = mean
        self.weights = averaged
