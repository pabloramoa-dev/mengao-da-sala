"""Gil e Dona Cida. Rigs originais com cabeça, olhos, boca e braços articulados.
IDs rubro/primo são somente compatibilidade técnica com o compositor, não o elenco.
"""
from src.flamengo.render.personagens_v3 import (GEO, GESTOS, EXPRESSOES, FORMAS_FALA,
    VISEMA, INK, defs as _defs, _uses, _boca_use, _pivo, _respira, braco, ids, celular)


def defs():
    return _defs().replace('#A9DDFA','#e44357').replace('#6FB6E3','#a40e29')


def gil(expr='neutra', gesto='repouso'):
    q='rubro'
    corpo=f'''<path d="M-170,180 Q-130,130 -65,140 L65,140 Q140,140 170,180 L192,535 L-192,535Z" fill="#b80d29" stroke="{INK}" stroke-width="10"/>
    <path d="M-179,240 H179 M-185,325 H185 M-190,410 H190 M-190,490 H190" stroke="#171923" stroke-width="39"/>
    <path d="M-58,110 H58 V156 Q0,190 -58,156Z" fill="#a86c44" stroke="{INK}" stroke-width="8"/>
    <path d="M-65,146 Q0,205 65,146" fill="none" stroke="#ffcf65" stroke-width="9"/>
    <text x="80" y="210" font-family="DejaVu Sans" font-size="26" font-weight="bold" fill="white">GIL</text>'''
    cab=f'''<ellipse cx="-153" cy="24" rx="30" ry="40" fill="#b97c52" stroke="{INK}" stroke-width="8"/>
    <ellipse cx="153" cy="24" rx="30" ry="40" fill="#b97c52" stroke="{INK}" stroke-width="8"/>
    <path d="M-152,-40 Q-158,-160 0,-174 Q158,-160 152,-40 L143,56 Q122,149 0,153 Q-122,149 -143,56Z" fill="url(#pele_j)" stroke="{INK}" stroke-width="11"/>
    <path d="M-151,-56 Q-170,-175 -87,-186 Q-65,-220 -24,-188 Q47,-218 91,-181 Q165,-161 151,-55 L121,-105 Q20,-130 -111,-100Z" fill="#27232b" stroke="{INK}" stroke-width="10"/>
    <path d="M-143,-75 L-124,-102 M143,-75 L124,-102" stroke="#c2b4ac" stroke-width="13"/>
    <path d="M-137,58 Q-110,151 0,151 Q110,151 137,58 L95,70 Q65,138 0,135 Q-65,138 -95,70Z" fill="#3b2926"/>
    {_uses(q,expr)}
    <path d="M-7,30 Q-28,54 -5,62 L21,56" fill="none" stroke="{INK}" stroke-width="7"/>
    {_boca_use(q,expr)}'''
    return f'<g id="{q}-rig">{_respira(q,corpo+_pivo(q,cab))}{braco(q,-1,gesto)}{braco(q,1,gesto)}</g>'


def cida(expr='neutra', gesto='repouso'):
    q='primo'
    corpo=f'''<path d="M-140,235 Q-145,179 -70,176 H70 Q145,179 140,235 L165,560 H-165Z" fill="#bd1535" stroke="{INK}" stroke-width="10"/>
    <path d="M-146,300 H146 M-153,390 H153 M-160,480 H160" stroke="#1a1923" stroke-width="35"/>
    <path d="M-38,119 H38 V190 Q0,212 -38,190Z" fill="#e2ae85" stroke="{INK}" stroke-width="7"/>
    <path d="M-62,177 Q0,270 62,177" fill="none" stroke="#ffd575" stroke-width="8"/>
    <circle cx="0" cy="238" r="12" fill="#ffd575"/>
    <text x="-60" y="285" fill="white" font-family="DejaVu Sans" font-size="23" font-weight="bold">DONA CIDA</text>'''
    cab=f'''<ellipse cx="0" cy="-195" rx="84" ry="68" fill="#b9b5bb" stroke="{INK}" stroke-width="10"/>
    <ellipse cx="0" cy="-27" rx="151" ry="186" fill="#b9b5bb" stroke="{INK}" stroke-width="10"/>
    <path d="M-120,-61 Q-126,-171 0,-179 Q126,-171 120,-61 L112,61 Q84,145 0,147 Q-84,145 -112,61Z" fill="url(#pele_p)" stroke="{INK}" stroke-width="9"/>
    <path d="M-127,-48 Q-145,-167 -48,-183 Q30,-211 126,-140 L127,-45 Q85,-130 30,-136 Q-48,-92 -127,-48Z" fill="#d2cdd2" stroke="{INK}" stroke-width="9"/>
    <path d="M-94,-149 Q0,-207 89,-150" fill="none" stroke="#bd1535" stroke-width="20"/>
    {_uses(q,expr)}
    <g fill="none" stroke="#a30b30" stroke-width="8"><rect x="-89" y="-57" width="82" height="79" rx="23"/><rect x="7" y="-57" width="82" height="79" rx="23"/><path d="M-7,-22 Q0,-30 7,-22"/></g>
    <path d="M4,23 Q23,53 2,60" fill="none" stroke="{INK}" stroke-width="6"/>
    <path d="M-93,50 l16,8 M93,50 l-16,8" stroke="#be8867" stroke-width="4"/>
    <ellipse cx="-119" cy="62" rx="10" ry="19" fill="none" stroke="#ffd575" stroke-width="7"/>
    <ellipse cx="119" cy="62" rx="10" ry="19" fill="none" stroke="#ffd575" stroke-width="7"/>
    {_boca_use(q,expr)}'''
    gesto='explicar' if gesto=='celular' else gesto
    arms=(braco(q,-1,gesto)+braco(q,1,gesto)).replace(celular(GEO[q]['braco'][1]+30),'').replace('url(#ceu)','url(#rubro)')
    return f'<g id="{q}-rig">{_respira(q,corpo+_pivo(q,cab))}{arms}</g>'

juninho=gil
primo=cida
