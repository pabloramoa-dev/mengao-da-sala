"""Fixture explicitamente fictícia e conferência dos artefatos de CI (sem publicar)."""
import argparse
import os
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analise", type=Path)
    ap.add_argument("--conferir", nargs="*", type=Path)
    a = ap.parse_args()
    if a.analise:
        a.analise.parent.mkdir(parents=True, exist_ok=True)
        a.analise.write_text(json.dumps({
            "_nota": "DADOS FICTÍCIOS para validar o render; não publicar",
            "jogo": {"id": "fixture-hyperframes", "data": "2026-01-01", "status": "FINISHED",
                     "resultado": "vitoria", "gols_nossos": 2, "gols_deles": 1,
                     "em_casa": True, "adversario": "Visitante Exemplo", "estadio": "Estádio Exemplo",
                     "substituicoes": [{"saiu": "Jogador Exemplo", "entrou": "Reserva Exemplo", "minuto": "65'"}]},
            "cartola": {"jogadores": [{"nome": "Jogador Exemplo", "pontos": 7.4}]},
            "tabela": {"posicao": 1},
        }, ensure_ascii=False, indent=2))
    for caminho in a.conferir or []:
        m = json.loads(caminho.read_text())
        assert m["motor"] == "hyperframes", caminho
        esperado = "hyperframes-v3" if os.environ.get("FLAMENGO_MOTOR", "v3") == "v3" else "hyperframes-v1"
        assert m["versao_visual"] == esperado, (caminho, m["versao_visual"])
        if esperado == "hyperframes-v3":
            assert m.get("camada_personagens") == "rig-svg-v3", caminho
        assert m["resolucao"] == [1080, 1920] and m["fps"] == 30, caminho
        assert caminho.with_suffix(".mp4").stat().st_size > 1000, caminho
        assert caminho.with_suffix(".txt").stat().st_size > 0, caminho
        print(f"ok: {caminho} · HyperFrames Full HD · {m['duracao_segundos']:.1f}s")


if __name__ == "__main__":
    main()
