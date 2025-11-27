# 🤖 AI Code Review Assistant – Автоматический AI-ревьюер для GitLab

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/OpenAI_API-Enabled-412991?style=for-the-badge&logo=openai">
  <img src="https://img.shields.io/badge/GitLab-Hooks_Friendly-FC6D26?style=for-the-badge&logo=gitlab">
  <br>
  <img src="https://img.shields.io/badge/Status-Production_ready-brightgreen?style=for-the-badge">
</p>

<p align="center">
  <strong>AI-ассистент, который автоматически проверяет код в GitLab, анализирует diff, ищет ошибки и оставляет профессиональные комментарии.</strong><br>
  Полная автоматизация рутинных code review задач → экономия времени → повышение качества кода.
</p>

---

## ✨ Основные возможности

### ✔ Мгновенный анализ Merge Request
- Авто-запуск при `open`, `reopen`
- Умная защита от GitLab label-update циклов
- Анализируются только DIFF-изменения

### ✔ AI-проверка качества кода
Ассистент определяет:
- логические ошибки
- архитектурные нарушения
- performance-проблемы
- security-риски
- style/code-smell
- корректность функционала

### ✔ Профессиональные AI-комментарии внутри MR
AI оставляет структурированный Markdown-отчёт:
- Summary
- Functional correctness
- Findings
- Recommendations
- Verdict
- Labels

### ✔ Автоматическое выставление Labels
Поддерживаются:
- ready-for-merge
- needs-fixes
- security
- urgent

### ✔ Auto-Approve MR
Если AI считает MR качественным — система делает approve.

### ✔ Встроенный веб-интерфейс (Dashboard + Reports)
Панель отображает:
- список всех ревью
- вердикт
- метки
- подробный отчёт

---

## 📁 Структура проекта

```
ai-code-review-assistant/
│── main.py
│── gitlab_client.py
│── llm_client.py
│── review_store.py
│── config.py
│── templates/
│     ├── dashboard.html
│     └── report.html
│── static/
│     └── style.css
│── requirements.txt
└── .env
```

---

## ⚙️ Установка

### 1. Установить зависимости
```
pip install -r requirements.txt
```

### 2. Создать .env
```
OPENAI_API_KEY=your_key
GITLAB_TOKEN=your_token
GITLAB_BASE_URL=https://gitlab.com
WEBHOOK_SECRET=your_secret
STORE_LIMIT=100
```

### 3. Запуск
```
uvicorn main:app --reload --port 8000
```

---

## 🔗 GitLab Webhook
URL:
```
https://your-server/gitlab/webhook
```
Секрет:
```
WEBHOOK_SECRET
```

Выбрать событие:
```
✓ Merge Request Hook
```

---

## ❤️ Автор
Разработчик: Братуха (serafiel)
Проект создан для ForteBank AI Hackathon

---

## 📄 Лицензия
MIT License
