"""Utilities for reporting progress of the comissão calculation job.

This module is imported by ``calculo_comissoes.py`` at runtime.  It is isolated
from the rest of the codebase so the calculation logic itself remains
unchanged; we merely emit progress updates and timing information to the JSON
file already consumed by the FastAPI adapter.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime
from threading import Lock
from time import perf_counter
from typing import Optional


class ProgressTracker:
    """Lightweight helper to update ``progress.json`` safely.

    The tracker keeps the logical unit of progress (percent, etapa, status and
    short log messages).  It never alters the calculation logic—it only writes
    metadata for the frontend to display.
    """

    def __init__(
        self,
        job_id: str,
        progress_file: str,
        max_messages: int = 20,
    ) -> None:
        self.job_id = job_id
        self.progress_file = progress_file
        self.max_messages = max_messages
        self._lock = Lock()

    # ------------------------------------------------------------------ utils
    def _ensure_dir(self) -> None:
        directory = os.path.dirname(self.progress_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def _read(self) -> dict:
        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("job_id") != self.job_id:
                raise ValueError("progress file belongs to a different job")
        except Exception:
            data = {
                "job_id": self.job_id,
                "percent": 0.0,
                "etapa": "",
                "mensagens": [],
                "status": "em_andamento",
            }
        return data

    def _write(self, data: dict) -> None:
        self._ensure_dir()
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    # ----------------------------------------------------------------- actions
    def start(self, etapa: str = "Iniciando...") -> None:
        with self._lock:
            self._write(
                {
                    "job_id": self.job_id,
                    "percent": 0.0,
                    "etapa": etapa,
                    "mensagens": [],
                    "status": "em_andamento",
                }
            )

    def update(
        self,
        etapa: Optional[str] = None,
        *,
        add_percent: float = 0.0,
        absolute_percent: Optional[float] = None,
        message: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        with self._lock:
            data = self._read()
            if absolute_percent is not None:
                data["percent"] = max(0.0, min(100.0, float(absolute_percent)))
            else:
                data["percent"] = max(
                    0.0,
                    min(100.0, float(data.get("percent", 0.0)) + float(add_percent)),
                )

            if etapa is not None:
                data["etapa"] = etapa

            if message:
                mensagens = list(data.get("mensagens", []))
                timestamp = datetime.now().strftime("%H:%M:%S")
                mensagens.append(f"[{timestamp}] {message}")
                data["mensagens"] = mensagens[-self.max_messages :]

            if status is not None:
                data["status"] = status
            elif data.get("status") not in ("concluido", "erro"):
                data["status"] = "em_andamento"

            self._write(data)

    def finish(self, success: bool, message: Optional[str] = None) -> None:
        etapa = "Concluído" if success else "Erro"
        status = "concluido" if success else "erro"
        self.update(
            etapa=etapa,
            absolute_percent=100.0,
            message=message,
            status=status,
        )


@contextmanager
def step_timer(tracker: Optional[ProgressTracker], etapa: str, weight: float):
    """Context manager que mede tempo e publica logs/percentual.

    ``weight`` representa o quanto aquela etapa contribui para o progresso
    total (em pontos percentuais).  Caso o tracker não esteja configurado, o
    bloco simplesmente executa sem efeitos colaterais.
    """

    if tracker is None:
        yield
        return

    tracker.update(etapa=f"{etapa}...", message=f"Iniciando {etapa}")
    inicio = perf_counter()
    try:
        yield
    except Exception as exc:  # repropaga após registrar
        tracker.update(
            etapa=f"Erro em {etapa}",
            message=f"[ERRO] {etapa}: {exc}",
            status="erro",
        )
        raise
    else:
        elapsed_ms = (perf_counter() - inicio) * 1000.0
        tracker.update(
            etapa=f"{etapa} concluída",
            add_percent=weight,
            message=f"[{etapa}] tempo={elapsed_ms:.0f}ms",
        )
