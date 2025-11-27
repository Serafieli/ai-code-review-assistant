import json
import re
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------------------------------------------
# JSON FIXER — автоматическая починка сломанного JSON от модели
# -------------------------------------------------------------
def try_fix_json(bad_json: str):
    """
    Попытка автоматической починки JSON.
    Убирает мусор, правит кавычки, удаляет лишние запятые.
    """

    cleaned = bad_json.strip()

    # убираем ```json блоки
    cleaned = re.sub(r"^```json", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = cleaned.replace("```", "").strip()

    # убираем текст до первой {
    if "{" in cleaned:
        cleaned = cleaned[cleaned.index("{"):]

    # убираем текст после последней }
    if cleaned.count("}") > 0:
        cleaned = cleaned[: cleaned.rfind("}") + 1]

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # базовые замены
    cleaned = cleaned.replace("\n", " ")

    # удаляем trailing запятые
    cleaned = re.sub(r",\s*}", "}", cleaned)
    cleaned = re.sub(r",\s*]", "]", cleaned)

    # замена одинарных кавычек
    cleaned = cleaned.replace("'", '"')

    try:
        return json.loads(cleaned)
    except Exception:
        return None


# -------------------------------------------------------------
# LLM DIFF ANALYZER (CORE)
# -------------------------------------------------------------
async def analyze_diff(diff_text: str, description: str = "") -> str:
    """
    Отправляет DIFF + DESCRIPTION в OpenAI.
    Возвращает строго JSON (str).
    """

    prompt = f"""
Ты — Senior Software Engineer, эксперт в code review.

Проанализируй изменения в Merge Request.

=== CONTEXT (MR DESCRIPTION) ===
{description}

=== DIFF ===
{diff_text}

Проанализируй:

1. summary — краткое резюме MR
2. functional_correctness — корректность реализации относительно описания
3. findings — список найденных проблем в формате:
   [
     {{
       "type": "security" | "style" | "architecture" | "logic" | "performance",
       "severity": "critical" | "high" | "medium" | "low",
       "file": "имя файла",
       "line": номер строки или 0,
       "message": "описание проблемы",
       "recommendation": "как исправить"
     }}
   ]
4. verdict:
   - "ready-for-merge"
   - "needs-fixes"
5. labels:
   - ["ready-for-merge"]
   - ["needs-fixes"]
   - можно добавлять "security", "refactor", "urgent"

Верни строго JSON БЕЗ текста вокруг.
Формат:
{{
  "summary": "",
  "functional_correctness": "",
  "findings": [],
  "verdict": "",
  "labels": []
}}
"""

    # ---------------------------------------------------------
    # ИСПРАВЛЕННЫЙ ВЫЗОВ НОВОГО API
    # ---------------------------------------------------------
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": "Ты строгий опытный инженер. Всегда отвечай строго JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_output_tokens=2048,
        temperature=0.2,
    )

    raw = response.output_text.strip()

    # ----------------------------------------
    # Если JSON валидный — отдаем сразу
    # ----------------------------------------
    try:
        json.loads(raw)
        return raw
    except Exception:
        pass

    # ----------------------------------------
    # Пытаемся автоматически починить JSON
    # ----------------------------------------
    fixed = try_fix_json(raw)

    if fixed:
        return json.dumps(fixed, ensure_ascii=False)

    # ----------------------------------------
    # Если ничего не помогло — возвращаем safe JSON
    # ----------------------------------------
    safe_result = {
        "summary": "AI response parsing failed",
        "functional_correctness": "",
        "findings": [],
        "verdict": "needs-fixes",
        "labels": ["needs-fixes"]
    }

    return json.dumps(safe_result, ensure_ascii=False)
