"""Teste das fontes do plano B — Cartola FC (notas) e ESPN (substituições).

Roda no GitHub Actions. Requisições simples, identificadas, com pausa.
Nada de contornar bloqueio: se uma fonte recusar, o veredito diz isso.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) mengao-da-sala-teste/0.1"
CARTOLA = ["https://api.cartola.globo.com", "https://api.cartolafc.globo.com"]
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"
FLA_CARTOLA = 262
POSICOES = {1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC"}


def pegar(url: str):
    time.sleep(2)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except Exception as exc:
        print(f"[erro] {url}: {exc}")
        return 0, None


def teste_cartola(rel: dict) -> None:
    for base in CARTOLA:
        cod, status = pegar(f"{base}/mercado/status")
        rel[f"cartola_status {base}"] = cod
        if not status:
            continue
        rodada = status.get("rodada_atual")
        for r in (rodada, (rodada or 1) - 1):
            cod, pont = pegar(f"{base}/atletas/pontuados/{r}")
            rel[f"cartola_pontuados r{r}"] = cod
            atletas = (pont or {}).get("atletas") or {}
            nossos = [a for a in atletas.values() if a.get("clube_id") == FLA_CARTOLA]
            if nossos:
                nossos.sort(key=lambda a: a.get("pontuacao", 0), reverse=True)
                rel["cartola_rodada"] = r
                rel["cartola_notas"] = [
                    {"nome": a.get("apelido"), "pos": POSICOES.get(a.get("posicao_id"), "?"),
                     "pontos": a.get("pontuacao"), "scout": a.get("scout")} for a in nossos]
                return
        return


def teste_espn(rel: dict, liga: str) -> None:
    cod, times = pegar(f"{ESPN}/{liga}/teams")
    rel[f"espn_{liga}_times"] = cod
    lista = [t["team"] for t in ((times or {}).get("sports", [{}])[0]
                                 .get("leagues", [{}])[0].get("teams", []))]
    fla = next((t for t in lista if "flamengo" in t.get("displayName", "").lower()), None)
    if not fla:
        return
    cod, agenda = pegar(f"{ESPN}/{liga}/teams/{fla['id']}/schedule")
    rel[f"espn_{liga}_agenda"] = cod
    jogos = [e for e in (agenda or {}).get("events", [])
             if e.get("competitions", [{}])[0].get("status", {}).get("type", {}).get("completed")]
    if not jogos:
        return
    ult = jogos[-1]
    cod, resumo = pegar(f"{ESPN}/{liga}/summary?event={ult['id']}")
    rel[f"espn_{liga}_resumo"] = cod
    eventos = (resumo or {}).get("keyEvents", [])
    subs = []
    for ev in eventos:
        tipo = (ev.get("type") or {}).get("text", "")
        if "substitution" in tipo.lower() and fla["id"] == (ev.get("team") or {}).get("id"):
            subs.append({"minuto": (ev.get("clock") or {}).get("displayValue"),
                         "texto": ev.get("text") or ev.get("shortText")})
    rel[f"espn_{liga}_jogo"] = ult.get("name")
    rel[f"espn_{liga}_substituicoes"] = subs
    rel[f"espn_{liga}_campos_resumo"] = sorted((resumo or {}).keys())


def main() -> int:
    rel: dict = {}
    teste_cartola(rel)
    for liga in ("bra.1", "conmebol.libertadores"):
        teste_espn(rel, liga)

    Path("data").mkdir(exist_ok=True)
    Path("data/fontes_teste.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    print("=" * 60)
    cart = "FUNCIONOU" if rel.get("cartola_notas") else "FALHOU"
    print(f"CARTOLA: {cart}")
    for a in (rel.get("cartola_notas") or [])[:3]:
        print(f"   top: {a['nome']} ({a['pos']}) {a['pontos']}")
    for a in (rel.get("cartola_notas") or [])[-2:]:
        print(f"   fim: {a['nome']} ({a['pos']}) {a['pontos']}")
    for liga in ("bra.1", "conmebol.libertadores"):
        ok = f"espn_{liga}_resumo" in rel and rel[f"espn_{liga}_resumo"] == 200
        print(f"ESPN {liga}: {'FUNCIONOU' if ok else 'FALHOU'} | jogo: {rel.get(f'espn_{liga}_jogo')}")
        for s in rel.get(f"espn_{liga}_substituicoes", []):
            print(f"   {s['minuto']} {s['texto']}")
    print("HTTP:", {k: v for k, v in rel.items() if isinstance(v, int)})
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
