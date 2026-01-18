import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Initialize the Client
client = None
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)

def evaluate(test_cases, model_name, system_template=None):
    results = []
    
    # Track Total Tokens for this entire run
    total_input = 0
    total_output = 0

    for test in test_cases:
        # 1. Prepare Prompt
        content = test.prompt
        if system_template:
            content = system_template.replace("{{prompt}}", test.prompt)

        # 2. Call Gemini (Get Text AND Usage)
        output, usage = call_gemini_with_usage(content)
        
        # Accumulate usage stats if available
        if usage:
            total_input += usage.prompt_token_count
            total_output += usage.candidates_token_count

        # 3. Score it (The Teacher)
        score, category = score_response_smart(output, test)

        results.append({
            "test_id": test.id,
            "output": output,
            "score": score,
            "category": category,
        })

    # Return Results AND Token Counts
    return results, total_input, total_output

def call_gemini_with_usage(prompt):
    """
    Calls Google Gemini API. Returns (text, usage_metadata).
    """
    try:
        if not client:
            raise Exception("No Gemini API Key found")

        # Using the alias that worked for you
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt
        )
        return response.text, response.usage_metadata

    except Exception as e:
        print(f"⚠️ Gemini Failed: {e}")
        # Return error text and None for usage
        return f"[Mock Fallback] (Real AI Failed: {str(e)}) | Response to: {prompt}", None

def call_gemini_safe(prompt):
    """
    Simple wrapper for internal grading calls (doesn't track usage for simplicity, 
    or you could add tracking here too if you want strict accounting).
    """
    text, _ = call_gemini_with_usage(prompt)
    return text

def score_response_smart(output: str, test_case) -> tuple[int, str]:
    """
    Hybrid Grader:
    1. Fast Keyword Match (Cheap)
    2. AI Semantic Judge (Smart)
    """
    expected = test_case.expected
    if not expected:
        return 2, "correct" # No expectation = Pass

    # 1. FAST CHECK: If the exact text is found, pass immediately.
    if expected.lower() in output.lower():
        return 2, "correct"
    
    # 2. SMART CHECK: If fast check fails, ask the AI Judge.
    try:
        print(f"🕵️ Fast check failed. Asking AI Judge to grade: '{expected}' vs '{output[:20]}...'")
        
        grading_prompt = f"""
        You are a strict teacher grading an exam.
        
        Question: {test_case.prompt}
        Expected Fact: {expected}
        Student Answer: {output}
        
        TASK: Does the Student Answer contain the correct fact? 
        Ignore style, tone (pirate/rude), and extra words. 
        Only check if the core meaning matches the Expected Fact.
        
        Reply strictly with 'YES' or 'NO'.
        """
        
        # Reuse safe caller (Judge usage is generally small, ignoring for now)
        verdict = call_gemini_safe(grading_prompt)
        
        if "YES" in verdict.upper():
            return 2, "correct"
        else:
            return 0, "incorrect"

    except Exception as e:
        print(f"Grading Failed: {e}")
        return 0, "incorrect"