"""Cena do Reel do canal do Flamengo.

Lê $FLAMENGO_TRAB/conteudo.json (roteiro + segs) e $FLAMENGO_TRAB/lip.json.

Armadilhas já pagas nos outros canais e respeitadas aqui:
  * TODOS os drivers de tempo (boca, piscada, respiração, legenda) ficam num
    motor = Dot invisível. Updater pendurado no personagem morre sem erro.
  * Tudo lê o RELÓGIO ABSOLUTO (motor.t), não a ordem dos play().
  * Expressões e piscada são absolutas (become / fator), nunca acumulam.
  * Legenda no terço central, banda escura, texto sem contorno.
  * Primeiro quadro = CAPA com o título (é o que aparece na grade).
"""
import json
import os
import re
from pathlib import Path

import numpy as np
from manim import *

from src.flamengo.render.elenco import (INK, NEGRO, OURO, RUBRO, cenario,
                                        expressao, torcedor)

config.frame_width = 8.0
config.frame_height = 14.222
config.pixel_width = 1080
config.pixel_height = 1920

PRE_ROLL = 0.8          # capa sozinha antes da primeira fala
TAIL = 1.2
ABERTURA = {"X": 0.0, "B": 0.25, "F": 0.35, "C": 0.55, "E": 0.7, "D": 1.0}


def _carregar():
    trab = Path(os.environ["FLAMENGO_TRAB"])
    conteudo = json.loads((trab / "conteudo.json").read_text(encoding="utf-8"))
    lip = json.loads((trab / "lip.json").read_text())["mouthCues"]
    return conteudo, lip


def _texto(txt, tam, cor=WHITE, larg_max=7.0, peso=BOLD):
    t = Text(txt, font_size=tam, weight=peso, color=cor)
    if t.width > larg_max:
        t.scale(larg_max / t.width)
    return t


def _banda(t, cor=BLACK, op=0.72, folga=(0.5, 0.3)):
    b = RoundedRectangle(width=t.width + folga[0], height=t.height + folga[1],
                         corner_radius=0.14, fill_color=cor, fill_opacity=op,
                         stroke_width=0).move_to(t)
    return VGroup(b, t)


def _quebrar(txt, max_chars=26):
    if "\n" in txt:                       # quebra definida pelo roteiro manda
        return "\n".join(_quebrar(p, max_chars) for p in txt.split("\n"))
    # placar nunca quebra: "2 a 1" / "2 x 1" vira um bloco só
    txt = re.sub(r"(\d+) ([ax]) (\d+)", "\\1\u00a0\\2\u00a0\\3", txt)
    palavras, linhas, atual = txt.split(" "), [], ""
    for p in palavras:
        if len(atual) + len(p) + 1 > max_chars and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = f"{atual} {p}".strip()
    if atual:
        linhas.append(atual)
    return "\n".join(linhas)


def _legenda(txt):
    t = Text(_quebrar(txt), font_size=34, weight=BOLD, color=WHITE, line_spacing=0.8)
    if t.width > 7.0:
        t.scale(7.0 / t.width)
    return _banda(t).move_to([0, 1.5, 0])


def _cartao(batida):
    """Cartão de dado grande para as batidas de placar e tabela."""
    tipo, d = batida.get("tipo"), batida.get("dados", {})
    if tipo == "nota":
        nome = _texto(str(d.get("nome", "")).upper(), 46, WHITE, 5.6)
        nota = _texto(f"{d.get('nota', 0):.1f}".replace(".", ","), 96, OURO, 5.6)
        rot = _texto("MELHOR DO CARTOLA" if d.get("nota", 0) >= 5 else "PIOR DO CARTOLA",
                     22, WHITE, 5.6)
        g = VGroup(rot, nome, nota).arrange(DOWN, buff=0.14)
        fundo = RoundedRectangle(width=max(g.width + 0.9, 4.2), height=g.height + 0.6,
                                 corner_radius=0.2, fill_color=RUBRO, fill_opacity=1,
                                 stroke_color=INK, stroke_width=6).move_to(g)
        return VGroup(fundo, g).move_to([0, 4.5, 0])
    if tipo == "mexida":
        l1 = _texto(f"{d.get('minuto', '')}'", 40, OURO, 5.8)
        l2 = _texto(f"SAI  {str(d.get('saiu', '')).upper()}", 38, WHITE, 5.8)
        l3 = _texto(f"ENTRA  {str(d.get('entrou', '')).upper()}", 38, WHITE, 5.8)
        g = VGroup(l1, l2, l3).arrange(DOWN, buff=0.16)
        fundo = RoundedRectangle(width=g.width + 0.9, height=g.height + 0.6, corner_radius=0.2,
                                 fill_color=NEGRO, fill_opacity=1, stroke_color=RUBRO,
                                 stroke_width=8).move_to(g)
        return VGroup(fundo, g).move_to([0, 4.5, 0])
    if d.get("cartao"):                    # cartão genérico dos formatos diários
        t_ = _texto(str(d["cartao"]), 64, WHITE, 6.4)
        fundo = RoundedRectangle(width=t_.width + 0.9, height=t_.height + 0.6, corner_radius=0.2,
                                 fill_color=NEGRO if tipo in ("hora", "jogo") else RUBRO,
                                 fill_opacity=1, stroke_color=INK, stroke_width=6).move_to(t_)
        return VGroup(fundo, t_).move_to([0, 4.4, 0])
    if tipo == "pergunta":
        t_ = _texto("ACERTOU OU ERROU?", 58, WHITE, 6.6)
        fundo = RoundedRectangle(width=t_.width + 0.9, height=t_.height + 0.6, corner_radius=0.2,
                                 fill_color=RUBRO, fill_opacity=1, stroke_color=INK,
                                 stroke_width=6).move_to(t_)
        return VGroup(fundo, t_).move_to([0, 4.5, 0])
    if tipo == "placar":
        txt = d.get("placar", "")
    elif tipo == "tabela":
        txt = f"{d.get('posicao', '')}º · {d.get('pontos', '')} PTS" if d.get("pontos") else \
              f"{d.get('posicao', '')}º LUGAR"
    else:
        return None
    t = _texto(txt, 72, WHITE, 6.4)
    fundo = RoundedRectangle(width=t.width + 0.9, height=t.height + 0.6, corner_radius=0.2,
                             fill_color=RUBRO, fill_opacity=1, stroke_color=INK,
                             stroke_width=6).move_to(t)
    return VGroup(fundo, t).move_to([0, 4.3, 0])


def _boca(centro, esc, abertura, humor):
    if abertura <= 0.02:
        ang = {"euforico": 1.7, "indignado": -1.0}.get(humor, .6)
        return ArcBetweenPoints(centro + np.array([-.22, -.46, 0]) * esc,
                                centro + np.array([.22, -.46, 0]) * esc,
                                angle=ang, stroke_color=INK, stroke_width=5)
    return Ellipse(width=(0.30 + 0.08 * abertura) * esc,
                   height=(0.06 + 0.30 * abertura) * esc,
                   fill_color="#5A1A1A", fill_opacity=1, stroke_color=INK,
                   stroke_width=5).move_to(centro + np.array([0, -.48, 0]) * esc)


class ReelFlamengo(Scene):
    def construct(self):
        conteudo, cues = _carregar()
        batidas, segs = conteudo["batidas"], conteudo["segs"]
        humor = conteudo["humor"]
        total = PRE_ROLL + segs[-1]["fim"] + TAIL

        self.camera.background_color = "#F2E6D8"
        self.add(cenario())

        p = expressao(torcedor(), humor)
        g = p["grupo"]
        g.scale(5.4 / g.height).move_to([0, -2.6, 0])
        self.add(g)
        base_y = g.get_center()[1]

        # ---- capa: título grande já no quadro 0 ----
        etiqueta = _banda(_texto("MENGÃO DA SALA", 26, WHITE), NEGRO, 1).move_to([0, 6.3, 0])
        titulo = _banda(_texto(_quebrar(conteudo["capa"], 18), 64, WHITE, 6.4), RUBRO, 1,
                        (0.8, 0.6)).move_to([0, 4.3, 0])
        self.add(etiqueta, titulo)

        # ---- motor: único dono de todos os updaters ----
        # O personagem recebe um updater vazio só para o Manim NÃO congelá-lo
        # na imagem estática do wait (senão boca e piscada não aparecem).
        g.add_updater(lambda m, dt: None)
        motor = Dot(radius=0.001, fill_opacity=0).set_opacity(0)
        motor.t = 0.0
        estado = {"resp": 0.0, "pisc": 1.0}
        self.add(motor)

        def cue_em(ta):
            for c in cues:
                if c["start"] <= ta < c["end"]:
                    return ABERTURA.get(c["value"], 0.0)
            return 0.0

        def dirigir(m, dt):
            m.t += dt
            t = m.t
            ta = t - PRE_ROLL
            alvo = 0.05 * np.sin(t * TAU / 2.6)
            g.shift(UP * (alvo - estado["resp"]))
            estado["resp"] = alvo
            centro, esc = p["cab"].get_center(), p["cab"].width / 1.72
            p["boca"].become(_boca(centro, esc, cue_em(ta) if ta >= 0 else 0.0, humor))
            fase = t % 3.7
            f = max(.08, abs(fase - .12) / .12) if fase < .24 else 1.0
            for k in ("oe", "od"):
                p[k].stretch(f / estado["pisc"], 1, about_point=p[k].get_center())
            estado["pisc"] = f

        motor.add_updater(dirigir)

        # ---- linha do tempo por eventos: troca de camada só ENTRE waits ----
        relogio = 0.0
        self.wait(PRE_ROLL)
        relogio = PRE_ROLL
        self.remove(titulo)
        camada = VGroup()
        for i, s in enumerate(segs):
            inicio = PRE_ROLL + s["ini"]
            if inicio > relogio:
                self.wait(inicio - relogio)
                relogio = inicio
            self.remove(camada)
            camada = VGroup(_legenda(batidas[i]["legenda"]))
            cartao = _cartao(batidas[i])
            if cartao is not None:
                camada.add(cartao)
            self.add(camada)
        self.wait(total - relogio)
