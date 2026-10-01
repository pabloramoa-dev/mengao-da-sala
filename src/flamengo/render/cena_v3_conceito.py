import cairosvg, sys
from personagens import defs, juninho, primo, INK
W, H = 1080, 1920
def fundo():
    s = f'''<defs>
 <radialGradient id="tvluz" cx="50%" cy="78%" r="70%"><stop offset="0" stop-color="#3B5BD9" stop-opacity=".55"/><stop offset="1" stop-color="#0D0B1E" stop-opacity="0"/></radialGradient>
 <linearGradient id="parede" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2A1630"/><stop offset="1" stop-color="#3E1A2E"/></linearGradient>
 <linearGradient id="sofa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8E1F2E"/><stop offset="1" stop-color="#5E1220"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#parede)"/>'''
    # papel de parede listrado sutil
    for x in range(0, W, 90):
        s += f'<rect x="{x}" y="0" width="45" height="{H}" fill="#fff" opacity=".025"/>'
    # janela com cidade à noite
    s += f'<rect x="60" y="430" width="330" height="420" rx="10" fill="#141A3A" stroke="{INK}" stroke-width="12"/>'
    s += '<circle cx="300" cy="510" r="38" fill="#FBE7A6"/>'
    s += '<path d="M60,760 L130,640 L200,720 L250,610 L330,700 L390,660 L390,850 L60,850 Z" fill="#2B3566"/>'
    for (x, w, h) in ((80, 60, 120), (150, 50, 160), (215, 70, 100), (300, 60, 140)):
        s += f'<rect x="{x}" y="{850-h}" width="{w}" height="{h}" fill="#0E1230"/>'
        for yy in range(850-h+15, 840, 26):
            for xx in range(x+10, x+w-8, 18):
                if (xx*7+yy) % 3: s += f'<rect x="{xx}" y="{yy}" width="7" height="10" fill="#FFD66B" opacity=".8"/>'
    s += f'<path d="M225,430 L225,850 M60,640 L390,640" stroke="{INK}" stroke-width="10"/>'
    # flâmula rubro-negra genérica (sem escudo)
    s += f'<path d="M760,420 L1000,420 L880,640 Z" fill="#D0102C" stroke="{INK}" stroke-width="9"/>'
    s += '<path d="M790,474 L970,474 L951,508 L809,508 Z M827,540 L933,540 L914,574 L846,574 Z" fill="#17120F"/>'
    # prateleira com troféu
    s += f'<rect x="700" y="760" width="320" height="22" rx="6" fill="#6B4630" stroke="{INK}" stroke-width="7"/>'
    s += f'<path d="M820,680 L880,680 Q884,730 850,738 Q816,730 820,680 Z" fill="#F2C14E" stroke="{INK}" stroke-width="7"/><rect x="836" y="738" width="28" height="22" fill="#F2C14E" stroke="{INK}" stroke-width="6"/>'
    s += f'<rect x="930" y="700" width="60" height="60" rx="6" fill="#2D2530" stroke="{INK}" stroke-width="6"/><rect x="938" y="708" width="44" height="22" fill="#D0102C"/><rect x="938" y="730" width="44" height="22" fill="#17120F"/>'
    s += f'<rect width="{W}" height="{H}" fill="url(#tvluz)"/>'
    return s
def sofa():
    s = f'<path d="M-20,1280 Q-20,1220 60,1215 L1020,1215 Q1100,1220 1100,1280 L1100,1560 L-20,1560 Z" fill="url(#sofa)" stroke="{INK}" stroke-width="12"/>'
    s += f'<path d="M40,1330 L1040,1330" stroke="#3E0B15" stroke-width="8" opacity=".6"/>'
    s += f'<rect x="-30" y="1260" width="150" height="300" rx="50" fill="#7A1827" stroke="{INK}" stroke-width="11"/>'
    s += f'<rect x="960" y="1260" width="150" height="300" rx="50" fill="#7A1827" stroke="{INK}" stroke-width="11"/>'
    # almofada listrada
    s += f'<g transform="translate(150,1250) rotate(-10)"><rect width="150" height="120" rx="34" fill="#D0102C" stroke="{INK}" stroke-width="9"/><rect x="6" y="30" width="138" height="22" fill="#17120F"/><rect x="6" y="74" width="138" height="22" fill="#17120F"/></g>'
    # pipoca
    s += f'<g transform="translate(930,1185) scale(0.8)"><path d="M0,40 L110,40 L95,170 L15,170 Z" fill="#fff" stroke="{INK}" stroke-width="8"/>'
    for x in (22, 48, 74): s += f'<path d="M{x},42 L{x-2},168" stroke="#D0102C" stroke-width="12"/>'
    for (x, y) in ((10, 30), (35, 18), (62, 14), (88, 22), (105, 34), (50, 0), (80, 4)): s += f'<circle cx="{x}" cy="{y}" r="20" fill="#FFF6D8" stroke="{INK}" stroke-width="5"/>'
    s += '</g>'
    return s
def tv():
    s = f'<rect x="40" y="1560" width="1000" height="330" rx="28" fill="#0D0D12" stroke="{INK}" stroke-width="12"/>'
    s += '<rect x="70" y="1590" width="940" height="270" rx="14" fill="#10204A"/>'
    s += '<rect x="70" y="1590" width="940" height="270" rx="14" fill="#2E7D32" opacity=".55"/>'
    s += '<path d="M540,1590 L540,1860 M70,1725 L1010,1725" stroke="#fff" stroke-width="5" opacity=".35"/><circle cx="540" cy="1725" r="60" fill="none" stroke="#fff" stroke-width="5" opacity=".35"/>'
    # placar
    s += f'<rect x="150" y="1630" width="780" height="120" rx="18" fill="#141016" stroke="#fff" stroke-width="4"/>'
    s += '<rect x="150" y="1630" width="140" height="120" rx="18" fill="#D0102C"/>'
    s += '<text x="220" y="1712" text-anchor="middle" font-family="Poppins" font-weight="700" font-size="58" fill="#fff">89\'</text>'
    s += '<text x="610" y="1716" text-anchor="middle" font-family="Poppins" font-weight="700" font-size="78" fill="#fff">MENGÃO 2 x 1</text>'
    s += '<text x="540" y="1830" text-anchor="middle" font-family="Poppins" font-weight="700" font-size="30" fill="#fff" opacity=".7">AO VIVO · PLACAR FICTÍCIO</text>'
    return s
def manchete():
    s = f'<g transform="rotate(-2 540 200)"><rect x="70" y="90" width="430" height="74" rx="10" fill="#F5C542" stroke="{INK}" stroke-width="8"/>'
    s += '<text x="285" y="142" text-anchor="middle" font-family="Poppins" font-weight="700" font-size="40" fill="#1A1214">PLANTÃO DA SALA</text></g>'
    s += f'<g transform="rotate(1.5 540 280)"><rect x="60" y="180" width="960" height="190" rx="18" fill="#D0102C" stroke="{INK}" stroke-width="10"/>'
    s += '<text x="540" y="262" text-anchor="middle" font-family="Poppins" font-weight="700" font-size="74" fill="#fff">VIROU NO FIM!</text>'
    s += '<text x="540" y="340" text-anchor="middle" font-family="Poppins" font-weight="700" font-size="62" fill="#F5C542">E O PRIMO SUMIU</text></g>'
    return s
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{defs()}{fundo()}'
svg += f'<g transform="translate(780,800) scale(1.0)">{primo()}</g>'
svg += f'<g transform="translate(360,850) scale(0.98)">{juninho()}</g>'
svg += sofa() + tv() + manchete() + '</svg>'
open("cena.svg", "w").write(svg)
cairosvg.svg2png(bytestring=svg.encode(), write_to="cena.png")
print("ok")
