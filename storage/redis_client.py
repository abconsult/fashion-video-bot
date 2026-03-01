import json
import os
from upstash_redis import Redis

_redis = None


def _get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis(
            url=os.environ["UPSTASH_REDIS_REST_URL"],
            token=os.environ["UPSTASH_REDIS_REST_TOKEN"]
        )
    return _redis


# ── FSM State Management ──────────────────────────────────────

def set_state(chat_id: int, state: str, data: dict = None):
    """Сохраняет состояние пользователя в Redis (TTL: 2 часа)."""
    payload = {"state": state, **(data or {})}
    payload.pop("clean_image_b64", None)  # не храним бинарные данные в FSM
    _get_redis().set(f"fsm:{chat_id}", json.dumps(payload), ex=7200)


def get_state(chat_id: int) -> dict:
    """Возвращает текущее состояние пользователя."""
    val = _get_redis().get(f"fsm:{chat_id}")
    if val:
        return json.loads(val) if isinstance(val, str) else val
    return {"state": "IDLE"}


def set_state_data(chat_id: int, key: str, value):
    """Обновляет отдельное поле в состоянии пользователя."""
    state_data = get_state(chat_id)
    state_data[key] = value
    _get_redis().set(f"fsm:{chat_id}", json.dumps(state_data), ex=7200)


def clear_state(chat_id: int):
    """Сбрасывает состояние пользователя."""
    _get_redis().delete(f"fsm:{chat_id}")


# ── Job Queue ─────────────────────────────────────────────────

def push_job(job: dict):
    """Добавляет задание в очередь обработки."""
    clean_job = {k: v for k, v in job.items() if k != "clean_image_b64"}

    # Бинарные данные изображения храним отдельно
    if "clean_image_b64" in job:
        chat_id = job["chat_id"]
        _get_redis().set(f"img_b64:{chat_id}", job["clean_image_b64"], ex=7200)

    _get_redis().rpush("job_queue", json.dumps(clean_job))


def pop_job() -> dict | None:
    """Извлекает следующее задание из очереди."""
    val = _get_redis().lpop("job_queue")
    if not val:
        return None

    job = json.loads(val) if isinstance(val, str) else val

    # Восстанавливаем b64-данные для шага виртуальной примерки
    if job.get("step") == "GENERATING_TRYON":
        chat_id = job.get("chat_id")
        if chat_id:
            b64 = _get_redis().get(f"img_b64:{chat_id}")
            if b64:
                job["clean_image_b64"] = b64

    return job


def get_queue_length() -> int:
    """Возвращает количество заданий в очереди."""
    return _get_redis().llen("job_queue")
