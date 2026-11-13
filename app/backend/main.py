import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import faults
from db import SessionLocal, get_db, init_db
from models import Idea
from otel import instrument, record_request
from schemas import IdeaCreate, IdeaOut


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create tables (if missing) on startup; nothing to clean up on shutdown."""
    init_db()
    yield


app = FastAPI(title="Idea Board", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
instrument(app, SessionLocal().bind)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Records every request's status/latency for the AI evaluator's canary
    health query (ai/evaluator/metrics.py), labeled by pod_template_hash.

    An unhandled exception (FAULT_MODE=panic) makes call_next raise instead
    of returning - confirmed live, this silently dropped every crashed
    request from the metric ai/routing's hard guard depends on, since the
    500 Starlette eventually returns happens above this middleware. Record
    it as a 500 here too, then re-raise so Starlette's own handling is
    unchanged.
    """
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        record_request(500, (time.perf_counter() - start) * 1000)
        raise
    record_request(response.status_code, (time.perf_counter() - start) * 1000)
    return response


@app.get("/healthz")
def healthz() -> dict:
    """Liveness/readiness probe target. Never subject to fault injection,
    so a misbehaving canary gets caught by traffic analysis, not by
    Kubernetes silently restarting the pod."""
    return {"status": "ok"}


@app.get("/ideas", response_model=list[IdeaOut])
def list_ideas(db: Session = Depends(get_db)) -> list[Idea]:
    """List ideas, newest first."""
    faults.maybe_inject()
    ideas = db.query(Idea).order_by(Idea.created_at.desc()).all()
    faults.simulate_n_plus_one(db, [idea.id for idea in ideas])
    return ideas


@app.post("/ideas", response_model=IdeaOut, status_code=201)
def create_idea(payload: IdeaCreate, db: Session = Depends(get_db)) -> Idea:
    """Create a new idea."""
    faults.maybe_inject()
    idea = Idea(text=payload.text)
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


@app.post("/ideas/{idea_id}/upvote", response_model=IdeaOut)
def upvote_idea(idea_id: int, db: Session = Depends(get_db)) -> Idea:
    """Upvote an idea by id; 404 if it doesn't exist."""
    faults.maybe_inject()
    idea = db.get(Idea, idea_id)
    if idea is None:
        raise HTTPException(status_code=404, detail="idea not found")
    idea.votes += 1
    db.commit()
    db.refresh(idea)
    return idea
