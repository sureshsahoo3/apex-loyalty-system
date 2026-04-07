"""Apex Loyalty System — FastAPI backend."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from logger import get_logger
from agents import orchestration_agent, scoring_agent

log = get_logger("API")

app = FastAPI(title="Apex Loyalty — AI Agent Pipeline", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:4201"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    log.info("REQUEST   %s %s", request.method, request.url.path)
    response = await call_next(request)
    elapsed = (time.perf_counter() - t0) * 1000
    log.info("RESPONSE  %s %s  ->  %d  (%.0fms)",
             request.method, request.url.path, response.status_code, elapsed)
    return response


@app.get("/health")
def health():
    log.debug("Health check OK")
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/high-risk-customers")
def high_risk_customers():
    """
    Full two-agent pipeline:
      1. OrchestrationAgent — consolidates all data sources
      2. ScoringAgent       — applies scoring rules, returns high-risk customers
    """
    log.info("Pipeline triggered: OrchestrationAgent -> ScoringAgent")
    t0 = time.perf_counter()

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        agent_mode = "Claude AI" if api_key else "Rule Engine"
        log.info("Agent mode: %s", agent_mode)

        # ── Step 1: OrchestrationAgent ────────────────────────────────
        log.info("STEP 1/2  OrchestrationAgent starting")
        t1 = time.perf_counter()
        consolidated = orchestration_agent.run(api_key=api_key)
        log.info("STEP 1/2  OrchestrationAgent done in %.2fs — %d total customers",
                 time.perf_counter() - t1, consolidated.get("total_customers", 0))

        # ── Step 2: ScoringAgent ──────────────────────────────────────
        log.info("STEP 2/2  ScoringAgent starting")
        t2 = time.perf_counter()
        scoring_result = scoring_agent.run(consolidated, api_key=api_key)
        customers = scoring_result["customers"]
        log.info("STEP 2/2  ScoringAgent done in %.2fs — %d high-risk customers identified",
                 time.perf_counter() - t2, len(customers))

        log.info(
            "Pipeline complete in %.2fs  |  High-risk: %d  (Critical: %d  High: %d  Medium: %d)",
            time.perf_counter() - t0,
            len(customers),
            sum(1 for c in customers if c["risk_level"] == "critical"),
            sum(1 for c in customers if c["risk_level"] == "high"),
            sum(1 for c in customers if c["risk_level"] == "medium"),
        )

        return {
            "customers":              customers,
            "summary":                scoring_result["summary"],
            "orchestration_summary":  consolidated.get("agent_summary", ""),
            "agent_mode":             scoring_result["agent_mode"],
            "total_sources":          consolidated.get("total_customers", 0),
        }

    except Exception as e:
        log.exception("Pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
