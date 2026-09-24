"""
Evaluation script for the LangGraph AI agent's intent classification.

This calls the REAL, running backend (not mocks), sends every test case
through the actual /api/v1/ai/chat endpoint, and compares the agent's
classified intent against the expected one. This is what turns "I think
it works" into an actual measured accuracy number.

Usage:
    1. Make sure the backend is running (uvicorn app.main:app ...)
    2. Set EVAL_EMAIL / EVAL_PASSWORD below (or via environment variables)
       to a real account that already exists in your database.
    3. Run: python evaluate_agent.py
"""

import asyncio
import json
import os
from collections import defaultdict

import httpx

BASE_URL = os.environ.get("EVAL_BASE_URL", "http://localhost:8000")
EMAIL = os.environ.get("EVAL_EMAIL", "emvs2005@gmail.com")
PASSWORD = os.environ.get("EVAL_PASSWORD", "1234567")
TEST_CASES_FILE = os.path.join(os.path.dirname(__file__), "test_cases.json")


async def get_auth_token(client: httpx.AsyncClient) -> str:
    response = await client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    response.raise_for_status()
    return response.json()["access_token"]


async def run_evaluation():
    with open(TEST_CASES_FILE, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            token = await get_auth_token(client)
        except Exception as e:
            print(f"❌ Could not log in ({EMAIL}). Check EVAL_EMAIL/EVAL_PASSWORD and that the backend is running.")
            print(f"   Error: {e}")
            return

        headers = {"Authorization": f"Bearer {token}"}

        results = []
        per_tool_correct = defaultdict(int)
        per_tool_total = defaultdict(int)

        print(f"\nRunning {len(test_cases)} test cases against {BASE_URL} ...\n")

        for i, case in enumerate(test_cases, start=1):
            message = case["input"]
            expected = case["expected_intent"]

            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/ai/chat",
                    json={"message": message},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                actual = data.get("intent", "UNKNOWN")
            except Exception as e:
                actual = f"ERROR: {e}"

            is_correct = actual == expected
            per_tool_total[expected] += 1
            if is_correct:
                per_tool_correct[expected] += 1

            results.append({
                "input": message,
                "expected": expected,
                "actual": actual,
                "correct": is_correct,
            })

            status = "✅" if is_correct else "❌"
            print(f"{status} [{i:2d}/{len(test_cases)}] expected={expected:<18} actual={actual:<18} \"{message[:50]}\"")

        # ---- Report ----
        total_correct = sum(r["correct"] for r in results)
        total = len(results)
        overall_accuracy = (total_correct / total * 100) if total else 0

        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        print(f"Overall accuracy: {total_correct}/{total} ({overall_accuracy:.1f}%)\n")

        print("Per-tool accuracy:")
        for tool in sorted(per_tool_total.keys()):
            correct = per_tool_correct[tool]
            total_for_tool = per_tool_total[tool]
            pct = (correct / total_for_tool * 100) if total_for_tool else 0
            print(f"  {tool:<20} {correct}/{total_for_tool} ({pct:.0f}%)")

        failures = [r for r in results if not r["correct"]]
        if failures:
            print(f"\n{len(failures)} failure(s):")
            for f in failures:
                print(f"  - \"{f['input']}\" -> expected {f['expected']}, got {f['actual']}")

        # Save full results for later comparison / regression tracking
        output_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "overall_accuracy": overall_accuracy,
                "per_tool": {
                    tool: {
                        "correct": per_tool_correct[tool],
                        "total": per_tool_total[tool],
                    }
                    for tool in per_tool_total
                },
                "results": results,
            }, f, indent=2)
        print(f"\nFull results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())