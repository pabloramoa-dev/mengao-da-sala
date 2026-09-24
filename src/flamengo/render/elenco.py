"""Elenco do canal do Flamengo — mesma gramatica visual do Previsao RJ.

Regra herdada: identidade por ACESSORIO, nunca por anatomia. Cabeca grande,
traco grosso, olho com brilho. O torcedor e irmao visual do Bira do Tempo.

Direitos: nenhum escudo, nenhum patrocinio, nenhum jogador real. A camisa e
listrada vermelha e preta na HORIZONTAL, generica, e o bone leva as iniciais do canal.

Interface identica a rj_cast.presenter(): devolve dict com grupo/cab/oe/od/
boca/maoE/maoD/bracoE/bracoD/sobE/sobD, para o motor de lip sync e camera
reaproveitar sem adaptacao.
"""
from manim import *
import numpy as np

config.frame_width = 8.0
config.frame_height = 14.222

INK = "#111111"
RUBRO = "#C8102E"
NEGRO = "#1A1A1A"
OURO = "#E8C468"
INICIAIS = "MS"          # Mengão da Sala - texto do bone, nunca escudo

EXPRESSOES = ("neutra", "euforico", "indignado", "tenso", "debochado")


def shape(cls, color, **kw):
    return cls(fill_color=color, fill_opacity=1, stroke_color=INK, stroke_width=5, **kw)


def _camisa_listrada(largura=1.55, altura=1.65):
    """Corpo com listras verticais recortadas dentro do retangulo do tronco."""
    base = shape(RoundedRectangle, RUBRO, width=largura, height=altura, corner_radius=0.32)
    base.move_to([0, -0.38, 0])
    # listras HORIZONTAIS: 6 faixas alternadas, comecando em vermelho no topo
    listras = VGroup()
    passo = altura / 6
    topo = -0.38 + altura / 2
    for i in range(1, 6, 2):
        y = topo - passo * i - passo / 2
        faixa = Rectangle(width=largura - 0.06, height=passo,
                          fill_color=NEGRO, fill_opacity=1, stroke_width=0)
        faixa.move_to([0, y, 0])
        listras.add(Intersection(faixa, base, fill_color=NEGRO,
                                 fill_opacity=1, stroke_width=0))
    return VGroup(base, listras)


def torcedor(nome="rubro"):
    pele = "#A96D49"
    cabelo = "#2B2320"

    sapatos = VGroup(*[shape(RoundedRectangle, "#F6F2E8", width=.68, height=.3,
                             corner_radius=.12).move_to([x, -2.12, 0]) for x in [-.43, .43]])
    pernas = VGroup(*[shape(RoundedRectangle, NEGRO, width=.48, height=1.15,
                            corner_radius=.12).move_to([x, -1.5, 0]) for x in [-.4, .4]])
    corpo = _camisa_listrada()
    pescoco = shape(RoundedRectangle, pele, width=.47, height=.58,
                    corner_radius=.16).move_to([0, .55, 0])
    cabeca = shape(RoundedRectangle, pele, width=1.72, height=1.9,
                   corner_radius=.67).move_to([0, 1.5, 0])
    orelhas = VGroup(*[shape(Circle, pele, radius=.18).move_to([x, 1.45, 0])
                       for x in [-.86, .86]])

    # bone virado para tras: acessorio que define o personagem
    copa = shape(RoundedRectangle, RUBRO, width=1.66, height=.78,
                 corner_radius=.36).move_to([0, 2.32, 0])
    aba = shape(RoundedRectangle, NEGRO, width=.62, height=.26,
                corner_radius=.12).move_to([-1.02, 2.16, 0])
    marca = Text(INICIAIS, font_size=20, weight=BOLD, color=WHITE).move_to([.16, 2.34, 0])
    bone = VGroup(copa, aba, marca)
    franja = VGroup(*[shape(Circle, cabelo, radius=r).move_to([x, y, 0])
                      for x, y, r in [(-.52, 1.98, .2), (-.16, 2.04, .22), (.22, 2.02, .2)]])

    olhos, sobrancelhas = [], []
    for x in [-.34, .34]:
        olho = VGroup(shape(Ellipse, WHITE, width=.35, height=.43).move_to([x, 1.55, 0]),
                      Dot([x + .025, 1.54, 0], radius=.085, color=INK),
                      Dot([x + .05, 1.58, 0], radius=.023, color=WHITE))
        olhos.append(olho)
        sobrancelhas.append(Line([x - .16, 1.92, 0], [x + .16, 1.95, 0],
                                 stroke_color=INK, stroke_width=7))

    nariz = ArcBetweenPoints([.01, 1.42, 0], [.13, 1.22, 0], angle=-.8,
                             stroke_color="#754A38", stroke_width=4)
    boca = ArcBetweenPoints([-.22, 1.04, 0], [.22, 1.04, 0], angle=1,
                            stroke_color=INK, stroke_width=5)

    maos = [shape(Circle, pele, radius=.22).move_to([x, -.73, 0]) for x in [-1.05, 1.05]]
    bracos = [Line([x * .7, .14, 0], m.get_center(), stroke_color=pele, stroke_width=24)
              for x, m in zip([-1, 1], maos)]
    gola = VGroup(Line([-.26, .4, 0], [0, .15, 0], stroke_color=INK, stroke_width=4),
                  Line([0, .15, 0], [.26, .4, 0], stroke_color=INK, stroke_width=4))

    grupo = VGroup(pernas, sapatos, *bracos, corpo, pescoco, orelhas, cabeca,
                   franja, bone, *olhos, *sobrancelhas, nariz, boca, gola, *maos)

    r = dict(grupo=grupo, cab=cabeca, oe=olhos[0], od=olhos[1], boca=boca,
             maoE=maos[0], maoD=maos[1], bracoE=bracos[0], bracoD=bracos[1],
             sobE=sobrancelhas[0], sobD=sobrancelhas[1], bone=bone)
    r.update(cabeca=cabeca, olho_e=olhos[0], olho_d=olhos[1],
             mao_e=maos[0], mao_d=maos[1])
    return r


def expressao(p, humor="neutra"):
    """Absoluta, nunca acumulativa — armadilha ja paga no Pablo Guru."""
    if humor not in EXPRESSOES:
        raise ValueError(f"Expressao desconhecida: {humor}")
    centro = p["cab"].get_center()
    esc = p["cab"].width / 1.72
    inclin = {"neutra": (.03, .03), "euforico": (.13, -.13),
              "indignado": (-.17, -.05), "tenso": (.15, -.15),
              "debochado": (-.14, .06)}[humor]
    for lado, x, s in zip(("E", "D"), (-.34, .34), inclin):
        y = .56 if humor in {"euforico", "tenso"} else .42
        p["sob" + lado].become(Line(centro + np.array([x - .16, y - s / 2, 0]) * esc,
                                    centro + np.array([x + .16, y + s / 2, 0]) * esc,
                                    stroke_color=INK, stroke_width=7))
    ang = {"euforico": 1.7, "indignado": -1.0, "tenso": -.5,
           "debochado": .9, "neutra": .6}[humor]
    p["boca"].become(ArcBetweenPoints(centro + np.array([-.22, -.46, 0]) * esc,
                                      centro + np.array([.22, -.46, 0]) * esc,
                                      angle=ang, stroke_color=INK, stroke_width=5))
    return p


def cenario(tipo="sala"):
    """Sala do torcedor: parede, TV desligada e cadeira. Sem escudo na parede."""
    fundo = Rectangle(width=9, height=16, fill_color="#F2E6D8",
                      fill_opacity=1, stroke_width=0)
    faixa = Rectangle(width=9, height=1.1, fill_color=RUBRO,
                      fill_opacity=1, stroke_width=0).move_to([0, -0.9, 0])
    chao = Rectangle(width=9, height=4.6, fill_color="#C9B49B",
                     fill_opacity=1, stroke_width=0).move_to([0, -5.0, 0])
    tv = VGroup(shape(RoundedRectangle, NEGRO, width=2.3, height=1.4, corner_radius=.12),
                shape(RoundedRectangle, "#3A3A3A", width=2.0, height=1.1,
                      corner_radius=.08)).scale(0.8).move_to([-2.7, -0.4, 0])
    return VGroup(fundo, faixa, chao, tv)


class FolhaDeElenco(Scene):
    """Prova visual: uma folha com o personagem nos cinco humores."""

    def construct(self):
        self.camera.background_color = "#F2E6D8"
        titulo = Text("TORCEDOR — FOLHA DE ELENCO", font_size=34, weight=BOLD, color=INK)
        if titulo.width > 7.2:
            titulo.scale(7.2 / titulo.width)
        self.add(titulo.move_to([0, 6.4, 0]))
        for i, humor in enumerate(EXPRESSOES):
            col, lin = i % 2, i // 2
            x = -1.9 + col * 3.8
            y = 4.4 - lin * 3.6
            v = expressao(torcedor(), humor)
            g = v["grupo"]
            g.scale(min(3.1 / g.width, 2.6 / g.height)).move_to([x, y, 0])
            self.add(g, Text(humor.upper(), font_size=18, weight=BOLD,
                             color=INK).move_to([x, y - 1.7, 0]))


class FotoPerfil(Scene):
    """Avatar 1080x1080: rosto do torcedor euforico em fundo rubro-negro.
    O Instagram corta em circulo — tudo que importa fica no centro."""

    def construct(self):
        self.camera.background_color = RUBRO
        faixas = VGroup(*[Rectangle(width=20, height=0.9, fill_color=NEGRO, fill_opacity=1,
                                    stroke_width=0).move_to([0, y, 0])
                          for y in (-3.6, -1.8, 0, 1.8, 3.6)])
        self.add(faixas)
        p = expressao(torcedor(), "euforico")
        busto = VGroup(p["grupo"])
        busto.scale(2.35).move_to([0, -1.55, 0])
        self.add(busto)
