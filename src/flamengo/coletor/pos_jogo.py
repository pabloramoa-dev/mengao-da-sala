"""Coletor pós-jogo do Mengão da Sala.

Junta, para o ÚLTIMO jogo encerrado do Flamengo (Brasileirão ou Libertadores):
  1. ESPN      -> placar, data, substituições com minuto
  2. Cartola   -> pontuação de cada jogador (só Brasileirão)
  3. Notícias  -> manchetes e trechos do ge e do Google Notícias (RSS)
  4. Groq      -> leitura de tudo isso: melhor/pior, polêmica, mexida do técnico,
                  tema quente — SEMPRE em palavras próprias, nunca copiando matéria

Saída: data/analise.json (entra no roteirista) + resumo no log.
Precisa do secret GROQ_API_KEY. Sem ele, gera tudo menos a leitura da Groq.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) mengao-da-sala/0.2"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"
LIGAS = {"bra.1": "Brasileirão", "conmebol.libertadores": "Libertadores", "bra.copa_do_brazil": "Copa do Brasil"}
CARTOLA = "https://api.cartola.globo.com"
FLA_CARTOLA = 262
POSICOES = {1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC"}
RSS = [
    "https://ge.globo.com/rss/ge/futebol/times/flamengo/",
    "https://news.google.com/rss/search?q=Flamengo+when:2d&hl=pt-BR&gl=BR&ceid=BR:pt-419",
]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELOS = "https://api.groq.com/openai/v1/models"
# ordem de preferência; o coletor usa o primeiro que a chave enxergar
PREFERIDOS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "moonshotai/kimi-k2-instruct",
              "qwen/qwen3-32b", "openai/gpt-oss-20b", "llama-3.1-8b-instant"]


def pegar(url: str, json_ok: bool = True, dados: bytes | None = None, cab: dict | None = None):
    time.sleep(1.5)
    h = {"User-Agent": UA, "Accept": "application/json" if json_ok else "*/*"}
    h.update(cab or {})
    req = urllib.request.Request(url, data=dados, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            corpo = r.read().decode("utf-8", "ignore")
            return r.status, (json.loads(corpo) if json_ok else corpo)
    except urllib.error.HTTPError as exc:
        print(f"[http {exc.code}] {url[:90]} {exc.read().decode('utf-8', 'ignore')[:200]}")
        return exc.code, None
    except Exception as exc:
        print(f"[erro] {url[:90]}: {exc}")
        return 0, None


# ------------------------------------------------------------------- ESPN
def ultimo_jogo() -> dict | None:
    """Último jogo ENCERRADO entre todas as competições, ordenado por DATA."""
    candidatos = []
    for liga, nome_liga in LIGAS.items():
        _, times = pegar(f"{ESPN}/{liga}/teams")
        lista = [t["team"] for t in ((times or {}).get("sports", [{}])[0]
                                     .get("leagues", [{}])[0].get("teams", []))]
        fla = next((t for t in lista if "flamengo" in t.get("displayName", "").lower()), None)
        if not fla:
            continue
        _, agenda = pegar(f"{ESPN}/{liga}/teams/{fla['id']}/schedule")
        for e in (agenda or {}).get("events", []):
            comp = (e.get("competitions") or [{}])[0]
            if comp.get("status", {}).get("type", {}).get("completed"):
                candidatos.append({"liga": liga, "competicao": nome_liga, "fla_id": fla["id"],
                                   "id": e["id"], "data": e.get("date", ""), "nome": e.get("name")})
    if not candidatos:
        return None
    return max(candidatos, key=lambda c: c["data"])


def detalhes(jogo: dict) -> dict:
    _, resumo = pegar(f"{ESPN}/{jogo['liga']}/summary?event={jogo['id']}")
    resumo = resumo or {}
    comp = ((resumo.get("header") or {}).get("competitions") or [{}])[0]
    placar = {}
    for c in comp.get("competitors", []):
        lado = "nos" if c.get("id") == jogo["fla_id"] else "eles"
        placar[lado] = {"time": (c.get("team") or {}).get("displayName"),
                        "gols": int(c["score"]) if str(c.get("score", "")).isdigit() else None,
                        "casa": c.get("homeAway") == "home"}
    subs, gols, cartoes = [], [], []
    for ev in resumo.get("keyEvents", []):
        tipo = ((ev.get("type") or {}).get("text") or "").lower()
        nosso = (ev.get("team") or {}).get("id") == jogo["fla_id"]
        minuto = (ev.get("clock") or {}).get("displayValue")
        texto = ev.get("text") or ev.get("shortText") or ""
        if "substitution" in tipo and nosso:
            m = re.search(r"\. (.+?) replaces (.+?)(?: because of an injury)?\.", texto)
            subs.append({"minuto": minuto, "entrou": m.group(1) if m else None,
                         "saiu": m.group(2) if m else None,
                         "lesao": "injury" in texto.lower()})
        elif "goal" in tipo:
            gols.append({"minuto": minuto, "nosso": nosso, "texto": texto})
        elif "card" in tipo and nosso:
            cartoes.append({"minuto": minuto, "texto": texto})
    nos, eles = placar.get("nos", {}), placar.get("eles", {})
    g1, g2 = nos.get("gols"), eles.get("gols")
    resultado = None if g1 is None or g2 is None else (
        "vitoria" if g1 > g2 else "derrota" if g1 < g2 else "empate")
    return {**jogo, "adversario": eles.get("time"), "em_casa": nos.get("casa"),
            "gols_nossos": g1, "gols_deles": g2, "resultado": resultado,
            "estadio": ((resumo.get("gameInfo") or {}).get("venue") or {}).get("fullName"),
            "status": "FINISHED" if (comp.get("status") or {}).get("type", {}).get("completed") else "UNKNOWN",
            "substituicoes": subs, "gols": gols, "cartoes": cartoes}


# ---------------------------------------------------------------- Cartola
def notas_cartola(data_jogo: str) -> dict | None:
    """Pontuação dos jogadores na rodada do jogo (tenta a rodada atual e a anterior)."""
    _, status = pegar(f"{CARTOLA}/mercado/status")
    if not status:
        return None
    atual = status.get("rodada_atual") or 1
    for r in (atual, atual - 1):
        _, pont = pegar(f"{CARTOLA}/atletas/pontuados/{r}")
        atletas = (pont or {}).get("atletas") or {}
        nossos = [a for a in atletas.values()
                  if a.get("clube_id") == FLA_CARTOLA and a.get("entrou_em_campo", True)
                  and a.get("posicao_id") != 6]
        if nossos:
            nossos.sort(key=lambda a: a.get("pontuacao", 0), reverse=True)
            return {"rodada": r, "jogadores": [
                {"nome": a.get("apelido"), "pos": POSICOES.get(a.get("posicao_id"), "?"),
                 "pontos": round(a.get("pontuacao") or 0, 1)} for a in nossos]}
    return None


# --------------------------------------------------------------- Notícias
def limpar(txt: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(txt or ""))).strip()


def noticias(limite: int = 25) -> list[dict]:
    itens = []
    for url in RSS:
        cod, xml = pegar(url, json_ok=False)
        if not xml:
            continue
        try:
            raiz = ET.fromstring(xml)
        except ET.ParseError:
            continue
        for it in raiz.iter("item"):
            titulo = limpar(it.findtext("title"))
            if "flamengo" not in titulo.lower() and "mengão" not in titulo.lower() \
                    and "fla" not in titulo.lower():
                continue
            itens.append({"titulo": titulo[:180],
                          "trecho": limpar(it.findtext("description"))[:300],
                          "fonte": urllib.parse.urlparse(url).netloc,
                          "data": it.findtext("pubDate")})
    vistos, unicos = set(), []
    for n in itens:
        chave = n["titulo"][:60].lower()
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(n)
    return unicos[:limite]


# ------------------------------------------------------------------- Groq
SISTEMA = (
    "Você é o analista do canal de torcedor 'Mengão da Sala'. Recebe dados de um jogo do "
    "Flamengo e manchetes/trechos de notícias. Responda SOMENTE com um objeto JSON válido. "
    "Regras: escreva tudo com palavras suas, nunca copie frases das matérias; não invente "
    "fatos nem falas de pessoas reais; se algo não estiver nos dados, use null; nada de "
    "ofensa a jogador, técnico ou torcida rival. Gol, gol contra, cartão e substituição só "
    "podem ser citados se estiverem em jogo.gols, jogo.cartoes ou jogo.substituicoes."
)
FORMATO = {
    "resumo_do_jogo": "2 frases, tom de torcedor",
    "melhor_em_campo": {"nome": "", "por_que": "1 frase"},
    "pior_em_campo": {"nome": "", "por_que": "1 frase"},
    "mexida_do_tecnico": {"minuto": "", "saiu": "", "entrou": "",
                          "pergunta": "pergunta provocativa para a torcida"},
    "polemica_do_dia": "1 frase ou null",
    "o_que_a_imprensa_diz": "1 a 2 frases, parafraseado",
    "temas_para_video": ["até 4 ideias curtas de vídeo"],
}


def escolher_modelo(chave: str) -> str | None:
    cod, lista = pegar(GROQ_MODELOS, cab={"Authorization": f"Bearer {chave}"})
    ids = [m.get("id", "") for m in (lista or {}).get("data", []) if m.get("active", True)]
    print(f"[groq] modelos visíveis: {len(ids)} (http {cod})")
    for pref in PREFERIDOS:
        if pref in ids:
            return pref
    texto = [i for i in ids if not any(x in i for x in ("whisper", "tts", "guard", "playai"))]
    return texto[0] if texto else None


def analisar(pacote: dict) -> dict | None:
    chave = os.environ.get("GROQ_API_KEY")
    if not chave:
        print("[groq] sem GROQ_API_KEY — pulando análise")
        return None
    modelo = escolher_modelo(chave)
    if not modelo:
        print("[groq] nenhum modelo de texto disponível para esta chave")
        return None
    print(f"[groq] usando {modelo}")
    corpo = {
        "model": modelo, "temperature": 0.4, "max_tokens": 3000,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SISTEMA},
            {"role": "user", "content": "Formato esperado:\n" + json.dumps(FORMATO, ensure_ascii=False)
             + "\n\nDados:\n" + json.dumps(pacote, ensure_ascii=False)[:14000]},
        ],
    }
    if modelo.startswith("openai/gpt-oss"):
        corpo["reasoning_effort"] = "low"  # sobra token para a resposta, que vinha cortada
    cod, resp = pegar(GROQ_URL, dados=json.dumps(corpo).encode("utf-8"),
                      cab={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"})
    if not resp:
        print(f"[groq] falhou (http {cod})")
        return None
    try:
        return json.loads(resp["choices"][0]["message"]["content"])
    except (KeyError, json.JSONDecodeError) as exc:
        print(f"[groq] resposta inesperada: {exc}")
        return None


# ---------------------------------------------------------------- checagem
PALAVRAS_DE_FATO = ("gol contra", "contra o próprio", "expuls", "cartão vermelho", "pênalti",
                    "penalti", "lesão", "lesionad")


def _nomes_validos(jogo: dict, cartola: dict | None) -> set[str]:
    nomes = set()
    for j in (cartola or {}).get("jogadores", []):
        nomes.add((j.get("nome") or "").lower())
    for s_ in jogo.get("substituicoes", []):
        for k in ("saiu", "entrou"):
            if s_.get(k):
                nomes.add(s_[k].lower())
                nomes.add(s_[k].split()[-1].lower())
    return {n for n in nomes if n}


def _fatos_do_jogo(jogo: dict) -> str:
    return " ".join([g.get("texto", "") for g in jogo.get("gols", [])]
                    + [c.get("texto", "") for c in jogo.get("cartoes", [])]).lower()


def checar(analise: dict | None, jogo: dict, cartola: dict | None) -> tuple[dict, list[str]]:
    """Só passa o que os DADOS confirmam. Devolve (analise_validada, descartes)."""
    if not analise:
        return {}, []
    ok, fora = {}, []
    nomes = _nomes_validos(jogo, cartola)
    fatos = _fatos_do_jogo(jogo)

    def nome_ok(n):
        n = (n or "").lower()
        return bool(n) and any(n in v or v in n for v in nomes)

    def texto_ok(t):
        t = (t or "").lower()
        suspeitos = [p for p in PALAVRAS_DE_FATO if p in t]
        # palavra de fato só passa se o próprio registro da ESPN tiver o mesmo tipo de evento
        return all(("own goal" in fatos) if "contra" in p else
                   ("red" in fatos) if ("expuls" in p or "vermelho" in p) else
                   ("penalty" in fatos) if "nalti" in p else True for p in suspeitos)

    for chave in ("melhor_em_campo", "pior_em_campo"):
        item = analise.get(chave) or {}
        if nome_ok(item.get("nome")) and texto_ok(item.get("por_que")):
            ok[chave] = item
        elif item:
            fora.append(f"{chave}: {item}")

    mex = analise.get("mexida_do_tecnico") or {}
    bate = any((s_.get("saiu") or "").lower().endswith((mex.get("saiu") or "#").lower().split()[-1])
               for s_ in jogo.get("substituicoes", [])) if mex.get("saiu") else False
    if bate:
        ok["mexida_do_tecnico"] = mex
    elif mex:
        fora.append(f"mexida_do_tecnico: {mex}")

    for chave in ("resumo_do_jogo", "polemica_do_dia", "o_que_a_imprensa_diz"):
        t = analise.get(chave)
        if t and texto_ok(t):
            ok[chave] = t
        elif t:
            fora.append(f"{chave}: {t}")
    if analise.get("temas_para_video"):
        ok["temas_para_video"] = analise["temas_para_video"]
    return ok, fora


# ------------------------------------------------------------------- main
def main() -> int:
    saida = {"gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    jogo = ultimo_jogo()
    if not jogo:
        print("sem jogo encerrado encontrado")
        return 2
    jogo = detalhes(jogo)
    saida["jogo"] = jogo
    if jogo["liga"] == "bra.1":
        saida["cartola"] = None  # reativar somente com vínculo verificável partida/rodada
    saida["noticias"] = noticias()
    bruta = analisar({"jogo": jogo, "notas_cartola": saida.get("cartola"),
                      "noticias": saida["noticias"]})
    saida["analise"], saida["descartados"] = checar(bruta, jogo, saida.get("cartola"))

    Path("data").mkdir(exist_ok=True)
    Path("data/analise.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2),
                                         encoding="utf-8")

    print("=" * 64)
    print(f"JOGO: Flamengo {jogo['gols_nossos']} x {jogo['gols_deles']} {jogo['adversario']} "
          f"({jogo['competicao']}, {jogo['data'][:10]}) -> {jogo['resultado']}")
    for s in jogo["substituicoes"]:
        print(f"  {s['minuto']} saiu {s['saiu']} / entrou {s['entrou']}")
    c = saida.get("cartola")
    if c:
        j = c["jogadores"]
        print(f"CARTOLA r{c['rodada']}: melhor {j[0]['nome']} {j[0]['pontos']} | "
              f"pior {j[-1]['nome']} {j[-1]['pontos']}")
    print(f"NOTÍCIAS: {len(saida['noticias'])} manchetes")
    a = saida["analise"]
    if a:
        print("GROQ:")
        print(json.dumps(a, ensure_ascii=False, indent=2))
    else:
        print("GROQ: sem análise")
    for d in saida["descartados"]:
        print(f"[checagem] DESCARTADO (dado não confirma): {d}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
