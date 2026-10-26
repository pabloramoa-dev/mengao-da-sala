"""Vozes de Gil e Dona Cida no motor v3 do Mengão da Sala.

    GIL       = Kokoro pm_alex (principal), Edge AntonioNeural (reserva).
    DONA CIDA = Edge FranciscaNeural (principal), Kokoro pf_dora (reserva).

O Edge TTS usa um serviço não oficial e pode ficar indisponível. A escolha é
independente por personagem: falha na Dona Cida não troca a voz do Gil.
Para cada fala existe um fallback explícito, sem alterar os personagens.

Emoção por fala no Edge: velocidade e tom. Kokoro segue speed=1.04.
Aparar silêncios, gerar os segmentos de lip-sync e masterizar para -16,5 LUFS
continua igual ao processo anterior.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

from src.flamengo.render.voz import masterizar

SR = 44100
VOZES = {
    # IDs técnicos herdados: rubro=Gil e primo=Dona Cida.
    # "voz" fica como configuração do Edge (reserva para o Gil).
    "rubro": dict(motor="kokoro", voz_principal="pm_alex",
                  voz="pt-BR-AntonioNeural", rate=-2, reserva="pt-BR-AntonioNeural"),
    "primo": dict(motor="edge", voz="pt-BR-FranciscaNeural",
                  rate=-2, reserva="pf_dora"),
}
# humor -> (ajuste de velocidade em %, ajuste de tom em Hz)
EMOCAO = {"euforico": (8, 6), "indignado": (5, 3), "tenso": (6, 2), "chocado": (3, 8),
          "rindo": (4, 4), "debochado": (-5, -3), "sofrendo": (-8, -5), "neutra": (0, 0)}
GAP_TROCA, GAP_MESMO, GAP_PERGUNTA = 0.12, 0.22, 0.38


def parametros(quem: str, humor: str) -> tuple[str, str, str]:
    cfg = VOZES.get(quem, VOZES["rubro"])
    dr, dp = EMOCAO.get(humor, (0, 0))
    return cfg["voz"], f"{cfg['rate'] + dr:+d}%", f"{dp:+d}Hz"


def voz_chave(voz: str, rate: str, pitch: str, texto: str) -> str:
    return hashlib.sha1(f"{voz}|{rate}|{pitch}|{texto}".encode("utf-8")).hexdigest()[:16]


def _cache_dir() -> Path:
    d = Path(os.environ.get("FLAMENGO_VOZ_CACHE", Path.home() / ".cache" / "flamengo_vozes"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def edge_mp3(texto: str, voz: str, rate: str, pitch: str) -> Path:
    """MP3 da fala (do cache ou do Edge TTS)."""
    alvo = _cache_dir() / f"{voz_chave(voz, rate, pitch, texto)}.mp3"
    if alvo.exists() and alvo.stat().st_size > 1000:
        return alvo
    import edge_tts

    async def _gerar():
        await edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch).save(str(alvo))
    erro = None
    for tentativa in range(3):
        try:
            asyncio.run(_gerar())
            if alvo.stat().st_size > 1000:
                return alvo
        except Exception as exc:          # rede, 403, mudança no serviço
            erro = exc
            time.sleep(2 * (tentativa + 1))
    raise RuntimeError(f"Edge TTS falhou: {erro}")


def _ler(caminho, aparar=True) -> np.ndarray:
    """Qualquer áudio -> mono float32 44,1 kHz, com o silêncio das pontas aparado."""
    import soundfile as sf
    filtro = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
              "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse"
              if aparar else "anull")
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(caminho), "-af", filtro,
                        "-ar", str(SR), "-ac", "1", out], check=True)
        s, _ = sf.read(out, dtype="float32")
    return s


def _kokoro(texto, voz):
    from kokoro_onnx import Kokoro
    from src.flamengo.render.kokoro import garantir_modelo
    import soundfile as sf
    if not hasattr(_kokoro, "k"):
        _kokoro.k = Kokoro(*garantir_modelo())
    s, sr = _kokoro.k.create(texto, voice=voz, speed=1.04, lang="pt-br")
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "k.wav")
        sf.write(a, s, sr)
        return _ler(a)


def narrar(batidas: list[dict], trabalho: Path, raiz: Path) -> dict:
    """Mesma interface do voz.narrar(): narracao.wav, narracao_master.wav, segs, lip."""
    import soundfile as sf
    trabalho.mkdir(parents=True, exist_ok=True)
    falas = []
    for b in batidas:
        quem = b.get("personagem", "rubro")
        voz, rate, pitch = parametros(quem, b.get("humor", "neutra"))
        falas.append((quem, voz, rate, pitch, b["fala"]))
    audios, motores = [], []
    for quem, voz_edge, rate, pitch, texto in falas:
        cfg = VOZES.get(quem, VOZES["rubro"])
        if cfg["motor"] == "kokoro":
            # Gil: Kokoro pm_alex sempre antes de qualquer tentativa do Edge.
            try:
                audio = _kokoro(texto, cfg["voz_principal"])
                usado = "kokoro"
            except Exception as exc:
                print(f"[voz] Kokoro indisponível para Gil ({exc}); usando Edge reserva",
                      file=sys.stderr)
                audio = _ler(edge_mp3(texto, voz_edge, rate, pitch))
                usado = "edge"
        else:
            # Dona Cida: Edge Francisca, sem alteração no timbre principal.
            try:
                audio = _ler(edge_mp3(texto, voz_edge, rate, pitch))
                usado = "edge"
            except Exception as exc:
                print(f"[voz] Edge indisponível para Dona Cida ({exc}); usando Kokoro reserva",
                      file=sys.stderr)
                audio = _kokoro(texto, cfg["reserva"])
                usado = "kokoro"
        audios.append(audio)
        motores.append(usado)
    motor = motores[0] if len(set(motores)) == 1 else "misto"

    buf, segs, t = [], [], 0.0
    for i, (b, s) in enumerate(zip(batidas, audios)):
        quem = b.get("personagem", "rubro")
        prox = batidas[i + 1] if i + 1 < len(batidas) else None
        if prox is None:
            gap = 0.3
        elif prox.get("tipo") in ("pergunta", "cta"):
            gap = GAP_PERGUNTA
        else:
            gap = GAP_TROCA if prox.get("personagem", "rubro") != quem else GAP_MESMO
        ini = t
        buf += [s, np.zeros(int(gap * SR), dtype=np.float32)]
        t += len(s) / SR
        segs.append({"i": i, "texto": b["fala"], "quem": quem, "ini": round(ini, 3),
                     "fim_fala": round(t, 3), "fim": round(t + gap, 3)})
        t += gap
        print(f"[voz] {i} {quem:5s} {len(s)/SR:5.2f}s  {b['fala']}", file=sys.stderr)
    voz = np.concatenate(buf)
    voz = voz / (float(np.abs(voz).max()) or 1.0) * 0.97
    narr = trabalho / "narracao.wav"
    sf.write(narr, voz, SR, subtype="PCM_16")
    lip = trabalho / "lip.json"
    subprocess.run([sys.executable, "-m", "src.flamengo.render.amplitude", str(narr), str(lip), "--fps", "22"],
                   check=True, cwd=raiz)
    master = masterizar(narr, trabalho / "narracao_master.wav")
    (trabalho / "segs.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"narracao": narr, "master": master, "segs": segs, "lip": lip, "motor_voz": motor}
