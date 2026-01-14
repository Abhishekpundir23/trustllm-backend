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

        # 2. Call Gemini (or Fallback)
        output = call_gemini_safe(content)
        
        # 3. Score it
        score, category = score_response(output, test)

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

        # FIX: Using the 'latest' alias which appeared in your available list
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt
        )
        return response.text

    except Exception as e:
        print(f"⚠️ Gemini Failed: {e}")
        return f"[Mock Fallback] (Real AI Failed: {str(e)}) | Response to: {prompt}"

def score_response(output: str, test_case) -> tuple[int, str]:
    if test_case.expected and test_case.expected.lower() in output.lower():
        return 2, "correct"
    return 0, "incorrect"