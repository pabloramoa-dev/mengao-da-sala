"""Teste do Sofascore para o canal do Flamengo — roda no GitHub Actions.

Pergunta que este teste responde: dá para puxar, de graça e de dentro do
Actions, as NOTAS dos jogadores e as SUBSTITUIÇÕES do último jogo?

Faz requisições simples e identificadas, no ritmo de uma pessoa (pausa de
3 s). NÃO tenta contornar bloqueio (sem imitação de navegador, sem proxy
residencial): se o Sofascore recusar, o resultado é "bloqueado" e o canal
usa o plano B — notas e substituições extraídas das matérias pós-jogo.

Saída: data/sofascore_teste.json + resumo legível no log do workflow.
Código de saída: 0 = funcionou, 2 = bloqueado/incompleto (o workflow NÃO falha
por isso; o resumo diz qual é o veredito).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://api.sofascore.com/api/v1"
UA = "Mozilla/5.0 (X11; Linux x86_64) flamengo-bot-teste/0.1"
PAUSA = 3.0


def pegar(caminho: str) -> tuple[int, dict | None]:
    req = urllib.request.Request(f"{BASE}{caminho}", headers={
        "User-Agent": UA, "Accept": "application/json",
        "Referer": "https://www.sofascore.com/"})
    time.sleep(PAUSA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except Exception as exc:  # rede, timeout, JSON inválido
        print(f"[erro] {caminho}: {exc}")
        return 0, None


# ---------------------------------------------------------------- parsers
def achar_time(busca: dict) -> dict | None:
    for r in busca.get("results", []):
        e = r.get("entity", {})
        if (r.get("type") == "team" and e.get("sport", {}).get("slug") == "football"
                and e.get("country", {}).get("name") == "Brazil"
                and "flamengo" in e.get("name", "").lower()
                and not any(b in e.get("name", "") for b in ("U17", "U20", "U23", "Sub", "Women"))
                and e.get("gender", "M") == "M"):
            return {"id": e["id"], "nome": e["name"]}
    return None


def ultimo_encerrado(eventos: dict, time_id: int) -> dict | None:
    fim = [e for e in eventos.get("events", [])
           if e.get("status", {}).get("type") == "finished"]
    if not fim:
        return None
    e = max(fim, key=lambda x: x.get("startTimestamp", 0))
    em_casa = e["homeTeam"]["id"] == time_id
    return {
        "id": e["id"],
        "data": datetime.fromtimestamp(e["startTimestamp"], timezone.utc).isoformat(),
        "competicao": e.get("tournament", {}).get("name"),
        "em_casa": em_casa,
        "adversario": (e["awayTeam"] if em_casa else e["homeTeam"])["name"],
        "gols_nossos": (e["homeScore"] if em_casa else e["awayScore"]).get("current"),
        "gols_deles": (e["awayScore"] if em_casa else e["homeScore"]).get("current"),
    }


def notas(lineups: dict, em_casa: bool) -> list[dict]:
    lado = lineups.get("home" if em_casa else "away", {})
    saida = []
    for p in lado.get("players", []):
        nota = p.get("statistics", {}).get("rating")
        if nota is not None:
            saida.append({"nome": p["player"].get("shortName") or p["player"]["name"],
                          "nota": round(float(nota), 1),
                          "reserva": bool(p.get("substitute")),
                          "minutos": p.get("statistics", {}).get("minutesPlayed")})
    return sorted(saida, key=lambda x: x["nota"], reverse=True)


def substituicoes(incidentes: dict, em_casa: bool) -> list[dict]:
    subs = []
    for i in incidentes.get("incidents", []):
        if i.get("incidentType") == "substitution" and i.get("isHome") == em_casa:
            subs.append({"minuto": i.get("time"),
                         "saiu": (i.get("playerOut") or {}).get("name"),
                         "entrou": (i.get("playerIn") or {}).get("name")})
    return sorted(subs, key=lambda s: s["minuto"] or 0)


# ------------------------------------------------------------------- teste
def main() -> int:
    etapas, resultado = {}, {"quando": datetime.now(timezone.utc).isoformat()}

    cod, busca = pegar("/search/all?q=Flamengo")
    etapas["busca"] = cod
    time_ = achar_time(busca or {})
    if not time_:
        return fechar(etapas, resultado, "bloqueado" if cod in (0, 403, 429) else "time_nao_achado")
    resultado["time"] = time_

    cod, eventos = pegar(f"/team/{time_['id']}/events/last/0")
    etapas["jogos"] = cod
    jogo = ultimo_encerrado(eventos or {}, time_["id"])
    if not jogo:
        return fechar(etapas, resultado, "sem_jogo")
    resultado["jogo"] = jogo

    cod, lineups = pegar(f"/event/{jogo['id']}/lineups")
    etapas["escalacao"] = cod
    resultado["notas"] = notas(lineups or {}, jogo["em_casa"])

    cod, inc = pegar(f"/event/{jogo['id']}/incidents")
    etapas["lances"] = cod
    resultado["substituicoes"] = substituicoes(inc or {}, jogo["em_casa"])

    ok = bool(resultado["notas"]) and etapas["lances"] == 200
    return fechar(etapas, resultado, "funcionou" if ok else "incompleto")


def fechar(etapas, resultado, veredito) -> int:
    resultado.update(veredito=veredito, http=etapas)
    Path("data").mkdir(exist_ok=True)
    Path("data/sofascore_teste.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 56)
    print(f"VEREDITO: {veredito.upper()}")
    print(f"HTTP por etapa: {etapas}")
    if "jogo" in resultado:
        j = resultado["jogo"]
        print(f"Último jogo: Flamengo {j['gols_nossos']} x {j['gols_deles']} "
              f"{j['adversario']} ({j['competicao']})")
    if resultado.get("notas"):
        n = resultado["notas"]
        print(f"MELHOR em campo: {n[0]['nome']} ({n[0]['nota']})")
        print(f"PIOR em campo:   {n[-1]['nome']} ({n[-1]['nota']})")
    for s in resultado.get("substituicoes", []):
        print(f"  {s['minuto']}' saiu {s['saiu']} -> entrou {s['entrou']}")
    print("=" * 56)
    return 0 if veredito == "funcionou" else 2


if __name__ == "__main__":
    sys.exit(main())
