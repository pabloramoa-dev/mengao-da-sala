"""Vozes da dupla — Edge TTS (vozes neurais da Microsoft), escolhidas de ouvido.

Pablo ouviu 6 candidatos no workflow "Teste de vozes" (28/09/2026) e escolheu
a opção 2. O Kokoro ficou robótico demais para diálogo.

    JUNINHO       = pt-BR-AntonioNeural, 6% mais rápido
    PRIMO SECADOR = en-US-AndrewMultilingualNeural falando português, 4% mais
                    lento (a pontinha de sotaque combina com o "secador")

Edge TTS (github.com/rany2/edge-tts) usa o serviço de leitura do navegador
Edge: não pede chave, mas depende de internet e é uso não oficial. Por isso:
  * cada fala tenta 3 vezes;
  * se o Edge cair, a esquete sai com o Kokoro (voz antiga) em vez de não sair;
  * CACHE por fala ($FLAMENGO_VOZ_CACHE): o mesmo texto com a mesma voz nunca
    é pedido duas vezes. A chave é voz_chave() — tools/vozes_cache.py usa a
    mesma fórmula para gerar áudio fora daqui.

Emoção por fala: o humor mexe na VELOCIDADE e um pouco no TOM de cada fala
(eufórico acelera e sobe, sofrendo arrasta e desce). Silêncio do começo/fim de
cada fala é aparado para a conversa ficar ágil. Masterização Vox igual aos
outros canais (ganho fixo + limitador, alvo -16,5 LUFS, sem loudnorm).
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
    "rubro": dict(voz="pt-BR-AntonioNeural", rate=6, reserva="pm_alex"),
    "primo": dict(voz="en-US-AndrewMultilingualNeural", rate=-4, reserva="pm_santa"),
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
    motor = "edge"
    falas = []
    for b in batidas:
        quem = b.get("personagem", "rubro")
        voz, rate, pitch = parametros(quem, b.get("humor", "neutra"))
        falas.append((quem, voz, rate, pitch, b["fala"]))
    try:
        audios = [_ler(edge_mp3(t, v, r, p)) for _q, v, r, p, t in falas]
    except Exception as exc:
        # sem Edge, a esquete sai com a voz antiga — melhor que o dia ficar sem post
        print(f"[voz] Edge TTS indisponível ({exc}); usando Kokoro", file=sys.stderr)
        motor = "kokoro"
        audios = [_kokoro(t, VOZES.get(q, VOZES["rubro"])["reserva"]) for q, _v, _r, _p, t in falas]

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
