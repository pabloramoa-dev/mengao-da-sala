"""Quadro conceito da sala v3 (SVG estático) para conferir o visual sem renderizar vídeo.

    python -m src.flamengo.render.cena_v3_conceito saida/cena_v3.svg

Usa a mesma cena do motor v3 (hyperframes_v3.svg_cena). Nada roda ao importar.
"""
import sys
from pathlib import Path


def main(destino: str = "cena_v3.svg") -> Path:
    from src.flamengo.render import hyperframes_v3 as V
    from src.flamengo.roteiro import batida
    b = batida("Virou no fim!", tipo="placar", placar="2 x 1")
    b.update(personagem="rubro", humor="euforico", gesto="bracos_cima")
    svg = V.svg_cena({"capa": "VIROU NO FIM!", "batidas": [b]})
    alvo = Path(destino)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(svg, encoding="utf-8")
    print(f"ok: {alvo}")
    return alvo


if __name__ == "__main__":
    main(*sys.argv[1:2])
