from typing import Optional, Tuple


def get_recommended_difficulty(mastery_score: Optional[int]) -> Tuple[str, str]:
    """
    Deterministic adaptive quiz difficulty rules based on topic mastery:
    - 0-49% mastery   -> easy
    - 50-79% mastery  -> medium
    - 80-100% mastery -> hard
    - Missing/None    -> easy (default)

    Returns:
        Tuple[difficulty_str, explanation_str]
    """
    if mastery_score is None:
        return (
            "easy",
            "No previous quiz history found for this topic. Starting with an easy-level quiz is recommended to build foundational knowledge.",
        )

    # Bounded score
    score = max(0, min(100, int(mastery_score)))

    if score < 50:
        return (
            "easy",
            f"Your current mastery is {score}%, so an easy-level quiz is recommended to strengthen fundamental concepts.",
        )
    elif score < 80:
        return (
            "medium",
            f"Your current mastery is {score}%, so a medium-level quiz is recommended to test conceptual understanding and application.",
        )
    else:
        return (
            "hard",
            f"Your current mastery is {score}%, so a hard-level quiz is recommended to challenge deeper reasoning and scenario analysis.",
        )
