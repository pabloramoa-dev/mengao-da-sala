"""Teste de vozes do @mengaodasala — o mesmo diálogo em vários motores de voz.

Roda no GitHub Actions (workflow "Teste de vozes"). Nada é publicado no
Instagram: sai um MP3 por candidato, pro Pablo escolher de ouvido.

Candidatos:
  1_kokoro_atual      o que está hoje (Kokoro + filtros) — referência
  2_edge_antonio_andrew   Edge TTS (vozes neurais da Microsoft, sem chave):
                          Juninho = pt-BR-AntonioNeural, Primo = AndrewMultilingual
  3_edge_antonio_duplo    Edge TTS: os dois com o Antonio, primo com tom/ritmo mudados
  4_edge_francisca_bia    Edge TTS: voz feminina (se um dia entrar uma personagem)
  5_chatterbox_pt         Chatterbox Multilingual (Resemble AI, MIT), com EMOÇÃO
                          ajustável por fala, clonando o timbre das vozes do Edge
  6_piper_faber_cadu      Piper pt_BR (faber x cadu), rápido e 100% local
"""
import asyncio
import os
import subprocess
import sys
import traceback
from pathlib import Path

import numpy as np
import soundfile as sf

OUT = Path("saida_vozes")
OUT.mkdir(exist_ok=True)
SR = 24000

DIALOGO = [  # (quem, fala, emoção 0..1 p/ Chatterbox)
    ("primo", "Você prometeu pra tua mãe que hoje ia ver o jogo calmo.", 0.45),
    ("rubro", "E eu tô calmíssimo! Olha a minha respiração: ahhh.", 0.7),
    ("primo", "Primo, a bola nem rolou e você já roeu a unha do pé.", 0.55),
    ("rubro", "É técnica de concentração! O Mengão sente a energia da sala!", 0.85),
    ("primo", "Então manda uma energia pra zaga, que ela tá precisando.", 0.5),
    ("rubro", "Sai da minha sala! Com calma. Mas sai!", 0.95),
    ("rubro", "E você, Nação? Vê o jogo sentado ou vira treinador em pé na sala? Comenta aí!", 0.75),
]


def pausa(s=0.18):
    return np.zeros(int(SR * s), dtype=np.float32)


def ler(caminho):
    """Qualquer áudio -> mono float32 24 kHz (via ffmpeg)."""
    tmp = str(caminho) + ".24k.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(caminho), "-ar", str(SR), "-ac", "1", tmp], check=True)
    s, _ = sf.read(tmp, dtype="float32")
    return s


def salvar(nome, partes):
    voz = np.concatenate([np.concatenate([p, pausa()]) for p in partes])
    voz = voz / (np.abs(voz).max() or 1) * 0.95
    wav = OUT / f"{nome}.wav"
    sf.write(wav, voz, SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-b:a", "128k", str(OUT / f"{nome}.mp3")], check=True)
    wav.unlink()
    print(f"[ok] {nome}.mp3  {len(voz)/SR:.1f}s")


def candidato(nome):
    def deco(fn):
        def rodar():
            try:
                fn(nome)
            except Exception:
                print(f"[FALHOU] {nome}")
                traceback.print_exc()
        return rodar
    return deco


# ---------------------------------------------------------------- Edge TTS
async def _edge(texto, voz, arq, rate="+0%", pitch="+0Hz"):
    import edge_tts
    await edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch).save(arq)


def edge(texto, voz, rate="+0%", pitch="+0Hz", tag="x"):
    arq = OUT / f"_tmp_{abs(hash((texto, voz, rate, pitch)))}.mp3"
    asyncio.run(_edge(texto, voz, str(arq), rate, pitch))
    s = ler(arq)
    arq.unlink()
    return s


EDGE = {
    "2_edge_antonio_andrew": {"rubro": ("pt-BR-AntonioNeural", "+6%", "+0Hz"),
                              "primo": ("en-US-AndrewMultilingualNeural", "-4%", "+0Hz")},
    "3_edge_antonio_duplo": {"rubro": ("pt-BR-AntonioNeural", "+8%", "-4Hz"),
                             "primo": ("pt-BR-AntonioNeural", "-6%", "+14Hz")},
    "4_edge_francisca_bia": {"rubro": ("pt-BR-AntonioNeural", "+6%", "+0Hz"),
                             "primo": ("pt-BR-FranciscaNeural", "+0%", "+0Hz")},
}


def rodar_edge():
    for nome, cfg in EDGE.items():
        @candidato(nome)
        def _(n, cfg=cfg):
            salvar(n, [edge(f, *cfg[q]) for q, f, _e in DIALOGO])
        _()


# ---------------------------------------------------------------- Kokoro (atual)
@candidato("1_kokoro_atual")
def kokoro(nome):
    sys.path.insert(0, ".")
    from kokoro_onnx import Kokoro
    from src.flamengo.render.kokoro import garantir_modelo
    k = Kokoro(*garantir_modelo())
    partes = []
    for q, f, _e in DIALOGO:
        voz = "pm_alex" if q == "rubro" else "pm_santa"
        s, sr = k.create(f, voice=voz, speed=1.04, lang="pt-br")
        tmp = OUT / "_k.wav"
        sf.write(tmp, s, sr)
        partes.append(ler(tmp))
    salvar(nome, partes)


# ---------------------------------------------------------------- Chatterbox
@candidato("5_chatterbox_pt")
def chatterbox(nome):
    import torch
    _load = torch.load
    torch.load = lambda *a, **k: _load(*a, **{**k, "map_location": "cpu"})   # pesos salvos em CUDA
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    modelo = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    # referência de timbre (clonagem): 10 s de cada voz do Edge
    refs = {}
    for q, cfg in EDGE["2_edge_antonio_andrew"].items():
        texto = ("Fala, Nação! Hoje tem Mengão e a sala tá pronta. Pipoca, camisa da sorte "
                 "e o controle remoto no lugar certo, que ninguém mexe.") if q == "rubro" else \
                ("Olha, primo, eu só vim ver o jogo. Se o teu time perder, eu juro que não "
                 "comento nada. Só um pouquinho, no grupo da família.")
        arq = OUT / f"_ref_{q}.wav"
        sf.write(arq, edge(texto, *cfg), SR)
        refs[q] = str(arq)
    partes = []
    for q, f, emo in DIALOGO:
        wav = modelo.generate(f, language_id="pt", audio_prompt_path=refs[q],
                              exaggeration=emo, cfg_weight=0.4 if emo > 0.7 else 0.5)
        tmp = OUT / "_c.wav"
        sf.write(tmp, wav.squeeze(0).numpy(), modelo.sr)
        partes.append(ler(tmp))
    salvar(nome, partes)


# ---------------------------------------------------------------- Piper
@candidato("6_piper_faber_cadu")
def piper(nome):
    base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR"
    vozes = {"rubro": "faber/medium/pt_BR-faber-medium", "primo": "cadu/medium/pt_BR-cadu-medium"}
    for v in vozes.values():
        for ext in (".onnx", ".onnx.json"):
            alvo = Path("piper") / (Path(v).name + ext)
            alvo.parent.mkdir(exist_ok=True)
            if not alvo.exists():
                subprocess.run(["curl", "-fsSL", "-o", str(alvo), f"{base}/{v}{ext}"], check=True)
    partes = []
    for q, f, _e in DIALOGO:
        tmp = OUT / "_p.wav"
        subprocess.run([sys.executable, "-m", "piper", "-m", f"piper/{Path(vozes[q]).name}.onnx",
                        "-f", str(tmp)], input=f.encode(), check=True)
        partes.append(ler(tmp))
    salvar(nome, partes)


if __name__ == "__main__":
    so = sys.argv[1:] or ["kokoro", "edge", "piper", "chatterbox"]
    if "kokoro" in so: kokoro()
    if "edge" in so: rodar_edge()
    if "piper" in so: piper()
    if "chatterbox" in so: chatterbox()
    for f in OUT.glob("_*"):
        f.unlink()
    print(sorted(p.name for p in OUT.glob("*.mp3")))
