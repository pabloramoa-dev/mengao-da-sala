"""Motor visual v3: sala à noite + Juninho e Primo em rig SVG, tudo no HyperFrames/GSAP.

Sem camada Manim: os personagens são SVG em camadas (personagens_v3) e o GSAP
anima só atributos (href das expressões/bocas, rotate dos pivôs). Isso deixa o
render determinístico quadro a quadro e mais leve que o motor anterior.

O que anima:
- piscar a cada 2–5 s (sequência fixa por personagem, mesma em todo render);
- respiração leve (escala a partir da cintura);
- quem fala: boca em 5 formatos pelo áudio (visemas do amplitude.py), cabeça
  acompanhando a fala, gesto da batida e uma ênfase no meio da frase;
- quem escuta reage: expressão/gesto da reação e inclinação para quem fala;
- câmera aproxima em fala forte (plano close/impacto ou humor intenso);
- tremida de tela + clarão no gol;
- TV em primeiro plano com placar, tabela ou manchete da batida.

Os textos exibidos vêm só da pauta/batida (já checadas); nada é criado aqui.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

from src.flamengo.render import hyperframes as hf
from src.flamengo.render import personagens_v4 as P
from src.flamengo.render import quintal

VERSION = "hyperframes-v4-gil-cida"
WIDTH, HEIGHT, FPS = hf.WIDTH, hf.HEIGHT, hf.FPS
NOMES = {"rubro": "GIL", "primo": "DONA CIDA"}
# posição dos personagens na cena (translate, escala) e centro da cabeça para a câmera
POS = {"rubro": (318, 842, .86), "primo": (790, 800, .84)}
REACAO = {
    "celular": ("debochado", "celular"), "nao": ("indignado", "cruzar"),
    "revirar": ("debochado", "ombros"), "rir": ("rindo", "ombros"),
    "sofrer": ("sofrendo", "facepalm"), "orgulho": ("euforico", "peito"),
    "choque": ("chocado", "maos_juntas"), "cruzar": ("debochado", "cruzar"),
    "sim": ("neutra", "repouso"),
}
INTENSOS = {"euforico", "indignado", "chocado"}
SELOS = {"plantao_da_sala": "PLANTÃO DA SALA", "pos_jogo_v2": "PÓS-JOGO", "pos_jogo": "PÓS-JOGO",
         "palpite_cida": "PALPITE NO QUINTAL", "pre_jogo": "PRÉ-JOGO", "tabela_semanal": "TABELA DA SEMANA", "primo_rival": "DESAFIO DO PRIMO",
         "o_sofa_nao_aguenta": "RESENHA DO SOFÁ", "voce_sabia": "VOCÊ SABIA?", "conta_do_titulo": "CONTA DO TÍTULO",
         "contagem": "CONTAGEM REGRESSIVA", "zoeira_rival": "ZOEIRA DA SALA", "hoje_tem_mengao": "HOJE TEM MENGÃO",
         "a_nacao_escala": "A NAÇÃO ESCOLHE", "a_nacao_respondeu": "A NAÇÃO RESPONDEU", "eu_avisei": "ANTES E DEPOIS"}
GOL = re.compile(r"\bgol(?:a[çc]o|s)?\b", re.I)


def cabeca(q):
    x, y, k = POS[q]
    return x, y - 40 * k


# ------------------------------------------------------------------ direção
def direcao(b: dict, q: str) -> tuple[str, str]:
    """(expressão, gesto) de q nesta batida: quem fala usa a direção; quem ouve, a reação."""
    if b.get("personagem", "rubro") == q:
        expr = b.get("humor", "neutra")
        gesto = b.get("gesto", "explicar")
        gesto = "ombros" if gesto == "perguntar" else gesto
        return (expr if expr in P.EXPRESSOES else "neutra", gesto if gesto in P.GESTOS else "explicar")
    padrao = "celular" if q == "primo" else ("nao" if b.get("humor") == "debochado" else "sim")
    expr, gesto = REACAO.get(b.get("reacao") or padrao, ("neutra", "repouso"))
    if q == "primo" and gesto not in ("celular", "cruzar", "ombros", "facepalm", "maos_juntas", "peito"):
        gesto = "celular"
    return expr, gesto


def eh_gol(b: dict) -> bool:
    return (b.get("tipo") == "placar" and b.get("humor") == "euforico") or \
        bool(GOL.search(b.get("fala", "")) and b.get("humor") == "euforico")


def piscadas(q: str, total: float) -> list[float]:
    """Intervalos 2–5 s, determinísticos (sem aleatório entre renders)."""
    t, k, out = (0.9 if q == "rubro" else 1.7), 0, []
    while t < total - .2:
        out.append(round(t, 3))
        k += 1
        t += 2.0 + ((k * (7 if q == "rubro" else 11)) % 30) / 10
    return out


def bocas(cues: list[dict], ini: float, fim: float) -> list[tuple[float, str]]:
    """Trocas de boca (tempo, formato) dentro da fala, sem repetir formato seguido."""
    out, ultima = [], None
    for c in cues:
        a, z = float(c["start"]), float(c["end"])
        if z <= ini or a >= fim:
            continue
        forma = P.VISEMA.get(c.get("value", "X"), "fechada")
        if forma != ultima:
            out.append((round(max(a, ini), 3), forma))
            ultima = forma
    if not out or out[0][0] > ini:
        out.insert(0, (ini, "fechada"))
    return out


# ------------------------------------------------------------------ cena
def cenario() -> str:
    """Sala à noite (fundo). Flâmula genérica, sem escudo."""
    W, H = WIDTH, HEIGHT
    s = '''<defs>
 <radialGradient id="tvluz" cx="50%" cy="80%" r="70%"><stop offset="0" stop-color="#3B5BD9" stop-opacity=".5"/><stop offset="1" stop-color="#0D0B1E" stop-opacity="0"/></radialGradient>
 <linearGradient id="parede" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22122A"/><stop offset="1" stop-color="#3E1A2E"/></linearGradient>
 <linearGradient id="sofa_g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8E1F2E"/><stop offset="1" stop-color="#5E1220"/></linearGradient>
 <linearGradient id="chao" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2A1A1E"/><stop offset="1" stop-color="#120C10"/></linearGradient>
</defs>'''
    s += f'<rect x="-200" y="-200" width="{W+400}" height="{H+400}" fill="url(#parede)"/>'
    for x in range(-180, W + 200, 90):
        s += f'<rect x="{x}" y="-200" width="45" height="{H+400}" fill="#fff" opacity=".025"/>'
    # janela com cidade à noite
    s += f'<g transform="translate(30,560)"><rect width="300" height="380" rx="10" fill="#141A3A" stroke="{P.INK}" stroke-width="12"/>'
    s += '<circle cx="225" cy="70" r="34" fill="#FBE7A6"/>'
    s += '<path d="M0,300 L70,190 L130,260 L180,160 L250,240 L300,210 L300,380 L0,380 Z" fill="#2B3566"/>'
    for (x, w, h) in ((18, 56, 120), (84, 48, 160), (142, 66, 100), (220, 56, 140)):
        s += f'<rect x="{x}" y="{380-h}" width="{w}" height="{h}" fill="#0E1230"/>'
        for yy in range(380 - h + 14, 370, 26):
            for xx in range(x + 9, x + w - 8, 18):
                if (xx * 7 + yy) % 3:
                    s += f'<rect x="{xx}" y="{yy}" width="7" height="10" fill="#FFD66B" opacity=".8"/>'
    s += f'<path d="M150,0 L150,380 M0,190 L300,190" stroke="{P.INK}" stroke-width="10"/></g>'
    # flâmula rubro-negra genérica + prateleira com troféu
    s += f'<path d="M800,560 L1010,560 L905,750 Z" fill="#D0102C" stroke="{P.INK}" stroke-width="9"/>'
    s += '<path d="M826,606 L984,606 L967,636 L843,636 Z M859,664 L951,664 L934,694 L876,694 Z" fill="#17120F"/>'
    s += f'<rect x="-20" y="1000" width="230" height="20" rx="6" fill="#6B4630" stroke="{P.INK}" stroke-width="7"/>'
    s += f'<path d="M70,930 L126,930 Q130,976 98,984 Q66,976 70,930 Z" fill="#F2C14E" stroke="{P.INK}" stroke-width="7"/><rect x="85" y="984" width="26" height="18" fill="#F2C14E" stroke="{P.INK}" stroke-width="6"/>'
    # luminária
    s += f'<path d="M1000,940 L1060,940 L1080,1010 L980,1010 Z" fill="#F5C542" stroke="{P.INK}" stroke-width="7"/><ellipse cx="1030" cy="1030" rx="120" ry="60" fill="#FFD66B" opacity=".08"/>'
    return s


def sofa() -> str:
    s = f'<path d="M-30,1170 Q-30,1110 60,1105 L1020,1105 Q1110,1110 1110,1170 L1110,1440 L-30,1440 Z" fill="url(#sofa_g)" stroke="{P.INK}" stroke-width="12"/>'
    s += '<path d="M40,1225 L1040,1225" stroke="#3E0B15" stroke-width="8" opacity=".6"/>'
    s += f'<rect x="-40" y="1150" width="150" height="300" rx="50" fill="#7A1827" stroke="{P.INK}" stroke-width="11"/>'
    s += f'<rect x="970" y="1150" width="150" height="300" rx="50" fill="#7A1827" stroke="{P.INK}" stroke-width="11"/>'
    s += f'<g transform="translate(520,1130) rotate(-8)"><rect width="140" height="110" rx="32" fill="#D0102C" stroke="{P.INK}" stroke-width="9"/><rect x="6" y="28" width="128" height="20" fill="#17120F"/><rect x="6" y="68" width="128" height="20" fill="#17120F"/></g>'
    s += f'<g transform="translate(960,1080) scale(.72)"><path d="M0,40 L110,40 L95,170 L15,170 Z" fill="#fff" stroke="{P.INK}" stroke-width="8"/>'
    s += ''.join(f'<path d="M{x},42 L{x-2},168" stroke="#D0102C" stroke-width="12"/>' for x in (22, 48, 74))
    s += ''.join(f'<circle cx="{x}" cy="{y}" r="20" fill="#FFF6D8" stroke="{P.INK}" stroke-width="5"/>'
                 for (x, y) in ((10, 30), (35, 18), (62, 14), (88, 22), (105, 34), (50, 0), (80, 4)))
    return s + '</g>'


def tv_moldura() -> str:
    s = f'<rect x="0" y="1660" width="{WIDTH}" height="{HEIGHT-1660}" fill="url(#chao)"/>'
    s += f'<rect x="440" y="1690" width="200" height="40" rx="10" fill="#0D0D12" stroke="{P.INK}" stroke-width="8"/>'
    s += f'<rect x="60" y="1380" width="960" height="320" rx="28" fill="#0D0D12" stroke="{P.INK}" stroke-width="12"/>'
    s += '<rect x="88" y="1406" width="904" height="266" rx="14" fill="#10204A"/>'
    s += '<rect x="88" y="1406" width="904" height="266" rx="14" fill="#2E7D32" opacity=".42"/>'
    s += '<path d="M540,1406 L540,1672 M88,1539 L992,1539" stroke="#fff" stroke-width="4" opacity=".18"/>'
    s += '<circle cx="540" cy="1539" r="56" fill="none" stroke="#fff" stroke-width="4" opacity=".18"/>'
    s += '<circle cx="980" cy="1688" r="6" fill="#ed344c"/>'
    return s


def tela_tv(pauta: dict, b: dict, i: int, font_path: Path) -> str:
    """HTML do que passa na TV nesta batida (só dados da batida/pauta)."""
    d = b.get("dados") or {}
    tipo = b.get("tipo")
    if tipo == "classificacao" and d.get("linhas"):
        linhas = d["linhas"]
        if not (1 <= len(linhas) <= 5):
            raise ValueError("Painel de tabela exige de uma a cinco equipes")
        rows = "".join(
            f'<tr class="{"flamengo" if str(r["id"]) == "819" else ""}"><td>{int(r["rank"])}</td>'
            f'<td>{hf._escape(hf._curto(r["time"], 22))}</td><td>{int(r["points"])}</td>'
            f'<td>{int(r["gamesPlayed"])}</td><td>{int(r["pointDifferential"]):+d}</td></tr>' for r in linhas)
        return ('<div class="tv-tag">BRASILEIRÃO · CLASSIFICAÇÃO</div><table class="tv-tabela"><thead><tr>'
                '<th>#</th><th>TIME</th><th>PTS</th><th>J</th><th>SG</th></tr></thead>'
                f'<tbody>{rows}</tbody></table>')
    p = hf.painel(pauta, b, i)
    if b.get("carimbo") or d.get("cartao"):
        p = dict(p, titulo=str(b.get("carimbo") or d.get("cartao")).upper())
    if p["tag"] == "RESENHA DO SOFÁ":
        p = dict(p, tag="RESENHA DA NAÇÃO")
    if tipo == "noticia":
        p = dict(p, tag="RUMOR · SEM CONFIRMAÇÃO" if d.get("rumor") else "NOTÍCIA DO DIA")
    elif tipo == "abre" and d.get("cartao"):
        p = dict(p, tag="RESENHA DA NAÇÃO")
    proprio = b.get("carimbo") or d.get("cartao") or tipo in ("placar", "tabela", "nota", "mexida", "cta")
    if not proprio:
        # sem dado próprio: a TV não repete a legenda; mostra o confronto ou mantém a tela anterior
        if pauta.get("rival"):
            p = dict(p, tag="RESENHA AO VIVO", titulo=f"MENGÃO × {str(pauta['rival']).upper()}")
        elif i == 0:
            p = dict(p, tag="RESENHA DA NAÇÃO", titulo=str(pauta.get("capa") or "MENGÃO DA SALA").upper())
        else:
            return None
    if tipo == "placar":
        titulo, tam = caber(p["titulo"], font_path, 700, 1, 150, 120, 40)
    else:
        titulo, tam = caber(p["titulo"], font_path, 820, 3, 200, 70, 30)
    placar = ' tv-placar' if tipo == "placar" else ''
    return (f'<div class="tv-tag">{hf._escape(p["tag"])}</div>'
            f'<div class="tv-titulo{placar}" style="font-size:{tam}px">{hf._escape(titulo)}</div>')


def caber(texto, font_path, largura, max_linhas, altura, maior, menor):
    for tam in range(maior, menor - 1, -2):
        linhas = hf._linhas(texto, tam, font_path, largura)
        if len(linhas) <= max_linhas and len(linhas) * tam * 1.12 <= altura and all(
                hf._largura(ln, tam, font_path) <= largura for ln in linhas):
            return "\n".join(linhas), tam
    linhas = hf._linhas(texto, menor, font_path, largura)[:max_linhas]
    return "\n".join(linhas), menor


def svg_cena(pauta: dict) -> str:
    b0 = pauta["batidas"][0]
    exterior = pauta.get("solo") == "primo" or pauta.get("formato") == "palpite_cida"
    fundo = quintal.fundo() if exterior else cenario()
    frente = "" if exterior else f'<g transform="translate(0,85)">{sofa()}</g>'
    luz = "" if exterior else f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#tvluz)" pointer-events="none"/>'
    painel = quintal.moldura() if exterior else tv_moldura()
    atores = ""
    for q, fn in (("primo", P.primo), ("rubro", P.juninho)):      # Juninho na frente
        x, y, k = POS[q]
        if pauta.get("solo"):
            x, y, k = 540, 820, .94
        e, g = direcao(b0, q)
        oculto = ' style="display:none"' if pauta.get('solo') and pauta['solo'] != q else ''
        atores += f'<g{oculto} transform="translate({x},{y}) scale({k})">{fn(e, g)}</g>'
    cx, cy = WIDTH / 2, 1000
    return (f'<svg id="cena" xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">'
            f'{P.defs()}<g id="cam" transform="translate({cx},{cy}) scale(1) translate({-cx},{-cy})">'
            f'<g id="tremor" transform="translate(0,0)">{fundo}{atores}{frente}</g></g>'
            f'{luz}{painel}</svg>')


# ------------------------------------------------------------------ composição
def _cam(x, y, s):
    return f"translate({x:.1f},{y:.1f}) scale({s:.3f}) translate({-x:.1f},{-y:.1f})"


def escrever_composicao(conteudo: dict, projeto: Path, font_path: Path, cues: list[dict] | None = None) -> dict:
    dur = hf.validar_conteudo(conteudo)
    cues = cues or []
    bats, segs = conteudo["batidas"], conteudo["segs"]
    clips, anim, telas = [], [], []
    A = anim.append

    # cabeçalho fixo da pauta (capa)
    formato = str(conteudo.get("formato", "resenha"))
    selo = SELOS.get(formato) or " ".join(formato.replace("_", " ").split()).upper()
    capa, capa_tam = caber(str(conteudo.get("capa") or "MENGÃO DA SALA").upper(), font_path, 900, 2, 150, 66, 34)

    for i, (b, s) in enumerate(zip(bats, segs)):
        a = float(s["ini"])
        z = dur if i == len(bats) - 1 else float(s["fim"])
        fala_fim = float(s["fim_fala"])
        quem = b.get("personagem", "rubro")
        ouvinte = "primo" if quem == "rubro" else "rubro"

        # TV: uma tela por conteúdo; batida sem dado próprio mantém a tela anterior no ar
        tela = tela_tv(conteudo, b, i, font_path)
        if tela is not None:
            if telas:
                telas[-1][2] = a
            telas.append([tela, a, z])
        elif telas:
            telas[-1][2] = z

        # personagens
        for q in ("rubro", "primo"):
            expr, gesto = direcao(b, q)
            (od, cd), (oe, ce) = P.GESTOS[gesto]
            A(f'tl.set("#{q}-exp",{{attr:{{href:"#{q}-exp-{expr}"}}}},{a});')
            if q != quem:
                A(f'tl.set("#{q}-boca",{{attr:{{href:"#{q}-rep-{expr}"}}}},{a});')
            for parte, ang in ((f"{q}-ombroD", od), (f"{q}-cotoveloD", cd), (f"{q}-ombroE", oe), (f"{q}-cotoveloE", ce)):
                A(f'tl.to("#{parte}",{{attr:{{transform:"rotate({-ang})"}},duration:.3,ease:"back.out(1.5)"}},{a});')
        # boca de quem fala, pelo áudio
        expr_q, gesto_q = direcao(b, quem)
        for t, forma in bocas(cues, a, fala_fim):
            A(f'tl.set("#{quem}-boca",{{attr:{{href:"#{quem}-fala-{forma}"}}}},{t});')
        A(f'tl.set("#{quem}-boca",{{attr:{{href:"#{quem}-rep-{expr_q}"}}}},{fala_fim});')
        # cabeça: quem fala acompanha a frase; quem ouve inclina para quem fala
        d = fala_fim - a
        voltas = max(1, int(d / .42)) | 1
        A(f'tl.to("#{quem}-cabeca",{{attr:{{transform:"rotate({-3 if quem == "rubro" else 3})"}},duration:{d/(voltas+1):.3f},ease:"sine.inOut",yoyo:true,repeat:{voltas}}},{a});')
        A(f'tl.to("#{ouvinte}-cabeca",{{attr:{{transform:"rotate({5 if ouvinte == "rubro" else -5})"}},duration:.35,ease:"power2.out"}},{a});')
        # ênfase no meio da frase
        if d > 1.4:
            _, c_d = P.GESTOS[gesto_q][0]
            A(f'tl.to("#{quem}-cotoveloD",{{attr:{{transform:"rotate({-(c_d + 16)})"}},duration:.18,yoyo:true,repeat:1,ease:"sine.inOut"}},{a + d*.5 + .3:.3f});')
        # câmera
        forte = i and (b.get("plano") in {"close", "impacto"} or b.get("humor") in INTENSOS)
        x, y = ((540, 780) if conteudo.get("solo") else cabeca(quem)) if forte else (WIDTH / 2, 1000)
        esc = (1.2 if b.get("plano") == "impacto" else 1.13) if forte else 1.0
        A(f'tl.to("#cam",{{attr:{{transform:"{_cam(x, y, esc)}"}},duration:.45,ease:"power2.out"}},{a});')
        if i:
            A(f'tl.fromTo("#flash",{{opacity:.10}},{{opacity:0,duration:.2}},{a});')
        # gol: tremida + clarão
        if eh_gol(b):
            t0 = a + .15
            for k, (dx, dy) in enumerate(((14, -8), (-12, 10), (10, 6), (-8, -10), (6, 4), (0, 0))):
                A(f'tl.to("#tremor",{{attr:{{transform:"translate({dx},{dy})"}},duration:.05,ease:"none"}},{t0 + k*.05:.3f});')
            A(f'tl.fromTo("#flash",{{opacity:.45}},{{opacity:0,duration:.45}},{t0});')
        if b.get("efeito") == "confete" or eh_gol(b):
            for n in range(22):
                ident = f"confetti{i}_{n}"
                clips.append(f'<div id="{ident}" class="confetti" style="left:{50+(n*137)%950}px;background:{["#ed344c", "#ffcf63", "#ffffff"][n%3]}"></div>')
                A(f'tl.fromTo("#{ident}",{{opacity:1,y:-30,rotation:0}},{{opacity:0,y:{900+(n*71)%600},rotation:{180+n*33},duration:2.2,ease:"power1.in"}},{a});')

        # legenda (texto falado, destaque proporcional por palavra)
        blocos = hf._blocos_legenda(b["fala"], font_path)
        pesos = [max(2, len(w)) for w in b["fala"].split()]
        tempo, j = a, 0
        for k, bloco in enumerate(blocos):
            inicio, spans = tempo, []
            tam = min(44, int(44 * 860 / max(860, max(hf._largura(w, 44, font_path) for w in bloco))))
            for palavra in bloco:
                fim = tempo + (fala_fim - a) * pesos[j] / sum(pesos)
                spans.append(f'<span id="w{i}_{j}">{hf._escape(palavra)}</span>')
                A(f'tl.set("#w{i}_{j}",{{color:"#ffd461"}},{tempo:.3f});tl.set("#w{i}_{j}",{{color:"#ffffff"}},{fim:.3f});')
                tempo, j = fim, j + 1
            fim_bloco = z if k == len(blocos) - 1 else tempo
            cor = "red" if quem == "rubro" else "blue"
            clips.append(f'<div id="caption{i}_{k}" class="clip caption {cor}" data-start="{inicio:.3f}" data-duration="{fim_bloco-inicio:.3f}" data-track-index="3">'
                         f'<div class="speaker">{NOMES[quem]}</div><div class="words" style="--caption-size:{tam}px">{" ".join(spans)}</div></div>')

    for k, (tela, a, z) in enumerate(telas):
        clips.append(f'<div id="tv{k}" class="clip tv" data-start="{a:.3f}" data-duration="{z-a:.3f}" data-track-index="2">{tela}</div>')
        if k:
            A(f'tl.fromTo("#tv{k}",{{opacity:0,scale:.97}},{{opacity:1,scale:1,duration:.22,ease:"power2.out"}},{a:.3f});')

    # vida contínua: respiração, piscar, balanço
    for q, per in (("rubro", 1.7), ("primo", 1.9)):
        c = P.GEO[q]["cintura"]
        n = int(dur / per) + 1
        A(f'tl.to("#{q}-respira",{{attr:{{transform:"translate(0,{c}) scale(1.012,1.02) translate(0,-{c})"}},duration:{per},ease:"sine.inOut",yoyo:true,repeat:{n}}},0);')
        for t in piscadas(q, dur):
            A(f'tl.set("#{q}-pisca",{{opacity:1}},{t});tl.set("#{q}-pisca",{{opacity:0}},{t + .11:.3f});')
    anim.insert(0, 'tl.set("#flash",{opacity:0},0);tl.set("#tremor",{attr:{transform:"translate(0,0)"}},0);')
    A(f'tl.fromTo("#status",{{opacity:.4}},{{opacity:1,duration:.7,yoyo:true,repeat:{math.ceil(dur/.7)}}},0);')
    A(f'tl.fromTo("#progress",{{scaleX:0}},{{scaleX:1,duration:{dur},ease:"none"}},0);')

    css = (projeto / "assets/composition_v3.css").read_text(encoding="utf-8")
    documento = (
        '<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Mengão da Sala v3</title>'
        f'<style>{css}</style></head><body>'
        f'<div id="root" data-composition-id="mengao-v3" data-start="0" data-width="{WIDTH}" data-height="{HEIGHT}" data-duration="{dur}" data-fps="{FPS}">'
        f'{svg_cena(conteudo)}'
        '<header><div class="brand">MENGÃO DA SALA</div><div class="live"><span id="status"></span>RESENHA DA NAÇÃO</div></header>'
        f'<div class="banner"><div class="selo">{hf._escape(selo)}</div>'
        f'<div class="capa" style="font-size:{capa_tam}px">{hf._escape(capa)}</div></div>'
        f'{"".join(clips)}'
        '<footer><span>@mengaodasala</span></footer><div id="progress"></div><div id="flash"></div>'
        f'<audio id="voice" src="assets/mix.wav" data-start="0" data-duration="{dur}" data-track-index="4"></audio>'
        '<script src="assets/gsap.min.js"></script>'
        f'<script>const tl=gsap.timeline({{paused:true}});{"".join(anim)}'
        'window.__timelines=window.__timelines||{};window.__timelines["mengao-v3"]=tl;</script>'
        '</div></body></html>')
    (projeto / "index.html").write_text(documento, encoding="utf-8")
    return {"duracao_segundos": dur, "motor": "hyperframes", "versao_visual": VERSION,
            "personagens": "rig-svg-v3", "resolucao": [WIDTH, HEIGHT], "fps": FPS,
            "legendas_timing": "proporcional_por_palavra", "boca": "visemas_por_amplitude"}


def preparar_projeto(trabalho: Path, raiz: Path, fonte: Path) -> Path:
    projeto = trabalho / "hyperframes_v3"
    assets = projeto / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fonte, assets / "bold.ttf")
    shutil.copyfile(raiz / "video/assets/composition_v3.css", assets / "composition_v3.css")
    shutil.copyfile(raiz / "video/node_modules/gsap/dist/gsap.min.js", assets / "gsap.min.js")
    return projeto


def renderizar(conteudo: dict, audio: dict, destino: Path, trabalho: Path, raiz: Path) -> dict:
    dur = hf.validar_conteudo(conteudo)
    fonte = Path(os.environ.get("FLAMENGO_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    if not fonte.is_file():
        raise RuntimeError("Fonte DejaVu Sans Bold não instalada")
    cli = raiz / "video/node_modules/hyperframes/bin/hyperframes.mjs"
    if not cli.is_file():
        raise RuntimeError("HyperFrames não instalado: rode npm ci --prefix video")
    projeto = preparar_projeto(trabalho, raiz, fonte)
    cues = json.loads(Path(audio["lip"]).read_text()).get("mouthCues", []) if audio.get("lip") else []
    hf.mixar_audio(conteudo, audio["master"], projeto / "assets/mix.wav")
    meta = escrever_composicao(conteudo, projeto, fonte, cues)
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js 22+ é necessário para HyperFrames")
    env = dict(os.environ, HYPERFRAMES_FFMPEG_PATH=shutil.which("ffmpeg") or "ffmpeg",
               HYPERFRAMES_FFPROBE_PATH=shutil.which("ffprobe") or "ffprobe", HYPERFRAMES_TELEMETRY_DISABLED="1")
    subprocess.run([node, str(cli), "lint", str(projeto)], check=True, cwd=raiz, env=env)
    parcial = destino.with_name(destino.stem + ".rendering.mp4")
    try:
        subprocess.run([node, str(cli), "render", str(projeto), "--output", str(parcial), "--fps", str(FPS),
                        "--workers", os.environ.get("FLAMENGO_HF_WORKERS", "2"), "--no-browser-gpu"],
                       check=True, cwd=raiz, env=env)
        hf.conferir_video(parcial, dur)
        parcial.replace(destino)
    finally:
        parcial.unlink(missing_ok=True)
    return meta
