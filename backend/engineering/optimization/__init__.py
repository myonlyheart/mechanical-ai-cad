"""Optimization module - 多方案生成与评分。"""

from .variants import (
    ScoringWeights,
    score_variant, generate_variants,
    compare_variants, recommend_variant,
    score_manufacturability, score_printability,
    score_strength, score_cost, score_weight,
)

__all__ = [
    "ScoringWeights",
    "score_variant", "generate_variants",
    "compare_variants", "recommend_variant",
    "score_manufacturability", "score_printability",
    "score_strength", "score_cost", "score_weight",
]
