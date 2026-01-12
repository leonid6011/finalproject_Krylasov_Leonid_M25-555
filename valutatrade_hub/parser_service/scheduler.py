from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

from .updater import RatesUpdater


@dataclass
class RatesScheduler:
    updater: RatesUpdater
    interval_seconds: int = 3600  # 1 час

    _thread: Optional[threading.Thread] = None
    _stop: threading.Event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.updater.run_update()
            except Exception:
                # в проде логируем, но не валим поток
                pass
            for _ in range(self.interval_seconds):
                if self._stop.is_set():
                    return
                time.sleep(1)
