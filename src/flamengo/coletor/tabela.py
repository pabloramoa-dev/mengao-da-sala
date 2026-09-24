"""Tabela do Brasileirão pela ESPN (sem chave) — completa o data/analise.json.

Grava em analise["tabela"]: posicao, pontos, jogos, rival_nome, rival_pontos,
diferenca e jogos_restantes. É o que decide o "Segue o líder!".
Se a ESPN falhar, não inventa nada: a tabela fica ausente e o roteiro usa
"Vitória do Mengão!" em vez de "Segue o líder!".

    python src/flamengo/coletor/tabela.py data/analise.json
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

URL = "https://site.api.espn.com/apis/v2/sports/soccer/bra.1/standings"
UA = "Mozilla/5.0 (X11; Linux x86_64) mengao-da-sala/0.2"


def _stat(entry: dict, *nomes: str):
    for s in entry.get("stats", []):
        if s.get("name") in nomes or s.get("abbreviation") in nomes:
            return s.get("value")
    return None


def tabela() -> dict | None:
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            dados = json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        print(f"[tabela] ESPN falhou: {exc}")
        return None

    entradas = []
    grupos = dados.get("children") or [dados]
    for g in grupos:
        entradas += (g.get("standings") or {}).get("entries", [])
    if not entradas:
        print("[tabela] sem entradas na resposta")
        return None

    linhas = []
    for e in entradas:
        linhas.append({"time": (e.get("team") or {}).get("displayName", ""),
                       "pontos": int(_stat(e, "points", "PTS") or 0),
                       "jogos": int(_stat(e, "gamesPlayed", "GP") or 0),
                       "rank": _stat(e, "rank", "R")})
    linhas.sort(key=lambda l: (l["rank"] if l["rank"] else 99, -l["pontos"]))
    for i, l in enumerate(linhas, 1):
        l["posicao"] = int(l["rank"]) if l["rank"] else i

    nossa = next((l for l in linhas if "flamengo" in l["time"].lower()), None)
    if not nossa:
        print("[tabela] Flamengo não encontrado")
        return None
    rival = linhas[1] if nossa["posicao"] == 1 else linhas[0]
    return {"posicao": nossa["posicao"], "pontos": nossa["pontos"], "jogos": nossa["jogos"],
            "rival_nome": rival["time"], "rival_pontos": rival["pontos"],
            "diferenca": nossa["pontos"] - rival["pontos"],
            "jogos_restantes": max(0, 38 - nossa["jogos"])}


def main() -> int:
    caminho = Path(sys.argv[1] if len(sys.argv) > 1 else "data/analise.json")
    analise = json.loads(caminho.read_text(encoding="utf-8"))
    t = tabela()
    analise["tabela"] = t
    caminho.write_text(json.dumps(analise, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[tabela] {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
