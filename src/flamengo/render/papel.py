"""Camada "colagem de papel" (estilo Vox) do @mengaodasala.

Portada do previsao-rj/render/characters/vox_papel.py (mesma engenharia já
aprovada no Pablo Guru, Nina e @previsaorj), só com a paleta rubro-negra:

  * recortes com borda rasgada + fibra branca + sombra;
  * fita adesiva, carimbo, manchete em pedaços de papel;
  * grão de papel aplicado DEPOIS, por ffmpeg, sobre o vídeo mudo
    (textura como imagem dentro do Manim deixa o render lento demais).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile

import numpy as np
from manim import (BLACK, DOWN, LEFT, ORIGIN, PI, RIGHT, UP, Line, Polygon,
                   RoundedRectangle, Text, VGroup)
from PIL import Image, ImageDraw, ImageFilter

FONTE = os.environ.get("FLAMENGO_FONTE", "Poppins")
CACHE = os.path.join(tempfile.gettempdir(), "mengao_vox_cache")

ESTILO = dict(
    tinta="#fbf8f0",
    ink="#141010",
    rubro="#C8102E",
    rubro_esc="#8E0B20",
    negro="#161214",
    ouro="#F2C14E",
    recorte="#f3ecdc",
    fita="#d8c38a",
    azul="#4F9FD8",
    verde="#2F9E62",
    sombra=0.5,
    grao=0.10,
)


def cor(nome):
    return ESTILO.get(nome, nome)


def texto(txt, tam, c="ink", peso="BOLD"):
    try:
        return Text(txt, font=FONTE, weight=peso, font_size=tam, color=cor(c))
    except Exception:                                   # fonte ausente: não derruba o render
        return Text(txt, font="DejaVu Sans", weight=peso, font_size=tam, color=cor(c))


def _png(chave, gerar):
    os.makedirs(CACHE, exist_ok=True)
    caminho = os.path.join(CACHE, hashlib.md5(chave.encode()).hexdigest()[:12] + ".png")
    if not os.path.exists(caminho):
        gerar().save(caminho)
    return caminho


# ------------------------------------------------------------------ recortes
def contorno_rasgado(w, h, dente=0.05, passo=0.11, semente=1):
    rng = np.random.default_rng(semente)
    pts = []

    def lado(a, b):
        n = max(2, int(np.linalg.norm(b - a) / passo))
        nor = np.array([-(b - a)[1], (b - a)[0], 0.0])
        nor /= np.linalg.norm(nor)
        for i in range(n):
            pts.append(a + (b - a) * (i / n) + nor * rng.uniform(-dente, dente))
    c = [np.array([-w / 2, -h / 2, 0.0]), np.array([w / 2, -h / 2, 0.0]),
         np.array([w / 2, h / 2, 0.0]), np.array([-w / 2, h / 2, 0.0])]
    for i in range(4):
        lado(c[i], c[(i + 1) % 4])
    return pts


def recorte(w, h, c="recorte", girar=0.0, sombra=True, semente=1, fibra=True, opacidade=1.0):
    pts = contorno_rasgado(w, h, semente=semente)
    g = VGroup()
    if sombra:
        g.add(Polygon(*pts, fill_color=BLACK, fill_opacity=ESTILO["sombra"] * opacidade,
                      stroke_width=0).shift(RIGHT * 0.07 + DOWN * 0.09))
    if fibra:
        g.add(Polygon(*contorno_rasgado(w + 0.1, h + 0.1, dente=0.045, semente=semente + 7),
                      fill_color="#fbf8f0", fill_opacity=opacidade, stroke_width=0))
    g.add(Polygon(*pts, fill_color=cor(c), fill_opacity=opacidade, stroke_width=0))
    return g.rotate(girar)


def fita(ponto=ORIGIN, girar=0.0, w=1.0, h=0.30):
    n, d = 6, 0.045
    esq = [[-w / 2 + (d if i % 2 else -d / 2), -h / 2 + h * i / n, 0] for i in range(n + 1)]
    dir_ = [[w / 2 + (d if i % 2 else -d / 2), h / 2 - h * i / n, 0] for i in range(n + 1)]
    return Polygon(*(esq + dir_), fill_color=ESTILO["fita"], fill_opacity=0.85,
                   stroke_width=0).rotate(girar).move_to(ponto)


def etiqueta(txt, c_papel="negro", c_txt="tinta", tam=26, semente=4, girar=0.0):
    t = texto(txt, tam, c_txt)
    p = recorte(t.width + 0.45, t.height + 0.3, c=c_papel, semente=semente)
    return VGroup(p, t.move_to(p[-1])).rotate(girar)


def manchete(txt, c_papel="ouro", c_txt="ink", tam=58, girar=0.05, semente=5,
             largura_max=6.6, desalinho=True):
    """Palavras em pedaços de papel rasgado, tortas, com desalinho de impressão."""
    rng = np.random.default_rng(semente)
    linhas_txt = txt.split("\n")
    linhas = []
    k = 0
    for lt in linhas_txt:
        pecas = []
        for pal in lt.split():
            t = texto(pal, tam, c_txt)
            papel = recorte(t.width + 0.32, t.height + 0.26, c=c_papel, semente=semente + k)
            camadas = [papel]
            if desalinho:
                camadas.append(t.copy().set_color(ESTILO["rubro"]).set_opacity(0.5)
                               .shift(LEFT * 0.03 + UP * 0.025))
            camadas.append(t.move_to(papel[-1]))
            pecas.append(VGroup(*camadas).rotate(rng.uniform(-girar, girar) * 2))
            k += 1
        if pecas:
            linhas.append(VGroup(*pecas).arrange(RIGHT, buff=0.08))
    g = VGroup(*linhas).arrange(DOWN, buff=0.06)
    if g.width > largura_max:
        g.scale_to_fit_width(largura_max)
    return g


def carimbo(txt, c="rubro", tam=52, girar=0.2):
    cc = cor(c)
    t = texto(txt, tam, cc)
    m1 = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.4, corner_radius=0.08,
                          stroke_color=cc, stroke_width=9, fill_color="#fbf8f0", fill_opacity=0.85)
    m2 = m1.copy().scale(1.07).set_stroke(width=4).set_fill(opacity=0)
    g = VGroup(m1, m2, t).rotate(girar)
    rng = np.random.default_rng(len(txt))
    falhas = VGroup(*[
        Line(ORIGIN, RIGHT * rng.uniform(0.08, 0.22), stroke_color="#fbf8f0",
             stroke_width=rng.uniform(2, 4), stroke_opacity=0.9)
        .move_to(g.get_center() + RIGHT * rng.uniform(-g.width / 2.3, g.width / 2.3)
                 + UP * rng.uniform(-g.height / 2.5, g.height / 2.5))
        .rotate(rng.uniform(0, PI)) for _ in range(10)])
    return VGroup(g, falhas)


# ------------------------------------------------------------------ entrada colada
def degrau(t, dur=0.36, fps=12):
    """Progresso 0..1 em degraus de 1/fps — o movimento de recorte do Vox."""
    if t >= dur:
        return 1.0
    n = max(1, int(round(fps * dur)))
    f = np.floor(max(0.0, t) / dur * n) / n
    return float(1 - (1 - f) ** 2)


def colado(base, dt_desde_entrada, dur=0.36, escala=1.35, giro=0.16):
    """Cópia do mobject no instante da entrada colada (maior e torto -> assenta)."""
    f = degrau(dt_desde_entrada, dur)
    novo = base.copy()
    if f < 1.0:
        c = base.get_center()
        novo.scale(escala + (1.0 - escala) * f, about_point=c)
        novo.rotate(giro * (1.0 - f), about_point=c)
    return novo


# ------------------------------------------------------------------ grão (ffmpeg)
def textura_png(largura, altura, semente=3):
    def gerar():
        rng = np.random.default_rng(semente)
        a = (rng.random((altura, largura)) ** 6 * 255 * ESTILO["grao"] * 2.2).astype(np.uint8)
        img = Image.new("RGBA", (largura, altura), (255, 255, 255, 0))
        img.putalpha(Image.fromarray(a))
        v = Image.new("L", (largura, altura), 0)
        lado = min(largura, altura)
        ImageDraw.Draw(v).rectangle([0, 0, largura, altura], outline=80, width=int(lado * 0.07))
        v = v.filter(ImageFilter.GaussianBlur(lado * 0.08))
        borda = Image.new("RGBA", (largura, altura), (20, 8, 10, 0))
        borda.putalpha(v)
        return Image.alpha_composite(img, borda)
    return _png(f"tex-mengao-{largura}x{altura}-{semente}", gerar)


def aplicar_textura(entrada, saida, crf=18):
    info = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "json", str(entrada)]))["streams"][0]
    tex = textura_png(int(info["width"]), int(info["height"]))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(entrada), "-loop", "1", "-i", tex,
                    "-filter_complex", "[0:v][1:v]overlay=shortest=1:format=auto,format=yuv420p[v]",
                    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", str(crf),
                    "-preset", "medium", str(saida)], check=True)
    return saida
