"""Mengão da Sala v3 — personagens em SVG em camadas (rig por partes)."""
INK = "#1A1214"

def defs():
    return f'''
<defs>
 <radialGradient id="pele_j" cx="45%" cy="38%" r="65%"><stop offset="0" stop-color="#C98A5E"/><stop offset="1" stop-color="#A86C44"/></radialGradient>
 <radialGradient id="pele_p" cx="45%" cy="38%" r="65%"><stop offset="0" stop-color="#F3CBA6"/><stop offset="1" stop-color="#DDA87F"/></radialGradient>
 <radialGradient id="iris_j" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="#9A6234"/><stop offset="1" stop-color="#3D2210"/></radialGradient>
 <radialGradient id="iris_p" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="#5FA37A"/><stop offset="1" stop-color="#1F4A33"/></radialGradient>
 <linearGradient id="rubro" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E3182F"/><stop offset="1" stop-color="#B10D22"/></linearGradient>
 <linearGradient id="ceu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#A9DDFA"/><stop offset="1" stop-color="#6FB6E3"/></linearGradient>
 <linearGradient id="cabelo_p" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3A2F44"/><stop offset="1" stop-color="#14101A"/></linearGradient>
 <linearGradient id="lente" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5B6B86"/><stop offset=".45" stop-color="#1D2330"/><stop offset="1" stop-color="#0B0E14"/></linearGradient>
 <clipPath id="clip_camisa_j"><path d="M-200,215 C-200,170 -150,140 -95,135 L95,135 C150,140 200,170 200,215 L210,520 L-210,520 Z"/></clipPath>
</defs>'''

def olho(cx, cy, w, h, iris, olhar=(0, 0), palpebra=0.0, lado=1):
    """palpebra 0..1 = quanto a pálpebra superior desce."""
    ix, iy = cx + olhar[0] * w * 0.22, cy + olhar[1] * h * 0.2
    ri = w * 0.36
    pid = f"o{abs(int(cx))}{abs(int(cy))}{iris[-1]}"
    s = f'<clipPath id="{pid}"><ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}"/></clipPath>'
    s += f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="#FFFDF8" stroke="{INK}" stroke-width="7"/>'
    s += f'<g clip-path="url(#{pid})">'
    s += f'<circle cx="{ix}" cy="{iy}" r="{ri}" fill="url(#{iris})"/>'
    s += f'<circle cx="{ix}" cy="{iy}" r="{ri*0.5}" fill="#0E0809"/>'
    s += f'<circle cx="{ix+ri*0.35}" cy="{iy-ri*0.38}" r="{ri*0.3}" fill="#fff"/>'
    s += f'<circle cx="{ix-ri*0.35}" cy="{iy+ri*0.35}" r="{ri*0.13}" fill="#fff" opacity=".85"/>'
    if palpebra > 0:
        top = cy - h / 2 - 4
        s += f'<rect x="{cx-w/2-6}" y="{top}" width="{w+12}" height="{h*palpebra+4}" fill="var(--pal)"/>'
    s += '</g>'
    # linha grossa da pálpebra superior
    ly = cy - h / 2 + h * palpebra
    s += f'<path d="M{cx-w/2-4},{ly+6} Q{cx},{ly-10 if palpebra==0 else ly-2} {cx+w/2+4},{ly+6}" fill="none" stroke="{INK}" stroke-width="11" stroke-linecap="round"/>'
    return s

def mao_aberta(x, y, rot, pele, sombra, esc=1.0):
    dedos = ''.join(
        f'<rect x="{dx-11}" y="-78" width="24" height="{ln}" rx="12" transform="rotate({ang} 0 0)" fill="{pele}" stroke="{INK}" stroke-width="6"/>'
        for dx, ln, ang in ((-24, 62, -14), (-4, 70, -4), (16, 66, 6), (34, 54, 16)))
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({esc})">{dedos}'
            f'<rect x="-52" y="-30" width="30" height="58" rx="15" transform="rotate(-38 -37 0)" fill="{pele}" stroke="{INK}" stroke-width="6"/>'
            f'<ellipse cx="0" cy="0" rx="44" ry="40" fill="{pele}" stroke="{INK}" stroke-width="6"/>'
            f'<path d="M-20,18 Q0,30 22,16" fill="none" stroke="{sombra}" stroke-width="5" stroke-linecap="round"/></g>')

def braco(x0, y0, x1, y1, manga, pele, larg=74, curva=40):
    mx, my = (x0 + x1) / 2 + curva, (y0 + y1) / 2
    # manga curta + antebraço
    return (f'<path d="M{x0},{y0} Q{mx},{my} {x1},{y1}" fill="none" stroke="{INK}" stroke-width="{larg+14}" stroke-linecap="round"/>'
            f'<path d="M{x0},{y0} Q{mx},{my} {x1},{y1}" fill="none" stroke="{pele}" stroke-width="{larg}" stroke-linecap="round"/>'
            f'<circle cx="{x0}" cy="{y0}" r="{larg*0.78}" fill="{manga}" stroke="{INK}" stroke-width="7"/>')

def juninho(expr="euforico"):
    pele, sombra = "url(#pele_j)", "#8E5634"
    s = '<g style="--pal:#B97C52">'
    # braços pra cima atrás do corpo
    s += braco(-165, 210, -255, -40, "url(#rubro)", "#B97C52", curva=-30)
    s += braco(165, 210, 255, -40, "url(#rubro)", "#B97C52", curva=30)
    s += mao_aberta(-262, -78, -18, "#C08257", sombra)
    s += mao_aberta(262, -78, 18, "#C08257", sombra)
    # tronco
    tronco = "M-200,215 C-200,170 -150,140 -95,135 L95,135 C150,140 200,170 200,215 L210,520 L-210,520 Z"
    s += f'<path d="{tronco}" fill="url(#rubro)" stroke="{INK}" stroke-width="10"/>'
    s += '<g clip-path="url(#clip_camisa_j)">'
    for y in range(190, 520, 84):
        s += f'<path d="M-230,{y} Q0,{y+14} 230,{y} L230,{y+40} Q0,{y+54} -230,{y+40} Z" fill="#17120F"/>'
    s += '<path d="M-210,180 C-150,250 -140,400 -160,520 L-210,520 Z" fill="#000" opacity=".22"/>'
    s += '<path d="M120,150 C170,170 190,210 190,260" fill="none" stroke="#fff" stroke-width="10" opacity=".25" stroke-linecap="round"/>'
    s += '</g>'
    s += f'<path d="{tronco}" fill="none" stroke="{INK}" stroke-width="10"/>'
    # gola e pescoço
    s += f'<path d="M-62,110 L62,110 L58,160 Q0,185 -58,160 Z" fill="#A86C44" stroke="{INK}" stroke-width="8"/>'
    s += f'<path d="M-78,140 Q0,200 78,140" fill="none" stroke="#17120F" stroke-width="20" stroke-linecap="round"/>'
    # cabelo cacheado atrás (sai por baixo do boné)
    for (cx, cy, r) in ((-150, 10, 42), (-165, -40, 40), (150, 10, 42), (165, -40, 40), (-120, 55, 34), (120, 55, 34)):
        s += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#221714" stroke="{INK}" stroke-width="7"/>'
    # orelhas
    for sx in (-1, 1):
        s += f'<ellipse cx="{sx*168}" cy="20" rx="28" ry="38" fill="#B47650" stroke="{INK}" stroke-width="7"/>'
        s += f'<path d="M{sx*172},5 Q{sx*160},20 {sx*170},38" fill="none" stroke="{sombra}" stroke-width="5"/>'
    # rosto
    rosto = "M-160,-30 C-165,-140 -90,-175 0,-175 C90,-175 165,-140 160,-30 C158,60 110,128 0,135 C-110,128 -158,60 -160,-30 Z"
    s += f'<path d="{rosto}" fill="{pele}" stroke="{INK}" stroke-width="12"/>'
    s += '<path d="M-120,60 C-90,118 -40,130 0,130 C40,130 90,118 120,60 C80,90 -80,90 -120,60 Z" fill="#3A2418" opacity=".18"/>'
    # bochechas
    for sx in (-1, 1):
        s += f'<ellipse cx="{sx*105}" cy="50" rx="32" ry="18" fill="#E5536A" opacity=".35"/>'
    # olhos e sobrancelhas
    s += olho(-62, -8, 86, 104, "iris_j", (0.15, 0.1))
    s += olho(62, -8, 86, 104, "iris_j", (0.15, 0.1))
    s += f'<path d="M-112,-92 Q-70,-120 -22,-98" fill="none" stroke="{INK}" stroke-width="20" stroke-linecap="round"/>'
    s += f'<path d="M22,-98 Q70,-120 112,-92" fill="none" stroke="{INK}" stroke-width="20" stroke-linecap="round"/>'
    # nariz
    s += f'<path d="M-6,32 Q-24,52 -6,60 Q8,64 22,56" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
    # boca aberta de comemoração
    s += f'<path d="M-62,74 Q0,70 62,74 Q55,128 0,132 Q-55,128 -62,74 Z" fill="#5C1219" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
    s += '<path d="M-54,78 Q0,75 54,78 L50,92 Q0,90 -50,92 Z" fill="#fff"/>'
    s += '<ellipse cx="4" cy="116" rx="30" ry="12" fill="#E36C78"/>'
    # boné virado pra trás
    s += f'<path d="M-205,-118 Q-235,-80 -190,-62 L-120,-96 Z" fill="#17120F" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
    s += f'<path d="M-168,-70 C-175,-190 -80,-232 0,-232 C80,-232 175,-190 168,-70 Q0,-110 -168,-70 Z" fill="url(#rubro)" stroke="{INK}" stroke-width="11"/>'
    s += '<path d="M-150,-120 C-110,-200 -40,-218 20,-220" fill="none" stroke="#fff" stroke-width="12" opacity=".3" stroke-linecap="round"/>'
    s += f'<path d="M-168,-70 Q0,-110 168,-70 L164,-50 Q0,-90 -164,-50 Z" fill="#17120F" stroke="{INK}" stroke-width="7"/>'
    # abertura do regulador (cabelo aparecendo)
    s += f'<path d="M-36,-96 Q0,-108 36,-96 L30,-70 Q0,-80 -30,-70 Z" fill="#221714" stroke="{INK}" stroke-width="6"/>'
    s += f'<circle cx="0" cy="-232" r="11" fill="#17120F"/>'
    s += '</g>'
    return s

def primo(expr="debochado"):
    pele = "url(#pele_p)"
    s = '<g style="--pal:#E6B48B">'
    # tronco: polo azul-celeste
    tronco = "M-150,250 C-150,205 -110,180 -70,176 L70,176 C110,180 150,205 150,250 L160,560 L-160,560 Z"
    s += f'<path d="{tronco}" fill="url(#ceu)" stroke="{INK}" stroke-width="10"/>'
    s += '<path d="M-160,230 C-115,300 -110,450 -125,560 L-160,560 Z" fill="#1B3B5A" opacity=".22"/>'
    s += '<path d="M-150,480 L150,480" stroke="#fff" stroke-width="10" opacity=".9"/>'
    # pescoço comprido
    s += f'<path d="M-36,120 L36,120 L40,200 Q0,214 -40,200 Z" fill="#E2AE85" stroke="{INK}" stroke-width="8"/>'
    # gola polo branca
    s += f'<path d="M-6,182 L-90,176 L-64,236 Z" fill="#fff" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
    s += f'<path d="M6,182 L90,176 L64,236 Z" fill="#fff" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
    s += f'<path d="M-22,186 L22,186 L0,250 Z" fill="#E2AE85" stroke="{INK}" stroke-width="6"/>'
    s += '<path d="M-30,190 Q0,236 30,190" fill="none" stroke="#F2C14E" stroke-width="7"/>'
    s += '<circle cx="0" cy="226" r="8" fill="#F2C14E" stroke="#A9781E" stroke-width="3"/>'
    s += f'<circle cx="0" cy="282" r="6" fill="{INK}"/><circle cx="0" cy="312" r="6" fill="{INK}"/>'
    # braço segurando o celular na altura do peito
    s += f'<path d="M128,250 Q170,340 70,362" fill="none" stroke="{INK}" stroke-width="78" stroke-linecap="round"/>'
    s += f'<path d="M128,250 Q170,340 70,362" fill="none" stroke="#E2AE85" stroke-width="64" stroke-linecap="round"/>'
    s += f'<path d="M78,190 C130,192 168,222 172,290 L112,312 C110,270 96,236 70,214 Z" fill="url(#ceu)" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
    s += f'<path d="M112,312 L172,290" stroke="#fff" stroke-width="8"/>'
    # celular
    s += f'<rect x="10" y="250" width="86" height="150" rx="16" fill="#23262F" stroke="{INK}" stroke-width="7" transform="rotate(-12 53 325)"/>'
    s += '<rect x="20" y="262" width="66" height="122" rx="10" fill="#8FE3FF" transform="rotate(-12 53 325)"/>'
    s += '<g transform="rotate(-12 53 325)"><rect x="28" y="276" width="50" height="8" rx="4" fill="#fff" opacity=".8"/><rect x="28" y="292" width="36" height="8" rx="4" fill="#fff" opacity=".6"/><rect x="28" y="312" width="50" height="40" rx="6" fill="#ffffff" opacity=".45"/></g>'
    s += f'<ellipse cx="62" cy="372" rx="46" ry="36" fill="#E8B48B" stroke="{INK}" stroke-width="6"/>'
    s += f'<rect x="76" y="300" width="24" height="52" rx="12" fill="#E8B48B" stroke="{INK}" stroke-width="6" transform="rotate(-30 88 326)"/>'
    # orelhas
    for sx in (-1, 1):
        s += f'<ellipse cx="{sx*122}" cy="0" rx="22" ry="34" fill="#E2AE85" stroke="{INK}" stroke-width="7"/>'
    # rosto comprido
    rosto = "M-118,-40 C-125,-170 -60,-205 0,-205 C60,-205 125,-170 118,-40 C112,70 70,140 0,145 C-70,140 -112,70 -118,-40 Z"
    s += f'<path d="{rosto}" fill="{pele}" stroke="{INK}" stroke-width="12"/>'
    # luz azul do celular no queixo
    s += '<path d="M-60,110 C-30,140 30,140 60,110 C30,124 -30,124 -60,110 Z" fill="#7FD6FF" opacity=".18"/>'
    # olhos meio fechados (debochado), olhando de lado
    s += olho(-46, -18, 70, 80, "iris_p", (-0.6, 0.2), palpebra=0.42)
    s += olho(46, -18, 70, 80, "iris_p", (-0.6, 0.2), palpebra=0.42)
    # sobrancelhas: uma reta, outra erguida
    s += f'<path d="M-92,-82 Q-55,-90 -16,-80" fill="none" stroke="{INK}" stroke-width="15" stroke-linecap="round"/>'
    s += f'<path d="M18,-100 Q55,-132 92,-108" fill="none" stroke="{INK}" stroke-width="15" stroke-linecap="round"/>'
    # nariz comprido
    s += f'<path d="M6,-10 Q26,40 4,56 Q-8,60 -18,54" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
    # bigodinho fino
    s += f'<path d="M-44,76 Q-20,64 0,72 Q20,64 44,76" fill="none" stroke="#1E1A22" stroke-width="9" stroke-linecap="round"/>'
    # sorriso de canto
    s += f'<path d="M-36,98 Q10,110 46,86" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
    s += f'<path d="M40,80 Q52,88 48,98" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
    # topete com gel
    s += f'<path d="M-122,-60 C-140,-160 -110,-230 -30,-262 C40,-290 120,-262 132,-190 C140,-140 128,-90 120,-60 C110,-120 80,-150 30,-158 C-30,-166 -90,-140 -122,-60 Z" fill="url(#cabelo_p)" stroke="{INK}" stroke-width="11"/>'
    s += '<path d="M-60,-240 C-10,-268 60,-262 100,-220" fill="none" stroke="#8C7FA3" stroke-width="10" opacity=".7" stroke-linecap="round"/>'
    s += '<path d="M-90,-170 C-50,-210 20,-220 70,-200" fill="none" stroke="#8C7FA3" stroke-width="6" opacity=".5" stroke-linecap="round"/>'
    # óculos escuros na testa
    for sx in (-1, 1):
        s += f'<path d="M{sx*10},-150 Q{sx*14},-120 {sx*48},-114 Q{sx*92},-112 {sx*96},-146 Q{sx*94},-168 {sx*52},-168 Q{sx*12},-168 {sx*10},-150 Z" fill="url(#lente)" stroke="{INK}" stroke-width="7"/>'
        s += f'<path d="M{sx*30},-156 L{sx*48},-150" stroke="#fff" stroke-width="5" opacity=".7" stroke-linecap="round"/>'
    s += f'<path d="M-10,-152 Q0,-160 10,-152" fill="none" stroke="{INK}" stroke-width="7"/>'
    s += '</g>'
    return s
