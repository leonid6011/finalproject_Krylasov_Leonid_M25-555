# valutatrade_hub/parser_service/storage.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class RatesStorage:
    """
    Хранилище кэша котировок.
    """
    data_dir: Path
    filename: str = "rates.json"

    def __post_init__(self) -> None:
        self.data_dir = Path(self.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / self.filename

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"pairs": {}, "last_refresh": None}

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            #если файл битый считаем что кэш пуст
            return {"pairs": {}, "last_refresh": None}

        if not isinstance(data, dict):
            return {"pairs": {}, "last_refresh": None}

        pairs = data.get("pairs") or {}
        last_refresh = data.get("last_refresh")

        if not isinstance(pairs, dict):
            pairs = {}

        return {"pairs": pairs, "last_refresh": last_refresh}

    def save(self, data: Dict[str, Any]) -> None:
        """
        Сохраняет данные в rates.json с записью.
        """
        pairs = data.get("pairs") if isinstance(data.get("pairs"), dict) else {}
        out = {
            "pairs": pairs,
            "last_refresh": data.get("last_refresh"),
        }
        
        tmp_path = self.path.with_suffix('.tmp')
        tmp_path.write_text(json.dumps(out, ensure_ascii=False, 
                                       indent=2), encoding="utf-8")
        tmp_path.rename(self.path)

    @staticmethod
    def _is_newer(a: str | None, b: str | None) -> bool:
        if a and not b:
            return True
        if not a:
            return False
        return a > (b or "")

    def upsert_pairs(
        self,
        new_pairs: Dict[str, Dict[str, Any]],
        *,
        last_refresh: str,
    ) -> int:
        """
        Добавляем или обновляем пары
        """
        cache = self.load()
        pairs: Dict[str, Dict[str, Any]] = cache.get("pairs", {}) or {}

        updated = 0
        for pair, payload in new_pairs.items():
            if not isinstance(payload, dict):
                continue
            cur = pairs.get(pair) or {}
            cur_updated_at = cur.get("updated_at")
            new_updated_at = payload.get("updated_at")
            if self._is_newer(new_updated_at, cur_updated_at):
                pairs[pair] = payload
                updated += 1

        self.save({"pairs": pairs, "last_refresh": last_refresh})
        return updated

    def append_to_history(self, entries: list[Dict[str, Any]]) -> None:
        """
        Добавляет записи в файл истории exchange_rates.json.
        """
        if not entries:
            return
        
        history_path = self.data_dir / "exchange_rates.json"
        
        history = []
        if history_path.exists():
            try:
                content = history_path.read_text(encoding="utf-8")
                if content.strip():
                    history = json.loads(content)
                    if not isinstance(history, list):
                        history = []
            except (json.JSONDecodeError, Exception):
                history = []
                
        history.extend(entries)
        
        tmp_path = history_path.with_suffix('.tmp')
        tmp_path.write_text(
            json.dumps(history, ensure_ascii=False, indent=2), 
            encoding="utf-8"
        )
        tmp_path.rename(history_path)
