"""Voz do torcedor = voz do Bira do Tempo (@previsaorj), sem nenhuma mudança.

Preset copiado de previsao-rj/src/previsao_rj/render/characters/pipeline.py:
    'bira': {'voice': 'pm_alex', 'pitch': 1.0, 'speed': 1.04, 'gap': 0.22}
Filtro do Bira (o mesmo do pipeline dele, sem pitch/vibrato):
    highpass=f=80,acompressor=threshold=-18dB:ratio=2:attack=8:release=180,volume=1.1
Masterização Vox: mede LUFS, aplica ganho FIXO e alimiter, alvo -16,5 LUFS.
Nada de loudnorm no caminho do sinal (faz a voz estalar).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PRESET_BIRA = {"voice": "pm_alex", "pitch": 1.0, "speed": 1.04, "gap": 0.22}
FILTRO_BIRA = ("highpass=f=80,acompressor=threshold=-18dB:ratio=2:"
               "attack=8:release=180,volume=1.1")
PACOTE = "src.flamengo.render"


def _run(cmd, cwd):
    subprocess.run([str(c) for c in cmd], check=True, cwd=cwd)


def medir_lufs(arquivo) -> float | None:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(arquivo), "-af", "ebur128",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def masterizar(entrada, saida, alvo=-16.5, teto=18.0):
    lufs = medir_lufs(entrada)
    ganho = 0.0 if lufs is None else max(-teto, min(teto, alvo - lufs))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(entrada), "-af",
                    f"volume={ganho:.2f}dB,alimiter=limit=0.89:level=disabled",
                    "-ar", "48000", "-ac", "1", str(saida)], check=True)
    return saida


def narrar(batidas: list[dict], trabalho: Path, raiz: Path) -> dict:
    """Gera narracao.wav (filtro Bira), narracao_master.wav, segs.json e lip.json."""
    trabalho.mkdir(parents=True, exist_ok=True)
    roteiro = trabalho / "roteiro.txt"
    roteiro.write_text("\n".join(b["fala"] for b in batidas), encoding="utf-8")
    bruto, narr = trabalho / "raw.wav", trabalho / "narracao.wav"
    master, segs, lip = trabalho / "narracao_master.wav", trabalho / "segs.json", trabalho / "lip.json"

    p = PRESET_BIRA
    _run([sys.executable, "-m", f"{PACOTE}.kokoro", roteiro, "--voz", p["voice"],
          "--speed", p["speed"], "--gap", p["gap"], "--out", bruto, "--seg-json", segs], raiz)
    _run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-af", FILTRO_BIRA,
          "-ar", "44100", "-ac", "1", narr], raiz)
    _run([sys.executable, "-m", f"{PACOTE}.amplitude", narr, lip, "--fps", "22"], raiz)
    masterizar(narr, master)
    return {"narracao": narr, "master": master, "segs": json.loads(segs.read_text()),
            "lip": lip}
