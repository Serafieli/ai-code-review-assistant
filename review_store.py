from datetime import datetime
from typing import List, Dict, Any


class ReviewStore:
    """
    Простое in-memory хранилище отчётов.
    Работает как база для Dashboard.
    """
    def __init__(self):
        self.reviews: List[Dict[str, Any]] = []
        self._id_counter = 1  # уникальный ID

    # -----------------------------------------------------------
    # ADD REVIEW
    # -----------------------------------------------------------
    def add_review(self, project_id: int, mr_iid: int, ai: dict):
        """
        ai ожидается в формате:
        {
            "summary": "",
            "functional_correctness": "",
            "findings": [],
            "verdict": "",
            "labels": []
        }
        """

        entry = {
            "id": self._id_counter,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project_id": project_id,
            "mr_iid": mr_iid,
            "summary": ai.get("summary", ""),
            "functional_correctness": ai.get("functional_correctness", ""),
            "findings": ai.get("findings", []),
            "verdict": ai.get("verdict", "unknown"),
            "labels": ai.get("labels", []),
            "raw_ai": ai  # сохраняем исходный JSON на всякий случай
        }

        # Добавляем в начало списка (последние MR — сверху)
        self.reviews.insert(0, entry)

        self._id_counter += 1

    # -----------------------------------------------------------
    # GET ALL
    # -----------------------------------------------------------
    def get_all(self) -> list:
        """
        Возвращает все ревью (последние добавленные — сверху)
        """
        return self.reviews

    # -----------------------------------------------------------
    # GET BY ID
    # -----------------------------------------------------------
    def get_by_id(self, review_id: int):
        """
        Возвращает конкретный отчёт по его ID
        """
        for r in self.reviews:
            if r["id"] == review_id:
                return r
        return None

    # -----------------------------------------------------------
    # CLEAR ALL
    # -----------------------------------------------------------
    def clear(self):
        """Полная очистка базы"""
        self.reviews = []
        self._id_counter = 1

    # -----------------------------------------------------------
    # ENFORCE STORE LIMIT
    # -----------------------------------------------------------
    def enforce_limit(self, limit: int):
        """
        Ограничивает количество записей.
        Если превышено — удаляет старые записи.
        """
        if len(self.reviews) > limit:
            # удаляем всё, что выходит за лимит
            self.reviews = self.reviews[:limit]


# Экземпляр хранилища
store = ReviewStore()
