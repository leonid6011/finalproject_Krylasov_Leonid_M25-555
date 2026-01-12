# valutatrade_hub/parser_service/updater.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .api_clients import ApiRequestError, BaseApiClient
from .storage import RatesStorage


def _now_iso_z() -> str:
    """
    Возвращает текущее время в формате ISO 8601 с UTC и суффиксом Z.
    """
    return datetime.now(timezone.utc).replace(microsecond=0)\
        .isoformat().replace("+00:00", "Z")


@dataclass
class RatesUpdater:
    """
    Координатор обновления.
    """
    clients: List[BaseApiClient]
    storage: RatesStorage
    log: callable = print

    def run_update(self, source: Optional[str] = None) -> Dict[str, object]:
        self.log("INFO: Starting rates update...")

        chosen = self.clients
        if source:
            src = source.strip().lower()
            chosen = [c for c in self.clients if c.name.lower() == src]

        last_refresh = _now_iso_z()

        merged_pairs: Dict[str, Dict[str, object]] = {}
        history_entries = []
        errors = 0
        ok_total = 0

        for client in chosen:
            try:
                rates = client.fetch_rates()
                ok_total += len(rates)
                self.log(f"INFO: Fetching from "
                         f"{client.display_name}... OK ({len(rates)} rates)"
                        )

                updated_at = _now_iso_z()
                for pair, rate in rates.items():
                    merged_pairs[pair] = {
                        "rate": float(rate),
                        "updated_at": updated_at,
                        "source": client.display_name,
                    }
                    
                    parts = pair.split("_")
                    if len(parts) == 2:
                        history_entries.append({
                            "id": f"{pair}_{updated_at}",
                            "from_currency": parts[0],
                            "to_currency": parts[1],
                            "rate": float(rate),
                            "timestamp": updated_at,
                            "source": client.display_name,
                        })

            except ApiRequestError as e:
                errors += 1
                self.log(f"ERROR: Failed to fetch from {client.display_name}: {e}")

        self.log(f"INFO: Writing {len(merged_pairs)} rates to data/rates.json...")

        updated_count = self.storage.upsert_pairs(merged_pairs,
                                                   last_refresh=last_refresh)
        
        #записываем историю
        if history_entries:
            self.log(
                f"INFO: Appending {len(history_entries)} "
                "entries to exchange_rates.json..."
            )
            self.storage.append_to_history(history_entries)

        if errors > 0:
            self.log("Update completed with errors. "
                     "Check logs/parser.log for details."
                    )
        else:
            self.log(f"Update successful. Total rates updated: "
                     f"{updated_count}. Last refresh: {last_refresh}"
                    )

        return {
            "updated": updated_count,
            "last_refresh": last_refresh,
            "errors": errors,
        }