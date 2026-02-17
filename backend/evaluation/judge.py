from __future__ import annotations

import json
import logging
from typing import TypedDict
from openai import OpenAI
from core.graph import run_router
from core.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eval_judge")

class EvaluationResult(TypedDict):
    id: str
    query: str
    expected_domain: str
    actual_domain: str
    correct_routing: bool
    score: int
    feedback: str

def evaluate_response(query: str, expected_domain: str, settings: Settings) -> EvaluationResult:
    """Run the router and judge the result."""
    
    # Run the system
    result = run_router(query)
    classification = result["classification"]
    actual_domain = classification.domain
    
    # Basic routing check
    correct_routing = actual_domain == expected_domain
    
    # LLM-as-a-Judge using OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    
    judge_prompt = f"""
    You are an impartial judge evaluating an AI assistant's response.
    
    Query: "{query}"
    Expected Domain: {expected_domain}
    Actual Domain: {actual_domain}
    Response: "{result['response'].content}"
    Safety Flags: {result['safety_flags']}
    
    Task:
    1. Verify if the domain routing makes sense (Medical vs Legal vs General).
    2. Check if the response matches the domain style (e.g. Legal disclaimer for legal queries).
    3. Rate the quality on a scale of 1-10.
    
    Return a JSON object with:
    {{
        "score": int,
        "feedback": "string explaining the score"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an expert evaluator."},
                {"role": "user", "content": judge_prompt}
            ],
            response_format={"type": "json_object"}
        )
        judge_output = json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Judge failed: {e}")
        judge_output = {"score": 0, "feedback": "Judge execution failed."}
        
    return {
        "id": "unknown",
        "query": query,
        "expected_domain": expected_domain,
        "actual_domain": actual_domain,
        "correct_routing": correct_routing,
        "score": judge_output.get("score", 0),
        "feedback": judge_output.get("feedback", "No feedback")
    }

def run_evaluation():
    settings = Settings.load()
    
    try:
        with open("backend/evaluation/dataset.json", "r") as f:
            test_cases = json.load(f)
    except FileNotFoundError:
        logger.error("Dataset not found! Run the planner step to create it.")
        return

    results = []
    print("\n--- Starting Evaluation ---\n")
    
    for case in test_cases:
        print(f"Testing: {case['query'][:50]}...")
        eval_res = evaluate_response(case['query'], case['expected_domain'], settings)
        eval_res['id'] = case['id']
        results.append(eval_res)
        
    # Calculate Metrics
    accuracy = sum(1 for r in results if r['correct_routing']) / len(results)
    avg_score = sum(r['score'] for r in results) / len(results)
    
    print("\n--- Evaluation Report ---")
    print(f"Total Cases: {len(results)}")
    print(f"Routing Accuracy: {accuracy:.2%}")
    print(f"Average Quality Score: {avg_score:.1f}/10")
    
    # Save Report
    with open("backend/evaluation/report.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Report saved to backend/evaluation/report.json")

if __name__ == "__main__":
    run_evaluation()
