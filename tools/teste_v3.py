"""Amostras v3 para a CI (sem publicar).

    python -m tools.teste_v3 --plantao saida/plantao_pauta.json

O Plantão de amostra usa tests/fixture_noticias.json (notícias e textos
FICTÍCIOS, marcados como tal) no lugar da Groq, para o render rodar sem chave.
"""
import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from src.flamengo import plantao, quadros
from src.flamengo.diario import legenda_post

FIXTURE = Path(__file__).resolve().parents[1] / "tests/fixture_noticias.json"


def pauta_plantao(destino: Path) -> dict:
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    d["coletado_em"] = datetime.now(timezone.utc).isoformat()
    noticias = destino.with_name("noticias_teste.json")
    noticias.parent.mkdir(parents=True, exist_ok=True)
    noticias.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    pauta = plantao.gerar(date.today(), noticias, gerador=lambda _p: d["textos_ficticios"])
    if pauta is None:
        raise SystemExit("amostra do plantão não passou na checagem")
    pauta = quadros.dirigir(pauta)
    pauta["legenda_post"] = "[AMOSTRA FICTÍCIA — NÃO PUBLICAR]\n" + legenda_post(pauta)
    destino.write_text(json.dumps(pauta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ok: {destino} · {len(pauta['batidas'])} falas")
    return pauta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plantao", type=Path, required=True)
    pauta_plantao(ap.parse_args().plantao)


if __name__ == "__main__":
    main()
