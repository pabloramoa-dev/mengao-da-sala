"""Barras SVG do bloco HyperFrames data-chart, adaptadas ao quadro vertical."""
from html import escape


def barras(ident, dados, maximo):
    """Usa o mesmo eixo em todas as páginas e exibe os valores exatos."""
    largura, altura, base = 900, 125, 153
    passo = largura / len(dados)
    elementos, animacoes = [], []
    for i, (rotulo, valor, destaque) in enumerate(dados):
        x = (i + .5) * passo
        h = max(0, valor) / max(1, maximo) * altura
        barra = f'{ident}-b{i}'
        cor = '#e5364f' if destaque else '#eebc69'
        elementos.append(f'<rect id="{barra}" x="{x-passo*.28:.1f}" y="{base}" width="{passo*.56:.1f}" height="0" fill="{cor}"/>'
                         f'<text x="{x:.1f}" y="{base-h-6:.1f}">{valor}</text>'
                         f'<text x="{x:.1f}" y="184">{escape(str(rotulo))}</text>')
        animacoes.append((barra, base-h, h))
    svg = '<svg viewBox="0 0 900 190" width="100%" fill="white" font-size="25" text-anchor="middle">' + ''.join(elementos) + '</svg>'
    return svg, animacoes


def animar(barras_svg, inicio):
    return ''.join(f'tl.to("#{ident}",{{attr:{{height:{altura:.2f},y:{y:.2f}}},duration:.8,ease:"power2.out"}},{inicio+i*.08:.3f});'
                   for i, (ident,y,altura) in enumerate(barras_svg))


def gols(placar):
    nos, eles = placar
    return barras('gols', [('FLA', nos, True), ('ADV', eles, False)], max(nos, eles))
