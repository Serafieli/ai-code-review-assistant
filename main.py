from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse

# импорт секрета из конфига
from config import WEBHOOK_SECRET

app = FastAPI(title="AI Code Review Assistant")


@app.get("/ping")
async def ping():
    """
    Проверка, что сервис жив
    """
    return {"status": "ok", "service": "ai-code-review-assistant"}


@app.post("/gitlab/webhook")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str | None = Header(None, alias="X-Gitlab-Token"),
    x_gitlab_event: str | None = Header(None, alias="X-Gitlab-Event")
):
    """
    Приём GitLab вебхука
    """
    # Проверяем секрет
    if x_gitlab_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    payload = await request.json()

    event_type = x_gitlab_event or payload.get("object_kind", "unknown")
    print(f"[WEBHOOK] Event: {event_type}")
    print(f"[WEBHOOK] Payload keys: {list(payload.keys())}")

    return JSONResponse({"status": "received", "event": event_type})
