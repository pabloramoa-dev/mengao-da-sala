"""Plantão da Sala — coletor de notícias do Flamengo das últimas 24 h.

Só biblioteca padrão. Lê RSS e a API pública da ESPN, filtra o que é do
Flamengo, agrupa a MESMA história contada por vários sites e pontua:
quanto mais veículos falam do assunto, mais quente ele é. A saída
(data/noticias_hoje.json) é a matéria-prima do Reel diário.

Regras editoriais (iguais ao editorial.yml):
- o vídeo nunca copia o texto do site: a Groq reescreve a partir do título;
- 'rumor' quando o título traz negocia/interesse/sonda/pode/estaria;
- fonte sempre vai na legenda.
"""
from __future__ import annotations
import json, re, sys, time, unicodedata, urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree as ET

MAX_TITULO = 150          # título maior que isso é post de rede social, não manchete
NAO_SAO_NOMES = {"flamengo", "mengao", "libertadores", "brasileirao", "campeonato", "brasileiro", "copa",
                 "brasil", "saiba", "confira", "veja", "rubro", "negro", "nacao", "maracana"}
UA = "Mozilla/5.0 (compatible; MengaoDaSalaBot/1.0; +https://github.com/pabloramoa-dev/mengao-da-sala)"
RUMOR = ("negocia", "interesse", "sonda", "estaria", "pode ", "avalia", "alvo", "especula", "proposta", "quer ")
TEMAS = {
    "mercado": ("contrat", "negocia", "proposta", "reforço", "reforco", "venda", "renova", "empréstimo", "emprestimo"),
    "dm": ("lesão", "lesao", "cirurgia", "desfalque", "departamento médico", "médico", "medico", "recupera",
           "dm ", "machuc", "volta aos treinos"),
    "jogo": (" x ", "escalação", "escalacao", "vence", "empata", "perde", "gol", "rodada", "classifica"),
    "tecnico": ("técnico", "tecnico", "treinador", "jardim", "comissão"),
    "bastidor": ("diretoria", "presidente", "bap", "boto", "sócio", "socio", "receita", "patrocín", "stf", "bets"),
    "torcida": ("torcida", "público", "publico", "ingresso", "maracanã", "maracana", "nação", "nacao"),
}


def _baixar(url: str, tentativas=2) -> bytes:
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except Exception:
            if i == tentativas - 1:
                raise
            time.sleep(2)


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def _data(txt):
    if not txt:
        return None
    try:
        d = parsedate_to_datetime(txt)
    except Exception:
        try:
            d = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        except Exception:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def ler_rss(raw: bytes, fonte: dict) -> list[dict]:
    raiz = ET.fromstring(raw)
    itens = []
    for it in raiz.iter("item"):
        titulo = (it.findtext("title") or "").strip()
        veiculo = (it.findtext("source") or "").strip()
        if fonte["id"].startswith("gnews") and " - " in titulo:      # "Título - Veículo"
            titulo, _, veiculo = titulo.rpartition(" - ")
        itens.append(dict(titulo=titulo, link=(it.findtext("link") or "").strip(),
                          quando=_data(it.findtext("pubDate")), veiculo=veiculo or fonte["nome"],
                          resumo=re.sub("<[^>]+>", " ", it.findtext("description") or "")[:400]))
    ns = {"a": "http://www.w3.org/2005/Atom"}                         # Atom (Reddit)
    for en in raiz.findall("a:entry", ns):
        link = en.find("a:link", ns)
        itens.append(dict(titulo=(en.findtext("a:title", "", ns)).strip(),
                          link=link.get("href") if link is not None else "",
                          quando=_data(en.findtext("a:updated", "", ns)), veiculo=fonte["nome"], resumo=""))
    return itens


def ler_espn(raw: bytes, fonte: dict) -> list[dict]:
    d = json.loads(raw)
    return [dict(titulo=a.get("headline", ""), link=(a.get("links", {}).get("web", {}) or {}).get("href", ""),
                 quando=_data(a.get("published")), veiculo="ESPN", resumo=a.get("description", ""))
            for a in d.get("articles", [])]


def eh_do_flamengo(it, cfg) -> bool:
    if not it["titulo"] or len(it["titulo"]) > MAX_TITULO:
        return False
    t = " " + _norm(it["titulo"] + " " + it["resumo"]) + " "
    if not any(_norm(p) in t for p in cfg["palavras_obrigatorias"]):
        return False
    return not any(_norm(p) in t for p in cfg["ignorar"])


def _tokens(t):
    return {w for w in _norm(t).split() if len(w) > 3 and w not in {"flamengo", "mengao", "sobre", "apos", "para", "contra", "rubro", "negro"}}


def agrupar(itens: list[dict], limiar=0.45) -> list[dict]:
    grupos = []
    for it in sorted(itens, key=lambda x: x["quando"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True):
        tk = _tokens(it["titulo"])
        for g in grupos:
            inter = len(tk & g["tokens"]) / max(1, min(len(tk), len(g["tokens"])))
            if inter >= limiar:
                g["itens"].append(it); g["tokens"] |= tk
                break
        else:
            grupos.append({"tokens": tk, "itens": [it]})
    return grupos


def _nomes(titulo: str) -> set[str]:
    """Nomes próprios do título (Arrascaeta, Fux, Jardim...) para achar a mesma história."""
    return {_norm(w).strip() for w in re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ]{3,}", titulo)} - NAO_SAO_NOMES


def fundir_mesmo_assunto(pautas: list[dict]) -> list[dict]:
    """Junta pautas do mesmo tema que citam o mesmo nome próprio (ex.: duas do Arrascaeta).
    A de maior nota fica; a outra vira 'relacionada' e soma veículos."""
    finais = []
    for p in sorted(pautas, key=lambda x: x["nota"], reverse=True):
        nomes = _nomes(p["titulo"])
        # tema "geral" é amplo: só funde com dois nomes em comum (um "Santos" sozinho não basta)
        minimo = 2 if p["tema"] == "geral" else 1
        alvo = next((f for f in finais if f["tema"] == p["tema"] and len(nomes & f["_nomes"]) >= minimo), None)
        if alvo:
            alvo["relacionadas"].append(dict(titulo=p["titulo"], rumor=p["rumor"]))
            alvo["veiculos"] = sorted(set(alvo["veiculos"]) | set(p["veiculos"]))
            alvo["links"] = (alvo["links"] + p["links"])[:6]
        else:
            finais.append(dict(p, relacionadas=[], _nomes=nomes))
    for f in finais:
        f.pop("_nomes")
    return finais


def classificar(titulo: str) -> tuple[str, bool]:
    t = " " + titulo.lower() + " "
    tema = next((k for k, ps in TEMAS.items() if any(p in t for p in ps)), "geral")
    return tema, any(r in t for r in RUMOR)


def coletar(cfg_path="config/fontes_noticias.json", horas=24, relatorio=None):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    agora = datetime.now(timezone.utc)
    corte = agora - timedelta(hours=horas)
    todos, saude, trends = [], [], []
    for f in cfg["fontes"]:
        t0 = time.time()
        try:
            raw = _baixar(f["url"])
            itens = ler_espn(raw, f) if f["tipo"] == "espn" else ler_rss(raw, f)
            if f["tipo"] == "trends":
                trends = [i["titulo"] for i in itens][:30]
                saude.append(dict(id=f["id"], ok=True, itens=len(itens), do_fla=None, ms=int((time.time()-t0)*1000)))
                continue
            fla = [dict(i, fonte=f["id"], peso=f["peso"]) for i in itens
                   if eh_do_flamengo(i, cfg) and (i["quando"] is not None and corte <= i["quando"] <= agora)]
            todos += fla
            saude.append(dict(id=f["id"], ok=True, itens=len(itens), do_fla=len(fla), ms=int((time.time()-t0)*1000)))
        except Exception as e:
            saude.append(dict(id=f["id"], ok=False, erro=f"{type(e).__name__}: {e}"[:160]))
    pautas = []
    for g in agrupar(todos):
        principal = max(g["itens"], key=lambda i: (i["peso"], len(i["titulo"])))
        veiculos = sorted({i["veiculo"] for i in g["itens"]})
        tema, rumor = classificar(principal["titulo"])
        em_alta = any(_norm(tr) in _norm(principal["titulo"]) for tr in trends if len(tr) > 3)
        nota = sum(max(i["peso"] for i in g["itens"] if i["veiculo"] == v) for v in veiculos) + 2 * len(veiculos) + (5 if em_alta else 0)
        pautas.append(dict(titulo=principal["titulo"], tema=tema, rumor=rumor, veiculos=veiculos,
                           links=[i["link"] for i in g["itens"]][:4], artigos=[dict(link=i["link"], veiculo=i["veiculo"], quando=i["quando"].isoformat()) for i in g["itens"]][:4], nota=nota, em_alta=em_alta,
                           quando=max((i["quando"] for i in g["itens"] if i["quando"]), default=agora).isoformat()))
    pautas = fundir_mesmo_assunto(pautas)
    pautas.sort(key=lambda p: p["nota"], reverse=True)
    saida = dict(coletado_em=agora.isoformat(), janela_horas=horas, pautas=pautas[:15],
                 assunto_do_momento_br=trends[:10], saude_fontes=saude)
    if relatorio:
        Path(relatorio).write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "data/noticias_hoje.json"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    r = coletar(relatorio=out)
    print("\nSAÚDE DAS FONTES")
    for s in r["saude_fontes"]:
        print(("  OK  " if s["ok"] else "  FALHOU ") + s["id"], s.get("itens", ""), "itens /", s.get("do_fla", ""), "do Fla" if s["ok"] else s.get("erro", ""))
    print("\nTOP PAUTAS DO DIA")
    for p in r["pautas"][:8]:
        print(f"  [{p['nota']:>3}] {p['tema']:<9}{' (RUMOR)' if p['rumor'] else ''} {p['titulo']}  — {', '.join(p['veiculos'][:3])}"
              + (f"  (+{len(p['relacionadas'])} relacionada)" if p.get("relacionadas") else ""))
    if not any(s["ok"] for s in r["saude_fontes"] if s["id"] != "trends_br"):
        sys.exit("nenhuma fonte respondeu")
