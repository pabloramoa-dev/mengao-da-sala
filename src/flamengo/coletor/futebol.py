"""Coletor de dados do Flamengo no football-data.org (plano gratuito).

Plano gratuito cobre o Brasileirao Serie A (codigo BSA), 10 chamadas/minuto,
placares com atraso. Nao cobre Libertadores nem Copa do Brasil - para essas,
o canal usa a via de noticia (coletor/noticias.py), nunca dado automatico.

Regra do canal: so vira video o que esta CONFIRMADO. Partida so entra em
roteiro de pos-jogo com status FINISHED. Nada de placar ao vivo.

Uso:
    export FOOTBALL_DATA_TOKEN=xxxx
    python -m flamengo.coletor.futebol --out data/snapshot.json
    python -m flamengo.coletor.futebol --offline tests/fixture_bsa.json
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://api.football-data.org/v4"
COMPETICAO = "BSA"
TIME = "Flamengo"          # casado por substring, sem id fixo
PAUSA = 6.5                # 10 req/min no plano gratuito


class SemToken(RuntimeError):
    pass


def _get(caminho: str, token: str) -> dict:
    req = urllib.request.Request(f"{BASE}{caminho}", headers={"X-Auth-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        corpo = exc.read().decode("utf-8", "ignore")[:300]
        raise RuntimeError(f"football-data {exc.code} em {caminho}: {corpo}") from exc


def _nosso(time_dict: dict) -> bool:
    nome = (time_dict or {}).get("name", "")
    return TIME.lower() in nome.lower()


def _partida(p: dict) -> dict:
    casa, fora = p["homeTeam"], p["awayTeam"]
    placar = p.get("score", {}).get("fullTime", {})
    gols_casa, gols_fora = placar.get("home"), placar.get("away")
    mandante = _nosso(casa)
    nos = gols_casa if mandante else gols_fora
    eles = gols_fora if mandante else gols_casa
    if nos is None or eles is None:
        resultado = None
    else:
        resultado = "vitoria" if nos > eles else "derrota" if nos < eles else "empate"
    return {
        "id": p["id"],
        "status": p["status"],
        "utc": p["utcDate"],
        "rodada": p.get("matchday"),
        "competicao": p.get("competition", {}).get("name", "Brasileirao"),
        "mandante": mandante,
        "casa": casa.get("shortName") or casa.get("name"),
        "fora": fora.get("shortName") or fora.get("name"),
        "adversario": (fora if mandante else casa).get("shortName")
        or (fora if mandante else casa).get("name"),
        "gols_casa": gols_casa,
        "gols_fora": gols_fora,
        "gols_nossos": nos,
        "gols_deles": eles,
        "resultado": resultado,
    }


def coletar(token: str | None = None) -> dict:
    token = token or os.environ.get("FOOTBALL_DATA_TOKEN")
    if not token:
        raise SemToken("Defina FOOTBALL_DATA_TOKEN (chave gratuita do football-data.org)")

    tabela = _get(f"/competitions/{COMPETICAO}/standings", token)
    time.sleep(PAUSA)
    jogos = _get(f"/competitions/{COMPETICAO}/matches", token)
    return montar(tabela, jogos)


def montar(tabela: dict, jogos: dict) -> dict:
    """Separado do HTTP para poder testar offline com fixture."""
    geral = next(t for t in tabela["standings"] if t.get("type") == "TOTAL")
    linhas = geral["table"]
    nossa = next(l for l in linhas if _nosso(l["team"]))
    lider = linhas[0]
    perseguidor = linhas[1] if nossa["position"] == 1 else lider

    todas = [_partida(p) for p in jogos["matches"] if _nosso(p["homeTeam"]) or _nosso(p["awayTeam"])]
    encerradas = [p for p in todas if p["status"] == "FINISHED"]
    futuras = [p for p in todas if p["status"] in {"SCHEDULED", "TIMED"}]
    futuras.sort(key=lambda p: p["utc"])

    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "competicao": tabela["competition"]["name"],
        "rodada_atual": jogos.get("matches", [{}])[0].get("season", {}).get("currentMatchday"),
        "tabela": {
            "posicao": nossa["position"],
            "pontos": nossa["points"],
            "jogos": nossa["playedGames"],
            "vitorias": nossa["won"],
            "empates": nossa["draw"],
            "derrotas": nossa["lost"],
            "saldo": nossa["goalDifference"],
            "rival_nome": perseguidor["team"].get("shortName") or perseguidor["team"]["name"],
            "rival_pontos": perseguidor["points"],
            "diferenca": nossa["points"] - perseguidor["points"],
            "jogos_restantes": 38 - nossa["playedGames"],
        },
        "ultimo_jogo": encerradas[-1] if encerradas else None,
        "proximo_jogo": futuras[0] if futuras else None,
        "sequencia": [p["resultado"] for p in encerradas[-5:]],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/snapshot.json")
    ap.add_argument("--offline", help="fixture JSON {tabela:..., jogos:...} para teste sem rede")
    args = ap.parse_args()

    if args.offline:
        bruto = json.loads(Path(args.offline).read_text(encoding="utf-8"))
        dados = montar(bruto["tabela"], bruto["jogos"])
    else:
        dados = coletar()

    destino = Path(args.out)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(dados, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
