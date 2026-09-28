"""Elenco v2 do @mengaodasala — JUNINHO (o dono da sala) e o PRIMO SECADOR.

Por que existe: na v1 os dois bonecos eram o MESMO desenho com a camisa
pintada de outra cor, parados, com a mesma voz. Aqui cada um tem silhueta,
rosto, cabelo, acessório e jeito de mexer próprios — dá pra saber quem fala
com o som desligado.

    JUNINHO        baixinho e parrudo, cabeça redonda, barba por fazer, boné
                   rubro-negro virado pra trás, camisa listrada na HORIZONTAL,
                   cachecol listrado. Gesticula grande, fala com o corpo todo.
    PRIMO SECADOR  alto e magro, rosto comprido, topete com gel, óculos escuros
                   na testa, bigodinho fino, camisa polo azul-celeste e
                   cordãozinho dourado. Mexe pouco, sobrancelha sempre erguida,
                   vive olhando o celular. Não tem time definido: ele SECA.

Direitos: nenhum escudo, nenhum patrocínio, nenhum jogador real.

RIG PARAMÉTRICO: o personagem é redesenhado a cada quadro a partir de uma POSE
(números), nunca animando submobjeto. É a lição mais cara já paga no Pablo
Guru: animar um pedaço desmonta o personagem de scene.mobjects e os updaters
morrem sem erro. Aqui não há o que desmontar — cada quadro é um desenho novo.

Coordenadas locais: (0, 0) = base do pescoço. O sofá, na frente, cobre a
cintura pra baixo (eles estão SENTADOS — na v1 estavam em pé em cima do sofá).
"""
from __future__ import annotations

import numpy as np
from manim import (DOWN, LEFT, ORIGIN, PI, RIGHT, TAU, UP, WHITE, Arc,
                   ArcBetweenPoints, Circle, Dot, Ellipse, Intersection, Line,
                   Polygon, Rectangle, RoundedRectangle, VGroup, VMobject)

INK = "#141010"
RUBRO = "#C8102E"
RUBRO_ESC = "#8E0B20"
NEGRO = "#1A1617"
OURO = "#F2C14E"
BOCA_IN = "#5A1418"
LINGUA = "#D9646A"

EXPRESSOES = ("neutra", "euforico", "indignado", "tenso", "debochado", "rindo", "chocado", "sofrendo")
GESTOS = ("repouso", "explicar", "apontar", "bracos_cima", "facepalm", "ombros",
          "cruzar", "peito", "celular", "maos_juntas", "contar")


def P(x, y):
    return np.array([x, y, 0.0])


def shape(cls, color, *args, sw=8, **kw):
    return cls(*args, fill_color=color, fill_opacity=1, stroke_color=INK, stroke_width=sw, **kw)


def curva(pts, **kw):
    m = VMobject(**kw)
    m.set_points_smoothly([np.asarray(p, dtype=float) for p in pts])
    return m


# =============================================================================
#  FICHA DE CADA PERSONAGEM (tudo que muda entre os dois)
# =============================================================================
FICHA = {
    "rubro": dict(
        nome="JUNINHO", pele="#A96D49", pele_esc="#8A5638", cabelo="#2B2320",
        cab_centro=P(0, 1.30), cab_r=0.98, cab_w=1.96, cab_h=1.96,
        olho_y=1.40, olho_dx=0.36, olho_w=0.40, olho_h=0.46, iris="#4A2A1A",
        sob_y=1.76, boca_y=0.80, boca_w=0.46,
        ombro=1.05, manga=RUBRO, braco_w=26, mao_r=0.24,
        energia=1.0,                  # quanto o corpo acompanha a fala
    ),
    "primo": dict(
        nome="PRIMO SECADOR", pele="#E2AE85", pele_esc="#C48D66", cabelo="#1E1A22",
        cab_centro=P(0, 1.62), cab_r=0.80, cab_w=1.58, cab_h=2.16,
        olho_y=1.78, olho_dx=0.30, olho_w=0.34, olho_h=0.36, iris="#2F4F3A",
        sob_y=2.12, boca_y=1.06, boca_w=0.40,
        ombro=0.80, manga="#8CC8EE", braco_w=20, mao_r=0.21,
        energia=0.55,                 # o secador é contido: mexe pouco, fala com a sobrancelha
    ),
}


# =============================================================================
#  PARTES ESTÁTICAS (feitas UMA vez, copiadas a cada quadro)
# =============================================================================
_CACHE: dict = {}


def _torso_juninho():
    f = FICHA["rubro"]
    corpo = shape(RoundedRectangle, RUBRO, sw=10, width=2.45, height=3.0, corner_radius=0.95)
    corpo.move_to(P(0, -1.55))
    listras = VGroup()
    passo = 0.36
    for i, y in enumerate(np.arange(-0.25, -3.1, -passo)):
        if i % 2 == 1:
            faixa = Rectangle(width=2.6, height=passo, stroke_width=0).move_to(P(0, y))
            listras.add(Intersection(faixa, corpo, fill_color=NEGRO, fill_opacity=1, stroke_width=0))
    contorno = corpo.copy().set_fill(opacity=0)
    pescoco = shape(RoundedRectangle, f["pele"], sw=8, width=0.62, height=0.5,
                    corner_radius=0.18).move_to(P(0, 0.12))
    # cachecol listrado em volta do pescoço + ponta caída do lado de fora
    volta = shape(RoundedRectangle, RUBRO, sw=8, width=1.35, height=0.42, corner_radius=0.2).move_to(P(0, -0.08))
    volta_l = VGroup(*[Rectangle(width=0.16, height=0.36, fill_color=NEGRO, fill_opacity=1,
                                 stroke_width=0).move_to(P(x, -0.08)) for x in (-0.42, -0.1, 0.22, 0.5)])
    ponta = shape(RoundedRectangle, RUBRO, sw=8, width=0.36, height=1.25, corner_radius=0.12)
    ponta.rotate(0.12).move_to(P(-0.42, -0.85))
    ponta_l = VGroup(*[Rectangle(width=0.3, height=0.12, fill_color=NEGRO, fill_opacity=1, stroke_width=0)
                       .rotate(0.12).move_to(P(-0.42 + 0.02 * k, -0.45 - 0.3 * k)) for k in range(4)])
    franja = VGroup(*[Line(P(-0.5 + 0.08 * k, -1.47), P(-0.5 + 0.08 * k, -1.62), stroke_color=RUBRO,
                           stroke_width=4) for k in range(3)])
    return VGroup(corpo, listras, contorno, pescoco, ponta, ponta_l, franja, volta, volta_l)


def _torso_primo():
    f = FICHA["primo"]
    polo = "#8CC8EE"
    corpo = shape(RoundedRectangle, polo, sw=10, width=1.85, height=3.1, corner_radius=0.55).move_to(P(0, -1.6))
    pescoco = shape(RoundedRectangle, f["pele"], sw=8, width=0.44, height=0.62, corner_radius=0.14).move_to(P(0, 0.18))
    # gola polo branca aberta + cordão dourado + botões
    golaE = Polygon(P(-0.05, -0.02), P(-0.52, -0.02), P(-0.34, -0.42), fill_color=WHITE, fill_opacity=1,
                    stroke_color=INK, stroke_width=6)
    golaD = golaE.copy().flip(UP, about_point=ORIGIN)
    v = Polygon(P(-0.18, -0.05), P(0.18, -0.05), P(0, -0.52), fill_color=f["pele"], fill_opacity=1,
                stroke_color=INK, stroke_width=5)
    cordao = ArcBetweenPoints(P(-0.2, 0.0), P(0.2, 0.0), angle=PI * 0.8).set_stroke(OURO, 6)
    ping = Dot(P(0, -0.2), radius=0.06, color=OURO)
    botoes = VGroup(*[Dot(P(0, y), radius=0.035, color=INK) for y in (-0.62, -0.82)])
    friso = Line(P(-0.92, -2.2), P(0.92, -2.2), stroke_color=WHITE, stroke_width=6)
    return VGroup(corpo, friso, pescoco, v, cordao, ping, golaE, golaD, botoes)


def _cabeca_juninho():
    f = FICHA["rubro"]
    c = f["cab_centro"]
    orelhas = VGroup(*[shape(Ellipse, f["pele"], sw=7, width=0.3, height=0.42).move_to(c + P(s * 0.98, -0.02))
                       for s in (-1, 1)])
    cabeca = shape(Circle, f["pele"], sw=12, radius=f["cab_r"]).move_to(c)
    barba = Ellipse(width=1.55, height=0.78, fill_color="#3B2A22", fill_opacity=0.22,
                    stroke_width=0).move_to(c + P(0, -0.5))
    costeleta = VGroup(*[Rectangle(width=0.14, height=0.36, fill_color=f["cabelo"], fill_opacity=1,
                                   stroke_width=0).move_to(c + P(s * 0.86, 0.22)) for s in (-1, 1)])
    # boné virado pra trás: copa cobrindo o topo + aba saindo atrás (lado oposto ao olhar)
    copa = VMobject(fill_color=RUBRO, fill_opacity=1, stroke_color=INK, stroke_width=10)
    arco = [c + P(np.cos(a) * 1.05, np.sin(a) * 1.05) for a in np.linspace(0.62, PI - 0.62, 24)]
    copa.set_points_as_corners(arco + [c + P(-0.84, 0.60), c + P(0.84, 0.60), arco[0]])
    faixa = Polygon(c + P(-0.80, 0.58), c + P(0.80, 0.58), c + P(0.70, 0.74), c + P(-0.70, 0.74),
                    fill_color=NEGRO, fill_opacity=1, stroke_color=INK, stroke_width=6)
    botao = Dot(c + P(0, 1.06), radius=0.07, color=NEGRO)
    costura = ArcBetweenPoints(c + P(-0.2, 1.04), c + P(0.3, 0.74), angle=-0.3).set_stroke(RUBRO_ESC, 4)
    return dict(atras=VGroup(orelhas), cabeca=VGroup(cabeca, barba, costeleta),
                topo=VGroup(copa, faixa, costura, botao))


def _cabeca_primo():
    f = FICHA["primo"]
    c = f["cab_centro"]
    orelhas = VGroup(*[shape(Ellipse, f["pele"], sw=7, width=0.26, height=0.4).move_to(c + P(s * 0.8, -0.05))
                       for s in (-1, 1)])
    cabeca = shape(Ellipse, f["pele"], sw=12, width=f["cab_w"], height=f["cab_h"]).move_to(c)
    # topete com gel: bloco de cabelo alto, penteado pra trás
    topete = VMobject(fill_color=f["cabelo"], fill_opacity=1, stroke_color=INK, stroke_width=9)
    topete.set_points_smoothly([c + P(-0.80, 0.30), c + P(-0.86, 0.80), c + P(-0.55, 1.18),
                                c + P(-0.05, 1.42), c + P(0.55, 1.36), c + P(0.84, 1.02),
                                c + P(0.80, 0.42), c + P(0.55, 0.78), c + P(0.0, 0.86),
                                c + P(-0.5, 0.74), c + P(-0.80, 0.30)])
    brilho = ArcBetweenPoints(c + P(-0.3, 1.2), c + P(0.35, 1.22), angle=-0.6).set_stroke("#6B6475", 5)
    # óculos escuros na testa
    lente = lambda x: shape(RoundedRectangle, "#23262E", sw=6, width=0.5, height=0.3,
                            corner_radius=0.1).move_to(c + P(x, 0.66))
    oculos = VGroup(lente(-0.3), lente(0.3), Line(c + P(-0.05, 0.7), c + P(0.05, 0.7), stroke_color=INK, stroke_width=6),
                    Line(c + P(-0.4, 0.72), c + P(-0.28, 0.64), stroke_color="#9AA3B5", stroke_width=3))
    costeleta = VGroup(*[Rectangle(width=0.1, height=0.3, fill_color=f["cabelo"], fill_opacity=1,
                                   stroke_width=0).move_to(c + P(s * 0.72, 0.28)) for s in (-1, 1)])
    return dict(atras=VGroup(orelhas), cabeca=VGroup(cabeca, costeleta),
                topo=VGroup(topete, brilho, oculos))


def _estaticos(quem):
    if quem not in _CACHE:
        if quem == "rubro":
            _CACHE[quem] = dict(torso=_torso_juninho(), **_cabeca_juninho())
        else:
            _CACHE[quem] = dict(torso=_torso_primo(), **_cabeca_primo())
    return _CACHE[quem]


# =============================================================================
#  ROSTO DINÂMICO
# =============================================================================
# (abertura do olho, pálpebra, inclinação sob. interna, altura extra sob.)
_ROSTO = {
    "neutra":    (1.00, 0.00, 0.00, 0.00),
    "euforico":  (1.10, 0.00, 0.10, 0.10),
    "indignado": (0.85, 0.10, -0.20, -0.04),
    "tenso":     (1.05, 0.00, 0.16, 0.08),
    "debochado": (0.80, 0.42, None, 0.00),       # None = uma sobrancelha erguida
    "rindo":     (0.25, 0.00, 0.08, 0.06),       # olho "fechado de rir" (arco)
    "chocado":   (1.25, 0.00, 0.12, 0.16),
    "sofrendo":  (0.90, 0.20, 0.22, 0.02),
}


def _boca(f, expr, abertura, c, face):
    """Boca: fechada por expressão, aberta pelo áudio (energia do lip sync)."""
    bc = c + P(0.05 * face, f["boca_y"] - f["cab_centro"][1])
    w = f["boca_w"]
    if abertura > 0.06:
        if expr in ("euforico", "rindo") and abertura > 0.35:
            # boca de festa: D com dentes
            h = 0.18 + 0.36 * abertura
            m = VMobject(fill_color=BOCA_IN, fill_opacity=1, stroke_color=INK, stroke_width=7)
            m.set_points_smoothly([bc + P(-w * 0.62, 0.06), bc + P(0, 0.08), bc + P(w * 0.62, 0.06),
                                   bc + P(w * 0.42, -h * 0.7), bc + P(0, -h), bc + P(-w * 0.42, -h * 0.7),
                                   bc + P(-w * 0.62, 0.06)])
            dentes = Rectangle(width=w * 0.9, height=0.09, fill_color=WHITE, fill_opacity=1,
                               stroke_width=0).move_to(bc + P(0, 0.0))
            lingua = Ellipse(width=w * 0.6, height=h * 0.35, fill_color=LINGUA, fill_opacity=1,
                             stroke_width=0).move_to(bc + P(0, -h * 0.72))
            return VGroup(m, lingua, dentes)
        ww = w * (0.72 + 0.18 * abertura) * (0.85 if expr == "chocado" else 1)
        hh = 0.07 + 0.34 * abertura
        m = Ellipse(width=ww, height=hh, fill_color=BOCA_IN, fill_opacity=1,
                    stroke_color=INK, stroke_width=7).move_to(bc + P(0, -hh * 0.25))
        if abertura > 0.45:
            lingua = Ellipse(width=ww * 0.55, height=hh * 0.35, fill_color=LINGUA, fill_opacity=1,
                             stroke_width=0).move_to(m.get_center() + P(0, -hh * 0.22))
            return VGroup(m, lingua)
        return VGroup(m)
    if expr in ("euforico", "rindo"):
        return VGroup(ArcBetweenPoints(bc + P(-w / 2, 0.06), bc + P(w / 2, 0.06), angle=1.9)
                      .set_stroke(INK, 8))
    if expr == "indignado":
        return VGroup(ArcBetweenPoints(bc + P(-w / 2, -0.06), bc + P(w / 2, -0.06), angle=-1.1)
                      .set_stroke(INK, 8))
    if expr == "sofrendo":
        return VGroup(curva([bc + P(-w / 2, -0.08), bc + P(-w / 5, 0.0), bc + P(w / 5, -0.07),
                             bc + P(w / 2, 0.0)], stroke_color=INK, stroke_width=8))
    if expr == "chocado":
        return VGroup(shape(Ellipse, BOCA_IN, sw=7, width=0.22, height=0.28).move_to(bc + P(0, -0.05)))
    if expr == "debochado":   # sorriso de canto, sempre do lado de quem ele provoca
        return VGroup(curva([bc + P(-w / 2 * face, -0.02), bc + P(0, -0.05), bc + P(w / 2 * face, 0.12)],
                            stroke_color=INK, stroke_width=8))
    if expr == "tenso":
        return VGroup(Line(bc + P(-w / 2.4, -0.02), bc + P(w / 2.4, -0.02), stroke_color=INK, stroke_width=8))
    return VGroup(ArcBetweenPoints(bc + P(-w / 2.2, 0.02), bc + P(w / 2.2, 0.02), angle=0.7)
                  .set_stroke(INK, 8))


def _rosto(quem, pose, face):
    f = FICHA[quem]
    c = f["cab_centro"]
    expr = pose["expr"]
    abre, palp_expr, incl, alt = _ROSTO[expr]
    palp = max(pose.get("palp", 0.0), palp_expr)
    olhar = np.asarray(pose.get("olhar", (0.0, 0.0)))
    g = VGroup()
    for lado in (-1, 1):
        base = P(lado * f["olho_dx"] + 0.07 * face, f["olho_y"])
        if expr == "rindo" and pose.get("boca", 0) < 0.9:
            g.add(ArcBetweenPoints(base + P(-0.15, -0.02), base + P(0.15, -0.02), angle=-2.0)
                  .set_stroke(INK, 8))
            continue
        h = max(0.035, f["olho_h"] * abre * (1 - palp))
        branco = Ellipse(width=f["olho_w"] * (1.08 if expr == "chocado" else 1), height=h,
                         fill_color=WHITE, fill_opacity=1, stroke_color=INK, stroke_width=6).move_to(base)
        g.add(branco)
        if h > 0.09:
            r = min(0.12 if expr != "chocado" else 0.085, h / 2 - 0.015)
            foco = base + P(olhar[0] * 0.07, olhar[1] * min(0.06, h / 4))
            g.add(Circle(radius=r, fill_color=f["iris"], fill_opacity=1, stroke_width=0).move_to(foco),
                  Dot(foco, radius=r * 0.55, color=INK),
                  Dot(foco + P(0.035, 0.035), radius=r * 0.28, color=WHITE))
        # pálpebra superior: traço grosso que desce com a piscada/deboche
        topo = base + P(0, h / 2)
        g.add(ArcBetweenPoints(topo + P(-f["olho_w"] / 2, -0.02), topo + P(f["olho_w"] / 2, -0.02),
                               angle=-0.6 if palp > 0.3 else -0.25).set_stroke(INK, 7 if palp > 0.3 else 5))
    # sobrancelhas: grossas, absolutas (nunca acumulam)
    sob_extra = pose.get("sob", 0.0)
    for lado in (-1, 1):
        cx = lado * f["olho_dx"] + 0.07 * face
        y = f["sob_y"] + alt + 0.12 * sob_extra
        if incl is None:                     # debochado: a sobrancelha do lado do alvo sobe
            sobe = (lado == face)
            y_int = y + (0.16 if sobe else -0.02)
            y_ext = y + (0.12 if sobe else -0.04)
        else:
            y_int, y_ext = y + incl, y - incl * 0.3
        g.add(Line(P(cx - lado * 0.08, y_int), P(cx + lado * 0.22, y_ext),
                   stroke_color=f["cabelo"], stroke_width=13 if quem == "rubro" else 9))
    # nariz: batata no Juninho, fino e comprido no Primo
    if quem == "rubro":
        g.add(shape(Ellipse, f["pele_esc"], sw=6, width=0.32, height=0.25).move_to(c + P(0.08 * face, -0.22)))
    else:
        g.add(curva([c + P(0.02 * face, 0.02), c + P(0.16 * face, -0.3), c + P(0.02 * face, -0.36)],
                    stroke_color=INK, stroke_width=6))
        # bigodinho fino + cavanhaque
        g.add(curva([c + P(-0.2 + 0.05 * face, -0.46), c + P(0.05 * face, -0.42), c + P(0.2 + 0.05 * face, -0.46)],
                    stroke_color=f["cabelo"], stroke_width=7))
        g.add(Polygon(c + P(-0.08 + 0.05 * face, -0.9), c + P(0.08 + 0.05 * face, -0.9),
                      c + P(0.05 * face, -1.04), fill_color=f["cabelo"], fill_opacity=1, stroke_width=0))
    g.add(_boca(f, expr, pose.get("boca", 0.0), c, face))
    if expr in ("tenso", "sofrendo") and pose.get("suor", True):
        gota = VMobject(fill_color="#9AD4F5", fill_opacity=1, stroke_color=INK, stroke_width=4)
        gota.set_points_smoothly([c + P(-0.7 * face, 0.75), c + P(-0.62 * face, 0.52),
                                  c + P(-0.7 * face, 0.46), c + P(-0.78 * face, 0.52), c + P(-0.7 * face, 0.75)])
        g.add(gota.shift(DOWN * (pose.get("t", 0) * 0.25 % 0.35)))
    return g


# =============================================================================
#  BRAÇOS (2 ossos, cotovelo calculado)
# =============================================================================
def _braco(quem, lado, mao, face, gesto):
    f = FICHA[quem]
    ombro = P(lado * f["ombro"], -0.42)
    mao = np.asarray(mao, dtype=float)
    meio = (ombro + mao) / 2
    d = mao - ombro
    n = np.linalg.norm(d) or 1.0
    perp = np.array([-d[1], d[0], 0.0]) / n
    if np.dot(perp, P(lado, -0.3)) < 0:
        perp = -perp                          # cotovelo sempre pra fora do corpo
    dobra = max(0.0, 1.9 - n) * 0.45
    cotovelo = meio + perp * dobra
    g = VGroup(
        Line(ombro, cotovelo, stroke_color=INK, stroke_width=f["braco_w"] + 8),
        Line(cotovelo, mao, stroke_color=INK, stroke_width=f["braco_w"] + 8),
        Line(ombro, cotovelo, stroke_color=f["pele"], stroke_width=f["braco_w"]),
        Line(cotovelo, mao, stroke_color=f["pele"], stroke_width=f["braco_w"]),
        Line(ombro, ombro + (cotovelo - ombro) * 0.55, stroke_color=f["manga"], stroke_width=f["braco_w"] + 2),
    )
    mao_m = shape(Circle, f["pele"], sw=7, radius=f["mao_r"]).move_to(mao)
    g.add(mao_m)
    if gesto == "apontar" and lado == face:
        ponta = mao + P(face * 0.42, 0.05)
        g.add(Line(mao, ponta, stroke_color=INK, stroke_width=16),
              Line(mao, ponta, stroke_color=f["pele"], stroke_width=9))
    if gesto == "contar" and lado == face:
        for k, a in enumerate((0.25, 0.0, -0.25)):
            ponta = mao + P(np.sin(a) * 0.3, 0.34)
            g.add(Line(mao, ponta, stroke_color=INK, stroke_width=13),
                  Line(mao, ponta, stroke_color=f["pele"], stroke_width=7))
    if gesto == "celular" and lado == face:
        g.add(shape(RoundedRectangle, "#20232B", sw=5, width=0.34, height=0.58, corner_radius=0.06)
              .move_to(mao + P(0.02 * face, 0.18)),
              RoundedRectangle(width=0.26, height=0.44, corner_radius=0.04, fill_color="#6FD3FF",
                               fill_opacity=0.9, stroke_width=0).move_to(mao + P(0.02 * face, 0.19)))
    return g


def maos_do_gesto(quem, gesto, face, t):
    """Alvo das duas mãos (esquerda, direita) em coordenadas locais."""
    f = FICHA[quem]
    o = f["ombro"]
    fr = face                                      # braço da frente = lado do outro
    rep = {-1: P(-o - 0.05, -2.05), 1: P(o + 0.05, -2.05)}
    alvo = dict(rep)
    if gesto == "explicar":
        alvo[fr] = P(fr * (o + 0.35), -0.75 + 0.14 * np.sin(t * 5.2))
    elif gesto == "apontar":
        alvo[fr] = P(fr * (o + 1.0), 0.05 + 0.04 * np.sin(t * 3))
    elif gesto == "bracos_cima":
        alvo = {s: P(s * (o + 0.45), 1.55 + 0.16 * np.sin(t * 9 + s)) for s in (-1, 1)}
    elif gesto == "facepalm":
        alvo[fr] = P(0.42 * fr, f["sob_y"] + 0.05)          # mão na testa, de lado
    elif gesto == "ombros":
        alvo = {s: P(s * (o + 0.55), -0.85) for s in (-1, 1)}
    elif gesto == "cruzar":
        alvo = {s: P(-s * 0.55, -1.05) for s in (-1, 1)}
    elif gesto == "peito":
        alvo[fr] = P(-0.3 * fr, -0.75 + 0.06 * abs(np.sin(t * 6)))
    elif gesto == "celular":
        alvo[fr] = P(fr * 0.62, -0.25)
    elif gesto == "maos_juntas":
        alvo = {s: P(s * 0.16, -0.95 + 0.03 * np.sin(t * 22)) for s in (-1, 1)}
    elif gesto == "contar":
        alvo[fr] = P(fr * (o + 0.25), 0.2)
    return alvo[-1], alvo[1]


# =============================================================================
#  O PERSONAGEM INTEIRO, A PARTIR DA POSE
# =============================================================================
def desenhar(quem, pose):
    """pose: expr, boca, palp, olhar(x,y), sob, tilt, bob, lean, maoE, maoD,
    gesto, escala_pop, t. Devolve VGroup em coordenadas locais (base do pescoço)."""
    est = _estaticos(quem)
    f = FICHA[quem]
    face = pose.get("face", 1)
    gesto = pose.get("gesto", "repouso")
    torso = est["torso"].copy()
    if face < 0:
        torso.flip(UP, about_point=ORIGIN)       # cachecol/ponta sempre do lado de fora
    cab = VGroup(est["atras"].copy(), est["cabeca"].copy(), _rosto(quem, pose, face), est["topo"].copy())
    if quem == "rubro":
        # aba do boné saindo por trás (lado oposto ao olhar)
        c = f["cab_centro"]
        aba = shape(RoundedRectangle, NEGRO, sw=8, width=0.78, height=0.26, corner_radius=0.12)
        aba.rotate(-0.25 * face).move_to(c + P(-0.98 * face, 0.66))
        cab.add_to_back(aba)
    pivo = P(0, 0.35)
    k = pose.get("escala_pop", 1.0)
    if k != 1.0:                                   # squash & stretch na troca de humor
        cab.stretch(k, 1, about_point=pivo).stretch(2 - k, 0, about_point=pivo)
    cab.rotate(pose.get("tilt", 0.0), about_point=pivo)
    cab.shift(UP * pose.get("cab_dy", 0.0))
    maos = [_braco(quem, -1, pose["maoE"], face, gesto), _braco(quem, 1, pose["maoD"], face, gesto)]
    corpo = VGroup(torso, *maos, cab) if gesto != "facepalm" else VGroup(torso, cab, *maos)
    corpo.shift(RIGHT * pose.get("lean", 0.0) + UP * pose.get("bob", 0.0))
    return corpo


# =============================================================================
#  A SALA (fundo em coordenadas do mundo, maior que o quadro p/ a câmera)
# =============================================================================
def sala(semente=3):
    rng = np.random.default_rng(semente)
    W, H = 11.0, 18.0
    parede = Rectangle(width=W, height=H, fill_color="#E9D6BC", fill_opacity=1, stroke_width=0)
    papel = VGroup(*[Rectangle(width=0.5, height=H, fill_color="#DEC8AA", fill_opacity=1,
                               stroke_width=0).move_to(P(x, 0)) for x in np.arange(-5.25, 5.5, 1.0)])
    rodape = Rectangle(width=W, height=0.35, fill_color="#8A6A52", fill_opacity=1, stroke_width=0).move_to(P(0, -3.1))
    chao = Rectangle(width=W, height=6, fill_color="#9C7B5F", fill_opacity=1, stroke_width=0).move_to(P(0, -6.25))
    tacos = VGroup(*[Line(P(-5.5, y), P(5.5, y), stroke_color="#86674D", stroke_width=4)
                     for y in np.arange(-3.6, -9, -0.55)])

    # janela da noite carioca: céu, lua, morro, prédios com luzinhas
    jx, jy, jw, jh = -2.35, 3.2, 3.2, 3.6
    moldura = shape(RoundedRectangle, "#F7F1E6", sw=10, width=jw + 0.4, height=jh + 0.4, corner_radius=0.1).move_to(P(jx, jy))
    ceu = Rectangle(width=jw, height=jh, fill_color="#1B2340", fill_opacity=1, stroke_width=0).move_to(P(jx, jy))
    lua = Circle(radius=0.32, fill_color="#F6E7B5", fill_opacity=1, stroke_width=0).move_to(P(jx + 0.85, jy + 1.1))
    morro = Polygon(P(jx - jw / 2, jy - 0.9), P(jx - 0.9, jy + 0.35), P(jx - 0.35, jy + 0.75),
                    P(jx + 0.2, jy + 0.1), P(jx + jw / 2, jy - 0.4), P(jx + jw / 2, jy - jh / 2),
                    P(jx - jw / 2, jy - jh / 2), fill_color="#2B3A52", fill_opacity=1, stroke_width=0)
    predios, luzes = VGroup(), VGroup()
    x = jx - jw / 2
    while x < jx + jw / 2 - 0.2:
        w = rng.uniform(0.35, 0.6)
        h = rng.uniform(0.7, 1.7)
        w = min(w, jx + jw / 2 - x)
        pr = Rectangle(width=w, height=h, fill_color="#121829", fill_opacity=1, stroke_width=0)
        pr.move_to(P(x + w / 2, jy - jh / 2 + h / 2))
        predios.add(pr)
        for yy in np.arange(jy - jh / 2 + 0.2, jy - jh / 2 + h - 0.1, 0.25):
            for xx in np.arange(x + 0.1, x + w - 0.05, 0.16):
                if rng.random() < 0.45:
                    luzes.add(Rectangle(width=0.07, height=0.09, fill_color="#FFD36B", fill_opacity=1,
                                        stroke_width=0).move_to(P(xx, yy)))
        x += w + 0.04
    cruz = VGroup(Line(P(jx, jy - jh / 2), P(jx, jy + jh / 2), stroke_color="#F7F1E6", stroke_width=10),
                  Line(P(jx - jw / 2, jy + 0.2), P(jx + jw / 2, jy + 0.2), stroke_color="#F7F1E6", stroke_width=10))
    cortina = VGroup(*[shape(RoundedRectangle, RUBRO_ESC, sw=7, width=0.55, height=jh + 0.9, corner_radius=0.2)
                       .move_to(P(jx + s * (jw / 2 + 0.25), jy - 0.1)) for s in (-1, 1)])
    janela = VGroup(moldura, ceu, lua, morro, predios, luzes, cruz, cortina)

    # bandeirão listrado na parede (sem escudo)
    bx, by = 2.45, 3.4
    bandeira = VGroup()
    for i in range(7):
        bandeira.add(Rectangle(width=2.6, height=0.36, fill_color=RUBRO if i % 2 == 0 else NEGRO,
                               fill_opacity=1, stroke_width=0).move_to(P(bx, by + 1.08 - 0.36 * i)))
    bandeira.add(Rectangle(width=2.6, height=2.52, stroke_color=INK, stroke_width=8).move_to(P(bx, by)))
    pregos = VGroup(*[Dot(P(bx + s * 1.2, by + 1.2), radius=0.07, color="#7A7A7A") for s in (-1, 1)])

    # prateleira: taça genérica, porta-retrato, planta
    prat = shape(Rectangle, "#7B5A43", sw=6, width=2.4, height=0.14).move_to(P(2.45, 1.45))
    taca = VGroup(shape(Polygon, OURO, *[P(2.0, 2.3), P(2.5, 2.3), P(2.36, 1.9), P(2.14, 1.9)]),
                  shape(Rectangle, OURO, sw=5, width=0.12, height=0.22).move_to(P(2.25, 1.72)),
                  shape(Rectangle, "#8A6A2A", sw=5, width=0.42, height=0.12).move_to(P(2.25, 1.56)))
    retrato = VGroup(shape(Rectangle, "#F7F1E6", sw=6, width=0.62, height=0.72).move_to(P(3.0, 1.9)),
                     Rectangle(width=0.44, height=0.26, fill_color=RUBRO, fill_opacity=1, stroke_width=0).move_to(P(3.0, 1.98)),
                     Rectangle(width=0.44, height=0.26, fill_color=NEGRO, fill_opacity=1, stroke_width=0).move_to(P(3.0, 1.72)))
    planta = VGroup(shape(Rectangle, "#B5643C", sw=5, width=0.34, height=0.3).move_to(P(1.55, 1.68)),
                    *[shape(Ellipse, "#3E8E5A", sw=5, width=0.18, height=0.5).rotate(a).move_to(P(1.55 + 0.18 * np.sin(a), 2.05))
                      for a in (-0.6, 0, 0.6)])
    # abajur de pé (brilho quente animado na cena)
    abajur = VGroup(Line(P(4.4, -3.0), P(4.4, 0.6), stroke_color=INK, stroke_width=8),
                    shape(Polygon, "#F4D58D", *[P(3.95, 0.6), P(4.85, 0.6), P(4.62, 1.3), P(4.18, 1.3)]))
    return VGroup(parede, papel, rodape, chao, tacos, janela, bandeira, pregos, prat, taca, retrato,
                  planta, abajur), luzes


def sofa():
    """Sofá em PRIMEIRO PLANO: cobre a cintura dos dois (eles estão sentados)."""
    enc = shape(RoundedRectangle, "#4A3E48", sw=12, width=9.4, height=2.1, corner_radius=0.4).move_to(P(0, -3.35))
    costura = Line(P(-4.4, -3.0), P(4.4, -3.0), stroke_color="#3A303A", stroke_width=6)
    assento = shape(RoundedRectangle, "#5B4D58", sw=12, width=10.2, height=1.9, corner_radius=0.4).move_to(P(0, -4.6))
    bracos = VGroup(*[shape(RoundedRectangle, "#4A3E48", sw=12, width=1.2, height=2.6, corner_radius=0.5)
                      .move_to(P(s * 4.75, -3.9)) for s in (-1, 1)])
    almofada = VGroup(shape(RoundedRectangle, RUBRO, sw=8, width=1.1, height=0.95, corner_radius=0.25)
                      .rotate(0.15).move_to(P(-3.55, -3.15)))
    for k in range(2):
        almofada.add(Rectangle(width=1.0, height=0.14, fill_color=NEGRO, fill_opacity=1, stroke_width=0)
                     .rotate(0.15).move_to(P(-3.55 + 0.02 * k, -3.0 - 0.3 * k)))
    # pipoca no braço do sofá + latinha genérica
    balde = VGroup(shape(Polygon, "#F7F1E6", *[P(3.25, -2.55), P(3.95, -2.55), P(3.85, -3.15), P(3.35, -3.15)]),
                   *[Line(P(3.33 + 0.12 * k, -2.57), P(3.38 + 0.1 * k, -3.13), stroke_color=RUBRO, stroke_width=7)
                     for k in range(5)],
                   *[shape(Circle, "#FFF3C9", sw=4, radius=0.1).move_to(P(3.3 + 0.13 * k, -2.48 + 0.05 * (k % 2)))
                     for k in range(6)])
    lata = VGroup(shape(RoundedRectangle, "#2F9E62", sw=6, width=0.32, height=0.52, corner_radius=0.06).move_to(P(4.55, -2.3)),
                  Rectangle(width=0.3, height=0.08, fill_color=WHITE, fill_opacity=1, stroke_width=0).move_to(P(4.55, -2.25)))
    return VGroup(bracos, enc, costura, assento, almofada, balde, lata)
