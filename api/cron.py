import os
from fastapi import FastAPI, Request, HTTPException

from storage.redis_client import pop_job, get_queue_length
from services.pipeline import process_job

app = FastAPI()


def _extract_bearer_token(request: Request) -> str:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        return ""
    parts = auth.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return auth.strip()


def _check_cron_auth(request: Request):
    expected = os.environ.get("CRON_SECRET", "")
    if not expected:
        # Явно падаем, чтобы не было «случайно открытого» воркера.
        raise HTTPException(status_code=500, detail="CRON_SECRET is not configured")

    got = _extract_bearer_token(request)
    if got != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/api/cron")
async def cron_health_check():
    return {"status": "active", "queue_length": get_queue_length()}


@app.post("/api/cron")
async def cron_worker(request: Request):
    """Vercel Cron worker: достает 1 job из Redis и обрабатывает."""
    _check_cron_auth(request)

    job = pop_job()
    if not job:
        return {"ok": True, "processed": False, "queue_length": get_queue_length()}

    await process_job(job)
    return {"ok": True, "processed": True, "step": job.get("step"), "queue_length": get_queue_length()}
