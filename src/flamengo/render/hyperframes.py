"""Compositor de produção: rig Manim original + HyperFrames / GSAP.

As falas e os fatos continuam no roteirista. Este módulo só apresenta a
pauta recebida. As palavras do karaokê usam tempo proporcional à fala real,
nunca são apresentadas como alinhamento fonético.
"""
from __future__ import annotations

import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

TAIL = 1.4
VERSION = "hyperframes-v1"
WIDTH, HEIGHT, FPS = 1080, 1920, 30
NOMES = {"rubro": "JUNINHO", "primo": "PRIMO SECADOR"}


def validar_conteudo(conteudo: dict) -> float:
    """Falhas de áudio/timing não podem produzir um vídeo aparentemente válido."""
    batidas, segs = conteudo.get("batidas"), conteudo.get("segs")
    if not batidas or not segs or len(batidas) != len(segs):
        raise ValueError("batidas e segmentos precisam corresponder")
    anterior = 0.0
    for b, s in zip(batidas, segs):
        a, fala, z = (float(s[k]) for k in ("ini", "fim_fala", "fim"))
        if not all(math.isfinite(t) for t in (a, fala, z)) or not (anterior <= a < fala <= z):
            raise ValueError("segmento com tempo inválido ou sobreposto")
        if not str(b.get("fala", "")).strip() or b.get("personagem", "rubro") not in NOMES:
            raise ValueError("fala vazia ou personagem desconhecido")
        anterior = z
    return anterior + TAIL


def _escape(texto) -> str:
    return html.escape(str(texto), quote=True)


def _curto(texto, limite=115):
    """Recorta texto existente, sem criar uma afirmação nova."""
    texto = " ".join(str(texto).split())
    if len(texto) <= limite:
        return texto
    return texto[:limite].rsplit(" ", 1)[0].rstrip(".,:;") + "…"


def painel(pauta: dict, batida: dict, indice: int) -> dict:
    """Dados exibidos vêm exclusivamente da batida/pauta já checada."""
    d = batida.get("dados") or {}
    tipo = batida.get("tipo", "reacao")
    tag = "RESENHA DO SOFÁ"
    titulo = batida.get("carimbo") or d.get("cartao") or _curto(batida["fala"], 68)
    subtitulo = _curto(batida.get("legenda") or batida["fala"])
    efeito = "versus"
    if indice == 0:
        tag, titulo = "MENGÃO NA SALA", pauta.get("capa") or titulo
    if tipo == "placar" and d.get("placar"):
        tag, titulo = "PLACAR CONFIRMADO", str(d["placar"]).replace(" x ", " × ")
        efeito = "campo"
    elif tipo == "tabela" and d.get("posicao") is not None:
        tag, titulo = "NA TABELA", f"{d['posicao']}º LUGAR"
        if d.get("pontos") is not None:
            titulo += f" · {d['pontos']} PONTOS"
    elif tipo == "nota" and d.get("nota") is not None:
        tag = d.get("rotulo") or "PONTUAÇÃO CARTOLA"
        titulo = f"{d.get('nome', '')}\n{float(d['nota']):.1f}".replace(".", ",")
        subtitulo = "Pontos no Cartola · " + subtitulo
    elif tipo == "mexida" and d.get("saiu") and d.get("entrou"):
        tag = "TROCA" + (f" · {d['minuto']} MIN" if d.get("minuto") else "")
        titulo = f"SAI {d['saiu']}\nENTRA {d['entrou']}"
    elif tipo == "pergunta":
        tag, titulo = "A NAÇÃO PARTICIPA", d.get("cartao") or "SUA VEZ, NAÇÃO!"
    elif tipo == "cta":
        tag = "A RESENHA CONTINUA"
        fala = batida["fala"].casefold()
        titulo = ("SEGUE O MENGÃO DA SALA" if "segue" in fala else
                  "MARCA O SEU SECADOR" if "marca" in fala else
                  "COMENTA AÍ, NAÇÃO!" if "comenta" in fala or "comentários" in fala else
                  "MANDA PARA O SEU AMIGO" if "manda" in fala or "compartilh" in fala else
                  "SUA VEZ, NAÇÃO!")
    # Um medidor de humor não é uma estatística esportiva.
    if tipo not in {"placar", "tabela", "nota", "mexida", "pergunta", "cta"} and not d:
        if re.search(r"\bsecador\b|\bsecando\b", batida["fala"], re.I):
            efeito = "medidor"
    return dict(tag=str(tag).upper(), titulo=str(titulo).upper(), subtitulo=subtitulo, efeito=efeito)


def _largura(texto, tamanho, font_path):
    from PIL import ImageFont
    f = ImageFont.truetype(str(font_path), tamanho)
    return f.getlength(texto)


def _linhas(texto, tamanho, font_path, max_width):
    linhas = []
    for paragrafo in str(texto).splitlines() or [""]:
        linha = ""
        for palavra in paragrafo.split():
            if linha and _largura(linha + " " + palavra, tamanho, font_path) > max_width:
                linhas.append(linha)
                linha = palavra
            else:
                linha = (linha + " " + palavra).strip()
        linhas.append(linha)
    return linhas


def titulo_formatado(texto, font_path):
    for tamanho in range(67, 28, -2):
        linhas = _linhas(texto, tamanho, font_path, 840)
        if len(linhas) <= 3 and len(linhas) * tamanho * 1.09 <= 132 and all(
                _largura(ln, tamanho, font_path) <= 840 for ln in linhas):
            return "\n".join(linhas), tamanho
    raise ValueError("título não cabe no painel; revise a pauta")


def _blocos_legenda(texto, font_path):
    """Duas linhas no máximo; verifica pixels, inclusive palavras extensas."""
    blocos, atual = [], []
    for palavra in texto.split():
        if atual and len(_linhas(" ".join(atual + [palavra]), 46, font_path, 840)) > 2:
            blocos.append(atual)
            atual = []
        atual.append(palavra)
    if atual:
        blocos.append(atual)
    return blocos


def escrever_composicao(conteudo: dict, projeto: Path, font_path: Path) -> dict:
    dur = validar_conteudo(conteudo)
    clips, anim = [], []
    for i, (b, s) in enumerate(zip(conteudo["batidas"], conteudo["segs"])):
        a = s["ini"]
        z = dur if i == len(conteudo["batidas"]) - 1 else s["fim"]
        p = painel(conteudo, b, i)
        titulo, tamanho = titulo_formatado(p["titulo"], font_path)
        if b.get("tipo") == "classificacao":
            linhas = (b.get("dados") or {}).get("linhas") or []
            if not (1 <= len(linhas) <= 5):
                raise ValueError("Painel de tabela exige de uma a cinco equipes")
            rows = []
            for row in linhas:
                cls = "flamengo" if str(row["id"]) == "819" else ""
                nome = _curto(row["time"], 27)
                rows.append(f'<tr class="{cls}"><td>{int(row["rank"])}</td><td>{_escape(nome)}</td><td>{int(row["points"])}</td><td>{int(row["gamesPlayed"])}</td><td>{int(row["pointDifferential"]):+d}</td></tr>')
            table = '<table class="standings"><thead><tr><th>POS</th><th>TIME</th><th>PTS</th><th>J</th><th>SG</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'
            clips.append(f'<section id="panel{i}" class="clip panel" data-start="{a}" data-duration="{z-a}" data-track-index="2"><div id="card{i}" class="card standings-card"><div class="eyebrow">BRASILEIRÃO · CLASSIFICAÇÃO</div>{table}<p>Coleta: {_escape(conteudo.get("coletado_em", "")[:16])} UTC · PTS pontos · J jogos · SG saldo</p></div></section>')
        elif p["efeito"] == "medidor":
            extra = f'<div class="meter"><div class="fill" id="fill{i}"></div></div><div class="meter-label">MEDIDOR DE SECAGEM · HUMOR</div>'
            anim.append(f'tl.fromTo("#fill{i}",{{scaleX:0}},{{scaleX:1,duration:1.2,ease:"power2.out"}},{a + .35});')
        elif p["efeito"] == "campo":
            extra = f'<div class="field"><div class="ball" id="ball{i}"></div><div class="field-circle"></div></div>'
            anim.append(f'tl.fromTo("#ball{i}",{{x:0,rotation:0}},{{x:600,rotation:720,duration:{min(2.5,z-a)},ease:"power2.inOut"}},{a});')
        else:
            extra = '<div class="versus"><span>JUNINHO</span><b>×</b><span>PRIMO SECADOR</span></div>'
        if b.get("tipo") != "classificacao":
            clips.append(f'<section id="panel{i}" class="clip panel" data-start="{a}" data-duration="{z-a}" data-track-index="2"><div id="card{i}" class="card"><div class="eyebrow">{_escape(p["tag"])}</div><h1 style="--title-size:{tamanho}px">{_escape(titulo)}</h1><p>{_escape(p["subtitulo"])}</p>{extra}</div></section>')
        # Capa legível no primeiro quadro; demais cartões entram suavemente.
        if i:
            anim.append(f'tl.fromTo("#card{i}",{{y:40,scale:.96,opacity:0}},{{y:0,scale:1,opacity:1,duration:.25,ease:"power3.out"}},{a});')
        anim.append(f'tl.to("#card{i}",{{y:-9,duration:{max(.1,z-a-.3)}}},{a+.3});')
        quem = b.get("personagem", "rubro")
        # Captions reproduce the actual spoken text, even when a numeric data
        # panel uses digits. No fabricated word-level alignment.
        blocos = _blocos_legenda(b["fala"], font_path)
        pesos = [max(2, len(w)) for w in b["fala"].split()]
        tempo, j = a, 0
        for k, bloco in enumerate(blocos):
            inicio, spans = tempo, []
            caption_size = min(46, int(46 * 840 / max(840, max(_largura(w, 46, font_path) for w in bloco))))
            for palavra in bloco:
                fim = tempo + (s["fim_fala"] - a) * pesos[j] / sum(pesos)
                spans.append(f'<span id="w{i}_{j}">{_escape(palavra)}</span>')
                anim.append(f'tl.set("#w{i}_{j}",{{color:"#ffd461"}},{tempo});tl.set("#w{i}_{j}",{{color:"#ffffff"}},{fim});')
                tempo, j = fim, j + 1
            fim_bloco = z if k == len(blocos) - 1 else tempo
            cor = "red" if quem == "rubro" else "blue"
            clips.append(f'<div id="caption{i}_{k}" class="clip caption {cor}" data-start="{inicio}" data-duration="{fim_bloco-inicio}" data-track-index="3"><div class="speaker">{NOMES[quem]}</div><div class="words" style="--caption-size:{caption_size}px">{" ".join(spans)}</div></div>')
        plano = b.get("plano", "dupla")
        scale = 1.10 if plano in {"close", "impacto"} and i else 1.03
        x = (48 if quem == "rubro" else -48) if scale > 1.05 else 0
        anim.append(f'tl.to("#base",{{scale:{scale},x:{x},duration:.38,ease:"power2.out"}},{a});')
        if i:
            anim.append(f'tl.fromTo("#flash",{{opacity:.12}},{{opacity:0,duration:.22}},{a});')
        if b.get("efeito") == "confete":
            for n in range(22):
                ident = f"confetti{i}_{n}"
                clips.append(f'<div id="{ident}" class="confetti" style="left:{50+(n*137)%950}px;background:{["#ed344c", "#ffcf63", "#ffffff"][n%3]}"></div>')
                anim.append(f'tl.fromTo("#{ident}",{{opacity:1,y:-30,rotation:0}},{{opacity:0,y:{800+(n*71)%600},rotation:{180+n*33},duration:2.2,ease:"power1.in"}},{a});')
    anim.append(f'tl.fromTo("#status",{{opacity:.5}},{{opacity:1,duration:.7,yoyo:true,repeat:{math.ceil(dur/.7)}}},0);tl.fromTo("#progress",{{scaleX:0}},{{scaleX:1,duration:{dur},ease:"none"}},0);')
    formato = " ".join(str(conteudo.get("formato", "resenha")).replace("_", " ").split()).upper()
    fonte = (projeto / "assets/composition.css").read_text()
    fonte += '\n.meter-label{font-size:17px;letter-spacing:1px;color:#bfb3b8;margin-top:9px}.field{height:74px}.field-circle{height:54px;width:54px;top:8px}.ball{top:19px;width:32px;height:32px}\n'
    documento = f'''<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Mengão da Sala</title><style>{fonte}</style></head><body><div id="root" data-composition-id="mengao-hf" data-start="0" data-width="{WIDTH}" data-height="{HEIGHT}" data-duration="{dur}" data-fps="{FPS}"><video id="base" class="clip" data-start="0" data-duration="{dur}" data-track-index="0" src="assets/base.mp4" muted playsinline></video><div class="shade"></div><header><div class="brand">MENGÃO DA SALA</div><div class="live"><span id="status"></span>RESENHA</div></header>{''.join(clips)}<div class="names"><span>JUNINHO</span><span>PRIMO SECADOR</span></div><footer><span>@mengaodasala</span><small>A RIVALIDADE MORA AQUI.</small></footer><div id="progress"></div><div class="demo">{_escape(formato)}</div><div id="flash"></div><audio id="voice" src="assets/mix.wav" data-start="0" data-duration="{dur}" data-track-index="4"></audio><script src="assets/gsap.min.js"></script><script>const tl=gsap.timeline({{paused:true}});{''.join(anim)}window.__timelines=window.__timelines||{{}};window.__timelines["mengao-hf"]=tl;</script></div></body></html>'''
    (projeto / "index.html").write_text(documento, encoding="utf-8")
    return {"duracao_segundos": dur, "motor": "hyperframes", "versao_visual": VERSION,
            "resolucao": [WIDTH, HEIGHT], "fps": FPS, "legendas_timing": "proporcional_por_palavra"}


def mixar_audio(conteudo, master: Path, destino: Path):
    """Batida original e efeitos discretos; voz mantém a masterização aprovada."""
    import numpy as np
    import soundfile as sf
    sr, dur = 48000, validar_conteudo(conteudo)
    bed = np.zeros(int(math.ceil(dur * sr)), dtype=np.float32)
    rng = np.random.default_rng(42)
    for k, inicio in enumerate(np.arange(0, dur, .5)):
        n = int(.15 * sr)
        t = np.arange(n) / sr
        s = .017 * np.sin(2*np.pi*(62*t-22*t*t)) * np.exp(-t*26)
        if k % 2:
            s += rng.normal(0, .003, n) * np.exp(-t*45)
        a = int(inicio*sr)
        z = min(n, len(bed)-a)
        bed[a:a+z] += s[:z]
    for seg in conteudo["segs"][1:]:
        n = int(.17*sr)
        t = np.arange(n)/sr
        s = rng.normal(0, .009, n) * np.sin(np.pi*t/.17)**2
        a, z = int(seg["ini"]*sr), min(n, len(bed)-int(seg["ini"]*sr))
        bed[a:a+z] += s[:z]
    sf.write(destino.parent / "bed.wav", bed, sr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(master), "-i", str(destino.parent / "bed.wav"),
                    "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.89:level=disabled[a]",
                    "-map", "[a]", "-ar", "48000", str(destino)], check=True)


def conferir_video(destino: Path, duracao: float) -> dict:
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,avg_frame_rate,codec_name",
                        "-of", "json", str(destino)], capture_output=True, text=True, check=True)
    m = json.loads(p.stdout)
    videos = [s for s in m["streams"] if s["codec_type"] == "video"]
    if not videos or (videos[0]["width"], videos[0]["height"]) != (WIDTH, HEIGHT):
        raise RuntimeError("HyperFrames não gerou vídeo vertical Full HD")
    num, den = (int(n) for n in videos[0]["avg_frame_rate"].split("/"))
    if not den or abs(num / den - FPS) > .01:
        raise RuntimeError("frame rate inesperado")
    if not any(s["codec_type"] == "audio" for s in m["streams"]):
        raise RuntimeError("vídeo renderizado sem áudio")
    if abs(float(m["format"]["duration"]) - duracao) > .15:
        raise RuntimeError("duração do vídeo não corresponde à narração")
    return m


def renderizar(conteudo: dict, audio: dict, destino: Path, trabalho: Path, raiz: Path) -> dict:
    import sys
    dur = validar_conteudo(conteudo)
    fonte = Path(os.environ.get("FLAMENGO_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    if not fonte.is_file():
        raise RuntimeError("Fonte DejaVu Sans Bold não instalada")
    cli = raiz / "video/node_modules/hyperframes/bin/hyperframes.mjs"
    if not cli.is_file():
        raise RuntimeError("HyperFrames não instalado: rode npm ci --prefix video")
    projeto = trabalho / "hyperframes"
    assets = projeto / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fonte, assets / "bold.ttf")
    shutil.copyfile(raiz / "video/assets/composition.css", assets / "composition.css")
    shutil.copyfile(raiz / "video/node_modules/gsap/dist/gsap.min.js", assets / "gsap.min.js")
    env = dict(os.environ, FLAMENGO_TRAB=str(trabalho), PYTHONPATH=str(raiz))
    # Character layer has no captions/camera; the browser owns those layers.
    subprocess.run([sys.executable, "-m", "manim", "--fps", str(FPS), "--disable_caching", "--media_dir", str(trabalho / "media_hf"),
                    str(raiz / "src/flamengo/render/cena_hyperframes.py"), "HyperframesBase"], check=True, cwd=raiz, env=env)
    mudo = next((trabalho / "media_hf/videos").rglob("HyperframesBase.mp4"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mudo), "-c:v", "libx264", "-preset", "fast", "-crf", "16",
                    "-g", str(FPS), "-keyint_min", str(FPS), "-sc_threshold", "0", "-movflags", "+faststart", str(assets / "base.mp4")], check=True)
    mixar_audio(conteudo, audio["master"], assets / "mix.wav")
    meta = escrever_composicao(conteudo, projeto, fonte)
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js 22+ é necessário para HyperFrames")
    hf_env = dict(env, HYPERFRAMES_FFMPEG_PATH=shutil.which("ffmpeg") or "ffmpeg",
                  HYPERFRAMES_FFPROBE_PATH=shutil.which("ffprobe") or "ffprobe", HYPERFRAMES_TELEMETRY_DISABLED="1")
    subprocess.run([node, str(cli), "lint", str(projeto)], check=True, cwd=raiz, env=hf_env)
    # Keep an atomic final path: publication cannot see a partially encoded MP4.
    parcial = destino.with_name(destino.stem + ".rendering.mp4")
    try:
        subprocess.run([node, str(cli), "render", str(projeto), "--output", str(parcial), "--fps", str(FPS),
                        "--workers", os.environ.get("FLAMENGO_HF_WORKERS", "2"), "--no-browser-gpu"], check=True, cwd=raiz, env=hf_env)
        conferir_video(parcial, dur)
        parcial.replace(destino)
    finally:
        parcial.unlink(missing_ok=True)
    return meta
