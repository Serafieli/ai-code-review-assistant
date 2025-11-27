from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import traceback

from config import WEBHOOK_SECRET, STORE_LIMIT
from gitlab_client import gitlab
from llm_client import analyze_diff
from review_store import store


# ------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------
app = FastAPI(title="AI Code Review Assistant Dashboard")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ------------------------------------------------------
# DASHBOARD (список всех отчётов)
# ------------------------------------------------------
@app.get("/")
async def dashboard(request: Request):
    reviews = store.get_all()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "reviews": reviews}
    )


# ------------------------------------------------------
# ОТЧЁТ ПО ID
# ------------------------------------------------------
@app.get("/review/{review_id}")
async def review_page(request: Request, review_id: int):
    item = store.get_by_id(review_id)

    if not item:
        return JSONResponse({"error": "review not found"}, status_code=404)

    return templates.TemplateResponse(
        "report.html",
        {"request": request, "item": item}
    )


# ------------------------------------------------------
# HEALTHCHECK
# ------------------------------------------------------
@app.get("/ping")
async def ping():
    return {"status": "ok", "service": "ai-code-review-assistant"}


# ------------------------------------------------------
# Очистка всех ревью (для тестов)
# ------------------------------------------------------
@app.post("/clear")
async def clear_reviews():
    store.clear()
    return {"status": "cleared"}


# ------------------------------------------------------
# GITLAB WEBHOOK
# ------------------------------------------------------
@app.post("/gitlab/webhook")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str | None = Header(None, alias="X-Gitlab-Token")
):

    # ---------- Проверка секрета ----------
    if x_gitlab_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    payload = await request.json()
    event = payload.get("object_kind")

    print("\n========== WEBHOOK RECEIVED ==========")
    print(json.dumps(payload, indent=2))

    # ---------- Работает только с MR ----------
    if event != "merge_request":
        print("Ignored: not MR event")
        return {"status": "ignored"}

    obj = payload["object_attributes"]
    action = obj["action"]
    project_id = payload["project"]["id"]
    mr_iid = obj["iid"]
    description = obj.get("description", "") or ""

    print(f"[MR] action={action}, project={project_id}, iid={mr_iid}")

    # ---------- Блокируем бесконечные циклы ----------
    # GitLab вызывает update при смене labels → пропускаем
    allowed_actions = {"open", "reopen"}

    if action not in allowed_actions:
        print(f"Ignored: action '{action}' not allowed")
        return {"status": "ignored"}

    # ------------------------------------------------------
    # ПОЛУЧАЕМ DIFF
    # ------------------------------------------------------
    changes = await gitlab.get_merge_request_diff(project_id, mr_iid)

    diff_text = ""
    for c in changes:
        old_p = c.get("old_path", "")
        new_p = c.get("new_path", "")
        diff = c.get("diff", "")

        diff_text += f"""
=== FILE CHANGE ===
Old: {old_p}
New: {new_p}

{diff}

"""

    if not diff_text.strip():
        print("Ignored: empty diff")
        return {"status": "ignored", "reason": "empty diff"}

    # ------------------------------------------------------
    # ОТПРАВЛЯЕМ В OpenAI
    # ------------------------------------------------------
    print("----------- SENDING DIFF TO OPENAI -----------")

    try:
        ai_raw = await analyze_diff(diff_text, description)
    except Exception as e:
        print("❌ OpenAI error:", e)
        traceback.print_exc()
        return {"status": "error", "stage": "openai"}

    # JSON FIX
    try:
        ai = json.loads(ai_raw)
    except Exception:
        print("❌ Could not parse AI JSON, raw:")
        print(ai_raw)
        traceback.print_exc()
        return {"status": "error", "stage": "json_parse", "raw": ai_raw}

    print("----------- AI REVIEW RESULT -----------")
    print(json.dumps(ai, indent=4, ensure_ascii=False))

    # ------------------------------------------------------
    # ФОРМИРУЕМ COMMENT
    # ------------------------------------------------------
    findings_md = ""

    for f in ai.get("findings", []):
        findings_md += f"""
### {f['severity'].upper()} — {f['type']}
**File:** `{f['file']}`  
**Line:** {f['line']}  
**Issue:** {f['message']}  
**Recommendation:** {f['recommendation']}
"""

    if not findings_md.strip():
        findings_md = "No critical issues found."

    comment = f"""
## 🤖 AI Code Review Report

### 📝 Summary
{ai.get('summary','')}

### 🔍 Functional correctness
{ai.get('functional_correctness','')}

### ⚠ Findings
{findings_md}

### 🏁 Verdict
**`{ai.get('verdict','')}`**

### 🏷 Labels
{", ".join(ai.get("labels", []))}
"""

    # ------------------------------------------------------
    # ОТПРАВЛЯЕМ КОММЕНТ
    # ------------------------------------------------------
    try:
        await gitlab.post_comment(project_id, mr_iid, comment)
    except Exception:
        print("❌ Failed to post comment")
        traceback.print_exc()

    # ------------------------------------------------------
    # СТАВИМ ЛЕЙБЛЫ (если есть)
    # ------------------------------------------------------
    labels = ai.get("labels") or []

    if isinstance(labels, list) and len(labels) > 0:
        try:
            await gitlab.set_labels(project_id, mr_iid, labels)
        except Exception:
            print("❌ Failed to set labels")
            traceback.print_exc()

    # ------------------------------------------------------
    # СОХРАНЯЕМ ОТЧЁТ
    # ------------------------------------------------------
    store.add_review(project_id, mr_iid, ai)

    # enforce storage limit
    store.enforce_limit(STORE_LIMIT)

    # ------------------------------------------------------
    # АВТО-АПРУВ
    # ------------------------------------------------------
    if ai.get("verdict") == "ready-for-merge":
        try:
            await gitlab.approve_mr(project_id, mr_iid)
        except Exception:
            print("❌ Failed to approve MR")

    return {"status": "done", "verdict": ai.get("verdict")}
