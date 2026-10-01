"""Mengão da Sala v3 — Juninho e Primo como rig SVG em camadas.

Cada parte do corpo é um grupo com id próprio, para o HyperFrames/GSAP animar
sem redesenhar nada:

    {q}            personagem inteiro (posição na cena)
    {q}-respira    tronco + cabeça (respiração: escala leve a partir da cintura)
    {q}-cabeca     cabeça (inclinação; pivô no pescoço)
    {q}-exp        <use> que aponta para a expressão ativa (olhos + sobrancelhas)
    {q}-pisca      pálpebras fechadas (opacidade 0/1 para piscar)
    {q}-boca       <use> que aponta para a boca de repouso ou o formato da fala
    {q}-ombroE/D   braço (pivô no ombro)  ·  {q}-cotoveloE/D  antebraço + mão

As expressões e as bocas ficam em <defs> (ids {q}-exp-<expr>, {q}-rep-<expr>,
{q}-fala-<forma>); a animação só troca o href. Os rotates dos braços usam o
formato fixo "rotate(<graus>)" para o GSAP interpolar o atributo.

q = "rubro" (Juninho) ou "primo" (Primo Secador). Personagens originais,
sem escudo, sem jogador real.
"""
from __future__ import annotations

INK = "#1A1214"
EXPRESSOES = ("neutra", "euforico", "indignado", "debochado", "rindo", "chocado", "sofrendo", "tenso")
FORMAS_FALA = ("fechada", "pequena", "media", "aberta", "redonda")
# visema do amplitude.py / Rhubarb -> formato de boca
VISEMA = {"X": "fechada", "A": "fechada", "B": "pequena", "C": "media", "D": "aberta",
          "E": "media", "F": "redonda", "G": "pequena", "H": "media"}
# gesto -> ((ombro, cotovelo) braço da frente/direito, (ombro, cotovelo) esquerdo), graus "para fora"
GESTOS = {
    "repouso": ((8, -8), (8, -8)),
    "explicar": ((38, -100), (10, -12)),
    "apontar": ((82, 8), (10, -10)),
    "bracos_cima": ((158, 16), (158, 16)),
    "facepalm": ((62, -172), (10, -10)),
    "ombros": ((58, 78), (58, 78)),
    "cruzar": ((22, -118), (22, -118)),
    "peito": ((22, -132), (8, -8)),
    "celular": ((26, -112), (10, -10)),
    "maos_juntas": ((30, -122), (30, -122)),
    "contar": ((60, -128), (12, -14)),
}

# Geometria de cada personagem (coordenadas locais; rosto centrado em 0,0)
GEO = {
    "rubro": dict(olho=((-62, -8), (62, -8)), olho_wh=(86, 104), iris="iris_j", olhar=(0.35, 0.08),
                  sobr=((22, -98), (70, -120), (112, -92)), sobr_w=20, boca=(0, 100), boca_k=1.0,
                  pal="#B97C52", pescoco=(0, 130), cintura=520, ombro=(168, 196),
                  braco=(160, 140), larg=70, manga="url(#rubro)", pele_braco="#B97C52", mao="#C08257",
                  sombra="#8E5634"),
    "primo": dict(olho=((-46, -18), (46, -18)), olho_wh=(70, 80), iris="iris_p", olhar=(-0.55, 0.18),
                  sobr=((16, -80), (55, -90), (92, -82)), sobr_w=15, boca=(0, 100), boca_k=0.82,
                  pal="#E6B48B", pescoco=(0, 140), cintura=560, ombro=(132, 214),
                  braco=(150, 135), larg=58, manga="url(#ceu)", pele_braco="#E2AE85", mao="#E8B48B",
                  sombra="#C98F67"),
}

# expressão -> pálpebra (0..1), sobrancelha (dy interno, dy externo, arco) por lado (esq, dir),
# íris (escala), olhar extra, extras
EXPR = {
    "neutra":    dict(pal=.12, sob=((0, 0, 0), (0, 0, 0))),
    "euforico":  dict(pal=0.0, sob=((-16, -14, -8), (-16, -14, -8)), bochecha=True),
    "indignado": dict(pal=.28, sob=((24, -12, 12), (24, -12, 12))),
    "debochado": dict(pal=.42, sob=((2, 6, 8), (-22, -28, -16)), olhar=(-0.25, 0.1)),
    "rindo":     dict(pal=1.0, sob=((-12, -10, -6), (-12, -10, -6)), bochecha=True),
    "chocado":   dict(pal=0.0, sob=((-32, -30, -12), (-32, -30, -12)), iris=.72),
    "sofrendo":  dict(pal=.38, sob=((-26, 14, 4), (-26, 14, 4)), olhar=(0, 0.55), lagrima=True),
    "tenso":     dict(pal=.2, sob=((14, 0, 6), (14, 0, 6)), suor=True),
}


def defs() -> str:
    return f'''<defs>
 <radialGradient id="pele_j" cx="45%" cy="38%" r="65%"><stop offset="0" stop-color="#C98A5E"/><stop offset="1" stop-color="#A86C44"/></radialGradient>
 <radialGradient id="pele_p" cx="45%" cy="38%" r="65%"><stop offset="0" stop-color="#F3CBA6"/><stop offset="1" stop-color="#DDA87F"/></radialGradient>
 <radialGradient id="iris_j" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="#9A6234"/><stop offset="1" stop-color="#3D2210"/></radialGradient>
 <radialGradient id="iris_p" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="#5FA37A"/><stop offset="1" stop-color="#1F4A33"/></radialGradient>
 <linearGradient id="rubro" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E3182F"/><stop offset="1" stop-color="#B10D22"/></linearGradient>
 <linearGradient id="ceu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#A9DDFA"/><stop offset="1" stop-color="#6FB6E3"/></linearGradient>
 <linearGradient id="cabelo_p" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3A2F44"/><stop offset="1" stop-color="#14101A"/></linearGradient>
 <linearGradient id="lente" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5B6B86"/><stop offset=".45" stop-color="#1D2330"/><stop offset="1" stop-color="#0B0E14"/></linearGradient>
 <clipPath id="clip_camisa_j"><path d="M-200,215 C-200,170 -150,140 -95,135 L95,135 C150,140 200,170 200,215 L210,520 L-210,520 Z"/></clipPath>
 {''.join(partes_rosto(q) for q in GEO)}
</defs>'''


# ------------------------------------------------------------------ rosto
def olho(cx, cy, w, h, iris, olhar=(0, 0), palpebra=0.0, uid="", pal="#B97C52", escala_iris=1.0):
    """palpebra 0..1 = quanto a pálpebra superior desce; 1 = olho fechado sorrindo."""
    if palpebra >= 1:
        return (f'<path d="M{cx-w/2+4},{cy+6} Q{cx},{cy-h*0.42} {cx+w/2-4},{cy+6}" fill="none" '
                f'stroke="{INK}" stroke-width="11" stroke-linecap="round"/>')
    ix, iy = cx + olhar[0] * w * 0.22, cy + olhar[1] * h * 0.2
    ri = w * 0.36 * escala_iris
    pid = f"clip-olho-{uid}"
    s = f'<clipPath id="{pid}"><ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}"/></clipPath>'
    s += f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="#FFFDF8" stroke="{INK}" stroke-width="7"/>'
    s += f'<g clip-path="url(#{pid})">'
    s += f'<circle cx="{ix:.1f}" cy="{iy:.1f}" r="{ri:.1f}" fill="url(#{iris})"/>'
    s += f'<circle cx="{ix:.1f}" cy="{iy:.1f}" r="{ri*0.5:.1f}" fill="#0E0809"/>'
    s += f'<circle cx="{ix+ri*0.35:.1f}" cy="{iy-ri*0.38:.1f}" r="{ri*0.3:.1f}" fill="#fff"/>'
    s += f'<circle cx="{ix-ri*0.35:.1f}" cy="{iy+ri*0.35:.1f}" r="{ri*0.13:.1f}" fill="#fff" opacity=".85"/>'
    if palpebra > 0:
        s += f'<rect x="{cx-w/2-6}" y="{cy-h/2-4}" width="{w+12}" height="{h*palpebra+4:.1f}" fill="{pal}"/>'
    s += '</g>'
    ly = cy - h / 2 + h * palpebra
    s += (f'<path d="M{cx-w/2-4},{ly+6:.1f} Q{cx},{(ly-10 if palpebra == 0 else ly-2):.1f} {cx+w/2+4},{ly+6:.1f}" '
          f'fill="none" stroke="{INK}" stroke-width="11" stroke-linecap="round"/>')
    return s


def sobrancelha(lado, base, dy, largura):
    """lado -1 = esquerda da tela. base = (interno, controle, externo) do lado direito."""
    (xi, yi), (xc, yc), (xo, yo) = base
    di, do, arco = dy
    return (f'<path d="M{lado*xi},{yi+di} Q{lado*xc},{yc+(di+do)/2+arco} {lado*xo},{yo+do}" fill="none" '
            f'stroke="{INK}" stroke-width="{largura}" stroke-linecap="round"/>')


def boca(forma, cx, cy, k=1.0, uid=""):
    """Bocas de fala (5 formatos) e de repouso (uma por expressão)."""
    def P(x, y):
        return f"{cx + x*k:.1f},{cy + y*k:.1f}"
    w = 9 if k >= 1 else 8
    escura, lingua = "#5C1219", "#E36C78"
    if forma == "fechada":
        return f'<path d="M{P(-34,2)} Q{P(0,8)} {P(34,2)}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>'
    if forma == "pequena":
        return f'<ellipse cx="{cx}" cy="{cy+4*k:.1f}" rx="{26*k:.1f}" ry="{10*k:.1f}" fill="{escura}" stroke="{INK}" stroke-width="{w}"/>'
    if forma == "media":
        return (f'<ellipse cx="{cx}" cy="{cy+6*k:.1f}" rx="{36*k:.1f}" ry="{19*k:.1f}" fill="{escura}" stroke="{INK}" stroke-width="{w}"/>'
                f'<path d="M{P(-26,-6)} Q{P(0,-10)} {P(26,-6)} L{P(24,1)} Q{P(0,-2)} {P(-24,1)} Z" fill="#fff"/>')
    if forma == "aberta":
        return (f'<path d="M{P(-44,-8)} Q{P(0,-12)} {P(44,-8)} Q{P(40,38)} {P(0,42)} Q{P(-40,38)} {P(-44,-8)} Z" fill="{escura}" stroke="{INK}" stroke-width="{w}" stroke-linejoin="round"/>'
                f'<path d="M{P(-36,-5)} Q{P(0,-8)} {P(36,-5)} L{P(33,6)} Q{P(0,3)} {P(-33,6)} Z" fill="#fff"/>'
                f'<ellipse cx="{cx+2*k:.1f}" cy="{cy+28*k:.1f}" rx="{20*k:.1f}" ry="{8*k:.1f}" fill="{lingua}"/>')
    if forma == "redonda":
        return f'<ellipse cx="{cx}" cy="{cy+8*k:.1f}" rx="{19*k:.1f}" ry="{23*k:.1f}" fill="{escura}" stroke="{INK}" stroke-width="{w}"/>'
    # ---- repouso por expressão
    if forma == "neutra":
        return f'<path d="M{P(-38,-2)} Q{P(0,16)} {P(38,-2)}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>'
    if forma == "euforico":
        return (f'<path d="M{P(-62,-26)} Q{P(0,-30)} {P(62,-26)} Q{P(55,28)} {P(0,32)} Q{P(-55,28)} {P(-62,-26)} Z" fill="{escura}" stroke="{INK}" stroke-width="{w}" stroke-linejoin="round"/>'
                f'<path d="M{P(-54,-22)} Q{P(0,-25)} {P(54,-22)} L{P(50,-8)} Q{P(0,-10)} {P(-50,-8)} Z" fill="#fff"/>'
                f'<ellipse cx="{cx+4*k:.1f}" cy="{cy+16*k:.1f}" rx="{30*k:.1f}" ry="{12*k:.1f}" fill="{lingua}"/>')
    if forma == "indignado":
        return f'<path d="M{P(-42,14)} Q{P(0,-8)} {P(42,14)}" fill="none" stroke="{INK}" stroke-width="{w+2}" stroke-linecap="round"/>'
    if forma == "debochado":
        return (f'<path d="M{P(-36,4)} Q{P(10,14)} {P(46,-10)}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>'
                f'<path d="M{P(40,-16)} Q{P(52,-8)} {P(48,2)}" fill="none" stroke="{INK}" stroke-width="{max(5, w-3)}" stroke-linecap="round"/>')
    if forma == "rindo":
        return (f'<path d="M{P(-52,-14)} Q{P(0,-18)} {P(52,-14)} Q{P(46,40)} {P(0,44)} Q{P(-46,40)} {P(-52,-14)} Z" fill="{escura}" stroke="{INK}" stroke-width="{w}" stroke-linejoin="round"/>'
                f'<path d="M{P(-44,-11)} Q{P(0,-14)} {P(44,-11)} L{P(41,1)} Q{P(0,-2)} {P(-41,1)} Z" fill="#fff"/>'
                f'<ellipse cx="{cx}" cy="{cy+30*k:.1f}" rx="{24*k:.1f}" ry="{10*k:.1f}" fill="{lingua}"/>')
    if forma == "chocado":
        return f'<ellipse cx="{cx}" cy="{cy+10*k:.1f}" rx="{24*k:.1f}" ry="{30*k:.1f}" fill="{escura}" stroke="{INK}" stroke-width="{w}"/>'
    if forma == "sofrendo":
        return f'<path d="M{P(-44,14)} Q{P(-22,0)} {P(0,10)} Q{P(22,0)} {P(44,14)}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>'
    if forma == "tenso":
        return (f'<rect x="{cx-40*k:.1f}" y="{cy-8*k:.1f}" width="{80*k:.1f}" height="{26*k:.1f}" rx="{10*k:.1f}" fill="#fff" stroke="{INK}" stroke-width="{w}"/>'
                + ''.join(f'<path d="M{P(x,-8)} L{P(x,18)}" stroke="{INK}" stroke-width="4"/>' for x in (-20, 0, 20))
                + f'<path d="M{P(-40,5)} L{P(40,5)}" stroke="{INK}" stroke-width="4"/>')
    raise ValueError(f"boca desconhecida: {forma}")


def partes_rosto(q: str) -> str:
    """<defs> de um personagem: uma expressão, uma boca de repouso e 5 bocas de fala."""
    g = GEO[q]
    (exl, eyl), (exr, eyr) = g["olho"]
    w, h = g["olho_wh"]
    s = ""
    for e in EXPRESSOES:
        p = EXPR[e]
        olhar = tuple(a + b for a, b in zip(g["olhar"], p.get("olhar", (0, 0))))
        corpo = ""
        for lado, (cx, cy) in ((-1, (exl, eyl)), (1, (exr, eyr))):
            corpo += olho(cx, cy, w, h, g["iris"], olhar, p["pal"], uid=f"{q}-{e}-{lado}",
                          pal=g["pal"], escala_iris=p.get("iris", 1.0))
            corpo += sobrancelha(lado, g["sobr"], p["sob"][0 if lado < 0 else 1], g["sobr_w"])
        if p.get("bochecha"):
            corpo += ''.join(f'<ellipse cx="{sx*(105 if q == "rubro" else 78)}" cy="{50 if q == "rubro" else 40}" rx="30" ry="16" fill="#E5536A" opacity=".45"/>' for sx in (-1, 1))
        if p.get("lagrima"):
            corpo += f'<path d="M{exl-10},{eyl+h/2} q-14,30 0,44 q14,-14 0,-44 Z" fill="#8FD3FF" stroke="{INK}" stroke-width="5"/>'
        if p.get("suor"):
            corpo += f'<path d="M{exr+w/2+20},{eyl-h/2-30} q-16,28 0,40 q16,-12 0,-40 Z" fill="#BDE8FF" stroke="{INK}" stroke-width="5"/>'
        s += f'<g id="{q}-exp-{e}">{corpo}</g>'
        s += f'<g id="{q}-rep-{e}">{boca(e, *g["boca"], k=g["boca_k"])}</g>'
    for f in FORMAS_FALA:
        s += f'<g id="{q}-fala-{f}">{boca(f, *g["boca"], k=g["boca_k"])}</g>'
    # pálpebras fechadas (piscar)
    tampa = ""
    for cx, cy in g["olho"]:
        tampa += f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2+3}" ry="{h/2+3}" fill="{g["pal"]}"/>'
        tampa += f'<path d="M{cx-w/2},{cy+4} Q{cx},{cy+18} {cx+w/2},{cy+4}" fill="none" stroke="{INK}" stroke-width="10" stroke-linecap="round"/>'
    s += f'<g id="{q}-tampa">{tampa}</g>'
    return s


# ------------------------------------------------------------------ braços
def mao_aberta(x, y, rot, pele, sombra, esc=1.0):
    dedos = ''.join(
        f'<rect x="{dx-11}" y="-78" width="24" height="{ln}" rx="12" transform="rotate({ang} 0 0)" fill="{pele}" stroke="{INK}" stroke-width="6"/>'
        for dx, ln, ang in ((-24, 62, -14), (-4, 70, -4), (16, 66, 6), (34, 54, 16)))
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({esc})">{dedos}'
            f'<rect x="-52" y="-30" width="30" height="58" rx="15" transform="rotate(-38 -37 0)" fill="{pele}" stroke="{INK}" stroke-width="6"/>'
            f'<ellipse cx="0" cy="0" rx="44" ry="40" fill="{pele}" stroke="{INK}" stroke-width="6"/>'
            f'<path d="M-20,18 Q0,30 22,16" fill="none" stroke="{sombra}" stroke-width="5" stroke-linecap="round"/></g>')


def celular(y):
    """Celular do Primo, perpendicular ao antebraço (tela para a câmera no gesto 'celular')."""
    return (f'<g transform="translate(0,{y}) rotate(-90)">'
            f'<rect x="-40" y="-70" width="80" height="140" rx="16" fill="#23262F" stroke="{INK}" stroke-width="7"/>'
            '<rect x="-31" y="-59" width="62" height="114" rx="10" fill="#8FE3FF"/>'
            '<rect x="-23" y="-46" width="46" height="8" rx="4" fill="#fff" opacity=".8"/>'
            '<rect x="-23" y="-30" width="34" height="8" rx="4" fill="#fff" opacity=".6"/>'
            '<rect x="-23" y="-12" width="46" height="36" rx="6" fill="#fff" opacity=".45"/></g>')


def braco(q: str, lado: int, gesto="repouso") -> str:
    """Braço com dois pivôs. lado 1 = direita da tela; -1 espelha. Ângulo positivo = para fora."""
    g = GEO[q]
    sup, ant = g["braco"]
    ox, oy = g["ombro"]
    o, c = GESTOS[gesto][0 if lado > 0 else 1]
    L = g["larg"]
    pele, mao = g["pele_braco"], g["mao"]
    lado_txt = "D" if lado > 0 else "E"
    mao_svg = mao_aberta(0, ant + 18, 180, mao, g["sombra"], .82 if q == "rubro" else .72)
    extra = celular(ant + 30) if (q == "primo" and lado > 0) else ""
    return (f'<g transform="translate({lado*ox},{oy}) scale({lado},1)">'
            f'<g id="{q}-ombro{lado_txt}" transform="rotate({-o})">'
            f'<path d="M0,0 L0,{sup}" stroke="{INK}" stroke-width="{L+14}" stroke-linecap="round"/>'
            f'<path d="M0,0 L0,{sup}" stroke="{pele}" stroke-width="{L}" stroke-linecap="round"/>'
            f'<g transform="translate(0,{sup})"><g id="{q}-cotovelo{lado_txt}" transform="rotate({-c})">'
            f'<path d="M0,0 L0,{ant}" stroke="{INK}" stroke-width="{L+12}" stroke-linecap="round"/>'
            f'<path d="M0,0 L0,{ant}" stroke="{pele}" stroke-width="{L-4}" stroke-linecap="round"/>'
            f'{extra}{mao_svg}</g></g>'
            f'<circle cx="0" cy="8" r="{L*0.8:.0f}" fill="{g["manga"]}" stroke="{INK}" stroke-width="7"/>'
            f'<path d="M{-L*0.8:.0f},{L*0.55:.0f} Q0,{L*0.95:.0f} {L*0.8:.0f},{L*0.55:.0f}" fill="none" stroke="#fff" stroke-width="7" opacity=".8"/>'
            f'</g></g>')


def _uses(q, expr):
    return (f'<use id="{q}-exp" href="#{q}-exp-{expr}"/>'
            f'<use id="{q}-pisca" href="#{q}-tampa" opacity="0"/>')


def _boca_use(q, expr):
    return f'<use id="{q}-boca" href="#{q}-rep-{expr}"/>'


def _pivo(q, conteudo):
    """Cabeça com pivô no pescoço (rotate em torno da origem do grupo)."""
    px, py = GEO[q]["pescoco"]
    return (f'<g transform="translate({px},{py})"><g id="{q}-cabeca" transform="rotate(0)">'
            f'<g transform="translate({-px},{-py})">{conteudo}</g></g></g>')


def _respira(q, conteudo):
    c = GEO[q]["cintura"]
    return f'<g id="{q}-respira" transform="translate(0,{c}) scale(1,1) translate(0,-{c})">{conteudo}</g>'


# ------------------------------------------------------------------ personagens
def juninho(expr="neutra", gesto="repouso"):
    pele, sombra = "url(#pele_j)", "#8E5634"
    tronco_d = "M-200,215 C-200,170 -150,140 -95,135 L95,135 C150,140 200,170 200,215 L210,520 L-210,520 Z"
    tronco = f'<path d="{tronco_d}" fill="url(#rubro)" stroke="{INK}" stroke-width="10"/>'
    tronco += '<g clip-path="url(#clip_camisa_j)">'
    for y in range(190, 520, 84):
        tronco += f'<path d="M-230,{y} Q0,{y+14} 230,{y} L230,{y+40} Q0,{y+54} -230,{y+40} Z" fill="#17120F"/>'
    tronco += '<path d="M-210,180 C-150,250 -140,400 -160,520 L-210,520 Z" fill="#000" opacity=".22"/>'
    tronco += '<path d="M120,150 C170,170 190,210 190,260" fill="none" stroke="#fff" stroke-width="10" opacity=".25" stroke-linecap="round"/>'
    tronco += '</g>'
    tronco += f'<path d="{tronco_d}" fill="none" stroke="{INK}" stroke-width="10"/>'
    tronco += f'<path d="M-62,110 L62,110 L58,160 Q0,185 -58,160 Z" fill="#A86C44" stroke="{INK}" stroke-width="8"/>'
    tronco += f'<path d="M-78,140 Q0,200 78,140" fill="none" stroke="#17120F" stroke-width="20" stroke-linecap="round"/>'

    cab = ""
    for (cx, cy, r) in ((-150, 10, 42), (-165, -40, 40), (150, 10, 42), (165, -40, 40), (-120, 55, 34), (120, 55, 34)):
        cab += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#221714" stroke="{INK}" stroke-width="7"/>'
    for sx in (-1, 1):
        cab += f'<ellipse cx="{sx*168}" cy="20" rx="28" ry="38" fill="#B47650" stroke="{INK}" stroke-width="7"/>'
        cab += f'<path d="M{sx*172},5 Q{sx*160},20 {sx*170},38" fill="none" stroke="{sombra}" stroke-width="5"/>'
    rosto = "M-160,-30 C-165,-140 -90,-175 0,-175 C90,-175 165,-140 160,-30 C158,60 110,128 0,135 C-110,128 -158,60 -160,-30 Z"
    cab += f'<path d="{rosto}" fill="{pele}" stroke="{INK}" stroke-width="12"/>'
    cab += '<path d="M-120,60 C-90,118 -40,130 0,130 C40,130 90,118 120,60 C80,90 -80,90 -120,60 Z" fill="#3A2418" opacity=".18"/>'
    for sx in (-1, 1):
        cab += f'<ellipse cx="{sx*105}" cy="50" rx="32" ry="18" fill="#E5536A" opacity=".3"/>'
    cab += _uses("rubro", expr)
    cab += f'<path d="M-6,32 Q-24,52 -6,60 Q8,64 22,56" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
    cab += _boca_use("rubro", expr)
    # boné virado pra trás
    cab += f'<path d="M-205,-118 Q-235,-80 -190,-62 L-120,-96 Z" fill="#17120F" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
    cab += f'<path d="M-168,-70 C-175,-190 -80,-232 0,-232 C80,-232 175,-190 168,-70 Q0,-110 -168,-70 Z" fill="url(#rubro)" stroke="{INK}" stroke-width="11"/>'
    cab += '<path d="M-150,-120 C-110,-200 -40,-218 20,-220" fill="none" stroke="#fff" stroke-width="12" opacity=".3" stroke-linecap="round"/>'
    cab += f'<path d="M-168,-70 Q0,-110 168,-70 L164,-50 Q0,-90 -164,-50 Z" fill="#17120F" stroke="{INK}" stroke-width="7"/>'
    cab += f'<path d="M-36,-96 Q0,-108 36,-96 L30,-70 Q0,-80 -30,-70 Z" fill="#221714" stroke="{INK}" stroke-width="6"/>'
    cab += '<circle cx="0" cy="-232" r="11" fill="#17120F"/>'

    corpo = _respira("rubro", tronco + _pivo("rubro", cab))
    return f'<g id="rubro-rig">{corpo}{braco("rubro", -1, gesto)}{braco("rubro", 1, gesto)}</g>'


def primo(expr="debochado", gesto="celular"):
    pele = "url(#pele_p)"
    tronco_d = "M-150,250 C-150,205 -110,180 -70,176 L70,176 C110,180 150,205 150,250 L160,560 L-160,560 Z"
    tronco = f'<path d="{tronco_d}" fill="url(#ceu)" stroke="{INK}" stroke-width="10"/>'
    tronco += '<path d="M-160,230 C-115,300 -110,450 -125,560 L-160,560 Z" fill="#1B3B5A" opacity=".22"/>'
    tronco += '<path d="M-150,480 L150,480" stroke="#fff" stroke-width="10" opacity=".9"/>'
    tronco += f'<path d="M-36,120 L36,120 L40,200 Q0,214 -40,200 Z" fill="#E2AE85" stroke="{INK}" stroke-width="8"/>'
    tronco += f'<path d="M-6,182 L-90,176 L-64,236 Z" fill="#fff" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
    tronco += f'<path d="M6,182 L90,176 L64,236 Z" fill="#fff" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
    tronco += f'<path d="M-22,186 L22,186 L0,250 Z" fill="#E2AE85" stroke="{INK}" stroke-width="6"/>'
    tronco += '<path d="M-30,190 Q0,236 30,190" fill="none" stroke="#F2C14E" stroke-width="7"/>'
    tronco += '<circle cx="0" cy="226" r="8" fill="#F2C14E" stroke="#A9781E" stroke-width="3"/>'
    tronco += f'<circle cx="0" cy="282" r="6" fill="{INK}"/><circle cx="0" cy="312" r="6" fill="{INK}"/>'

    cab = ""
    for sx in (-1, 1):
        cab += f'<ellipse cx="{sx*122}" cy="0" rx="22" ry="34" fill="#E2AE85" stroke="{INK}" stroke-width="7"/>'
    rosto = "M-118,-40 C-125,-170 -60,-205 0,-205 C60,-205 125,-170 118,-40 C112,70 70,140 0,145 C-70,140 -112,70 -118,-40 Z"
    cab += f'<path d="{rosto}" fill="{pele}" stroke="{INK}" stroke-width="12"/>'
    cab += '<path d="M-60,110 C-30,140 30,140 60,110 C30,124 -30,124 -60,110 Z" fill="#7FD6FF" opacity=".18"/>'
    cab += _uses("primo", expr)
    cab += f'<path d="M6,-10 Q26,40 4,56 Q-8,60 -18,54" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
    cab += _boca_use("primo", expr)
    cab += f'<path d="M-44,74 Q-20,62 0,70 Q20,62 44,74" fill="none" stroke="#1E1A22" stroke-width="9" stroke-linecap="round"/>'
    cab += f'<path d="M-122,-60 C-140,-160 -110,-230 -30,-262 C40,-290 120,-262 132,-190 C140,-140 128,-90 120,-60 C110,-120 80,-150 30,-158 C-30,-166 -90,-140 -122,-60 Z" fill="url(#cabelo_p)" stroke="{INK}" stroke-width="11"/>'
    cab += '<path d="M-60,-240 C-10,-268 60,-262 100,-220" fill="none" stroke="#8C7FA3" stroke-width="10" opacity=".7" stroke-linecap="round"/>'
    cab += '<path d="M-90,-170 C-50,-210 20,-220 70,-200" fill="none" stroke="#8C7FA3" stroke-width="6" opacity=".5" stroke-linecap="round"/>'
    for sx in (-1, 1):
        cab += f'<path d="M{sx*10},-150 Q{sx*14},-120 {sx*48},-114 Q{sx*92},-112 {sx*96},-146 Q{sx*94},-168 {sx*52},-168 Q{sx*12},-168 {sx*10},-150 Z" fill="url(#lente)" stroke="{INK}" stroke-width="7"/>'
        cab += f'<path d="M{sx*30},-156 L{sx*48},-150" stroke="#fff" stroke-width="5" opacity=".7" stroke-linecap="round"/>'
    cab += f'<path d="M-10,-152 Q0,-160 10,-152" fill="none" stroke="{INK}" stroke-width="7"/>'

    corpo = _respira("primo", tronco + _pivo("primo", cab))
    return f'<g id="primo-rig">{corpo}{braco("primo", -1, gesto)}{braco("primo", 1, gesto)}</g>'


IDS_ANIMADOS = ("respira", "cabeca", "exp", "pisca", "boca", "ombroE", "ombroD", "cotoveloE", "cotoveloD")


def ids(q: str) -> list[str]:
    return [f"{q}-{p}" for p in IDS_ANIMADOS]
