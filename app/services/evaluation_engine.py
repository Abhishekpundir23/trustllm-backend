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

    for test in test_cases:
        # 1. Prepare Prompt
        content = test.prompt
        if system_template:
            content = system_template.replace("{{prompt}}", test.prompt)

        # 2. Call Gemini (The Student)
        output = call_gemini_safe(content)
        
        # 3. Score it (The Teacher) <--- UPDATED
        score, category = score_response_smart(output, test)

        results.append({
            "test_id": test.id,
            "output": output,
            "score": score,
            "category": category,
        })

    return results

def call_gemini_safe(prompt):
    """
    Calls Google Gemini API. Falls back to Mock if it fails.
    """
    try:
        if not client:
            raise Exception("No Gemini API Key found")

        # Using the alias that worked for you
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt
        )
        return response.text

    except Exception as e:
        print(f"⚠️ Gemini Failed: {e}")
        return f"[Mock Fallback] (Real AI Failed: {str(e)}) | Response to: {prompt}"

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
    # (e.g. Expected "7", Output "It be 7 colors") -> Pass
    if expected.lower() in output.lower():
        return 2, "correct"
    
    # 2. SMART CHECK: If fast check fails, ask the AI Judge.
    # (e.g. Expected "7", Output "Seven colors") -> AI will fix this.
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
        
        # We reuse the safe caller to do the grading!
        verdict = call_gemini_safe(grading_prompt)
        
        if "YES" in verdict.upper():
            return 2, "correct"
        else:
            return 0, "incorrect"

    except Exception as e:
        print(f"Grading Failed: {e}")
        return 0, "incorrect"