def evaluate(test_cases, model_name):
    results = []

    for test in test_cases:
        output = query_llm(test.prompt, model_name)
        score, category, reason = score_response(
            output,
            test.expected,
            test.rules,
            test.task_type
        )

        results.append({
            "test_id": test.id,
            "output": output,
            "score": score,
            "category": category,
            "reason": reason
        })

    return results
def mock_llm(prompt: str, model_name: str) -> str:
    # TEMPORARY: replace with OpenAI / HF later
    return f"[{model_name}] Response to: {prompt}"


def score_response(output: str, test_case) -> tuple[int, str]:
    """
    Returns (score, category)
    0 = incorrect
    1 = partial
    2 = correct
    """
    if test_case.expected and test_case.expected in output:
        return 2, "correct"
    return 0, "incorrect"
