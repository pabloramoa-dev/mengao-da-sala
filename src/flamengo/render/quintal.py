"""Quintal diurno da Dona Cida: céu aberto, plantas, flores e quadro de madeira."""
INK='#304936'


def vaso(x,y,k=1,cor='#c97146',flor=False):
    s=f'<g transform="translate({x},{y}) scale({k})">'
    s+='<ellipse cx="0" cy="12" rx="87" ry="17" fill="#234c31" opacity=".13"/>'
    s+=f'<path d="M-64,-92 L64,-92 L48,4 Q0,22 -48,4Z" fill="{cor}" stroke="{INK}" stroke-width="5"/>'
    s+='<path d="M-44,-82 L-30,-4" stroke="#fff1c9" stroke-width="9" opacity=".25"/>'
    s+=f'<rect x="-73" y="-111" width="146" height="28" rx="9" fill="{cor}" stroke="{INK}" stroke-width="5"/>'
    for i,(dx,dy) in enumerate([(-55,-225),(-20,-280),(24,-260),(66,-206),(0,-205)]):
        s+=f'<path d="M0,-108 Q{dx},-155 {dx},{dy}" fill="none" stroke="#467947" stroke-width="8"/>'
        for lado,extra in [(-1,0),(1,35)]:
            s+=f'<ellipse cx="{dx+lado*23}" cy="{dy+55+extra}" rx="42" ry="19" transform="rotate({lado*35} {dx+lado*23} {dy+55+extra})" fill="{["#41794a","#66a757","#91be66"][i%3]}" stroke="#365f3c" stroke-width="3"/>'
        if flor:
            for a in range(0,360,72):
                s+=f'<ellipse cx="{dx}" cy="{dy-15}" rx="12" ry="21" transform="rotate({a} {dx} {dy})" fill="{["#f799af","#ffc46d","#ed7493"][i%3]}"/>'
            s+=f'<circle cx="{dx}" cy="{dy}" r="10" fill="#ffe699"/>'
    return s+'</g>'


def fundo():
    s='''<defs>
    <linearGradient id="quintal-ceu" x2="0" y2="1"><stop stop-color="#83d4eb"/><stop offset="1" stop-color="#eaf9e6"/></linearGradient>
    <linearGradient id="quintal-piso" x2="0" y2="1"><stop stop-color="#ead5af"/><stop offset="1" stop-color="#cfae85"/></linearGradient>
    </defs>
    <g id="quintal-dia">
    <rect x="-250" y="-250" width="1580" height="2420" fill="url(#quintal-ceu)"/>
    <circle cx="900" cy="635" r="100" fill="#fff3b5" opacity=".4"/>
    <circle cx="900" cy="635" r="65" fill="#ffe996"/>
    <g fill="#fff" opacity=".85"><ellipse cx="350" cy="570" rx="130" ry="26"/><ellipse cx="390" cy="548" rx="65" ry="38"/>
    <ellipse cx="680" cy="710" rx="99" ry="22"/><ellipse cx="705" cy="693" rx="46" ry="31"/></g>
    <path d="M-100,950 Q150,770 360,900 Q640,765 870,875 Q1050,790 1180,945 V1400 H-100Z" fill="#a4cb83"/>
    <path d="M-140,1080 Q180,927 420,1040 Q735,914 1150,1060 V1460 H-140Z" fill="#6eaa65"/>
    <rect x="-200" y="1120" width="1500" height="850" fill="url(#quintal-piso)"/>
    <path d="M-100,1250 H1180 M-100,1430 H1180 M-100,1660 H1180 M-100,1910 H1180 M160,1120 L-100,1920 M470,1120 L390,1920 M760,1120 L970,1920" stroke="#b99e7b" stroke-width="4" opacity=".5"/>
    <path d="M-150,685 L112,600 L294,686 V1160 H-150Z" fill="#fff2d5" stroke="#ae966f" stroke-width="7"/>
    <path d="M-170,690 L110,578 L318,686" fill="none" stroke="#b76646" stroke-width="29" stroke-linejoin="round"/>
    <rect x="27" y="753" width="164" height="190" rx="9" fill="#78aca4" stroke="#be8d57" stroke-width="13"/>
    <path d="M109,753 V943 M27,848 H191" stroke="#eadcbb" stroke-width="9"/>
    <path d="M-25,1018 H285" stroke="#a87748" stroke-width="16"/>
    <path d="M1000,550 V1230 M824,545 V1160 M810,561 H1180 M810,610 H1180 M866,540 V850 M940,540 V850 M1020,540 V850" stroke="#c19b68" stroke-width="12"/>
    <path d="M1110,300 Q960,430 1020,700 Q870,865 1040,995" fill="none" stroke="#547547" stroke-width="14"/>
    '''
    for x,y,k in [(20,440,1),(155,445,.85),(1010,360,1.2),(1070,500,1),(985,795,.7),(1080,930,.85)]:
        s+=f'<g transform="translate({x},{y}) scale({k})" fill="#629852" stroke="#466e3e" stroke-width="4"><ellipse rx="101" ry="54" transform="rotate(-25)"/><ellipse cx="54" cy="30" rx="79" ry="44" transform="rotate(18)"/><ellipse cx="-40" cy="48" rx="83" ry="43"/></g>'
    s+='<path d="M205,582 V775 M155,588 L205,775 L256,610" stroke="#8b7951" stroke-width="5" fill="none"/>'
    s+=vaso(205,900,.65,'#e9b86f',True)
    s+=vaso(110,1230,1.17,'#bf7853')+vaso(278,1210,.68,'#e6bb7a',True)
    s+=vaso(970,1250,1.25,'#ca7e59',True)+vaso(815,1190,.7,'#83a69b')
    s+='<ellipse cx="540" cy="1342" rx="260" ry="40" fill="#746642" opacity=".15"/>'
    return s+'</g>'


def moldura():
    s='''<g id="quadro-quintal">
    <rect x="127" y="1286" width="826" height="57" rx="14" fill="#bd915b" stroke="#795737" stroke-width="7"/>
    <path d="M147,1308 H930 M175,1344 V1402 M905,1344 V1402" stroke="#88623f" stroke-width="8"/>
    <path d="M208,1240 H267 V1280 Q236,1300 208,1280Z" fill="#fff1d6" stroke="#856340" stroke-width="5"/>
    <path d="M268,1248 Q302,1246 297,1267 Q285,1280 269,1268" fill="none" stroke="#856340" stroke-width="6"/>
    <path d="M142,1650 L100,1805 M938,1650 L980,1805" stroke="#946641" stroke-width="24"/>
    <rect x="56" y="1374" width="968" height="330" rx="20" fill="#b38454" stroke="#754f35" stroke-width="9"/>
    <rect x="83" y="1401" width="914" height="276" rx="9" fill="#295b49" stroke="#e1bc7f" stroke-width="5"/>
    <path d="M95,1387 H978 M95,1690 H978" stroke="#e3bc7f" stroke-width="4"/>
    <rect x="869" y="1653" width="62" height="7" rx="3" fill="#fff4d6" transform="rotate(-5 869 1653)"/>
    </g>'''
    return s+vaso(36,1840,.7,'#d0855c',True)+vaso(1040,1830,.75,'#dca66b',True)
