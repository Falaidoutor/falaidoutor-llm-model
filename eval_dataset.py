"""
Evaluation script: sends each triage_text from the MIMICIV dataset to the LLM Model
and saves the responses for later comparison against ground-truth acuity labels.

Usage:
    python eval_dataset.py [--csv PATH] [--output PATH] [--delay SECONDS] [--limit N]

Output: JSON file with a list of records:
    {
        "edstay_id": ...,
        "acuity_ground_truth": ...,   # ESI 1-5 from dataset
        "triage_text": "...",
        "llm_response": { ... },      # full TriageResponse from the model
        "error": null | "message"     # populated only on failure
    }
"""

import argparse
import asyncio
import csv
import json
import sys
import time
from pathlib import Path

import httpx

LLM_BASE_URL = "http://localhost:8000"
TRIAGE_ENDPOINT = f"{LLM_BASE_URL}/triage"
DEFAULT_CSV = Path(__file__).parent / "mimiciv-triage-eval-dataset-v1.csv"
DEFAULT_OUTPUT = Path(__file__).parent / "eval_results.json"
REQUEST_TIMEOUT = 180.0  # seconds — LLM can be slow


async def call_triage(client: httpx.AsyncClient, symptoms: str) -> dict:
    response = await client.post(
        TRIAGE_ENDPOINT,
        json={"symptoms": symptoms},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


async def run_evaluation(csv_path: Path, output_path: Path, delay: float, limit: int | None):
    rows = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            if limit and len(rows) >= limit:
                break

    total = len(rows)
    print(f"Dataset: {csv_path.name} — {total} records to evaluate")
    print(f"Output : {output_path}")
    print(f"Endpoint: {TRIAGE_ENDPOINT}\n")

    VALID_CLASSIFICATIONS = {"ESI-1", "ESI-2", "ESI-3", "ESI-4", "ESI-5"}

    def is_valid_result(record: dict) -> bool:
        llm = record.get("llm_response") or {}
        return llm.get("classificacao") in VALID_CLASSIFICATIONS

    results = []

    # Load existing results to allow resuming interrupted runs
    if output_path.exists():
        with output_path.open(encoding="utf-8") as f:
            try:
                results = json.load(f)
                valid_count = sum(1 for r in results if is_valid_result(r))
                print(f"Resuming — {len(results)} records found, {valid_count} with valid classification (others will be retried).\n")
            except json.JSONDecodeError:
                results = []

    processed_ids = {str(r["edstay_id"]) for r in results if is_valid_result(r)}

    async with httpx.AsyncClient() as client:
        for i, row in enumerate(rows, start=1):
            edstay_id = row["edstay_id"]
            acuity = int(row["acuity"])
            triage_text = row["triage_text"]

            if edstay_id in processed_ids:
                print(f"[{i:>3}/{total}] edstay_id={edstay_id} — skipped (valid result exists)")
                continue

            # Remove previous failed/invalid attempt so the new result replaces it
            results = [r for r in results if str(r["edstay_id"]) != edstay_id]

            print(f"[{i:>3}/{total}] edstay_id={edstay_id} (ESI {acuity}) ... ", end="", flush=True)
            t0 = time.monotonic()

            record: dict = {
                "edstay_id": edstay_id,
                "acuity_ground_truth": acuity,
                "triage_text": triage_text,
                "llm_response": None,
                "error": None,
            }

            try:
                record["llm_response"] = await call_triage(client, triage_text)
                elapsed = time.monotonic() - t0
                classification = record["llm_response"].get("classificacao", "?")
                print(f"OK ({elapsed:.1f}s) → {classification}")
            except httpx.HTTPStatusError as exc:
                elapsed = time.monotonic() - t0
                record["error"] = f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
                print(f"HTTP ERROR ({elapsed:.1f}s) — {record['error']}")
            except Exception as exc:
                elapsed = time.monotonic() - t0
                record["error"] = str(exc)
                print(f"ERROR ({elapsed:.1f}s) — {record['error']}")

            results.append(record)

            # Persist after every record so a crash doesn't lose progress
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            if delay > 0 and i < total:
                await asyncio.sleep(delay)

    # --- Summary ---
    success = sum(1 for r in results if r["error"] is None)
    failed = sum(1 for r in results if r["error"] is not None)
    print(f"\nDone. {success} succeeded, {failed} failed.")
    print(f"Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate LLM triage model against MIMICIV dataset.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to the CSV dataset file")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to the output JSON file")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to wait between requests (default: 0.5). Use 0 for no delay.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N records (useful for quick smoke tests).",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"ERROR: CSV file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(run_evaluation(args.csv, args.output, args.delay, args.limit))


if __name__ == "__main__":
    main()
