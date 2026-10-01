"""Plantão da Sala — Reel diário com as 3 notícias do Mengão das últimas 24 h.

Fluxo: data/noticias_hoje.json (src.flamengo.coletor.noticias) → 3 pautas de
maior nota → a Groq reescreve cada uma COM PALAVRAS PRÓPRIAS a partir do título
→ validação → pauta pronta para o gerar.py (15–25 s).

Juninho apresenta, o Primo zoa, a TV mostra a manchete curta.

Travas editoriais:
- nunca copia texto de site: fala muito parecida com o título é recusada;
- nada inventado: número ou nome próprio que não esteja no título é recusado;
- rumor é dito como rumor (marcador obrigatório na fala);
- fontes (veículos) vão na legenda;
- sem Groq, sem chave, sem arquivo ou com arquivo vazio/velho → devolve None e o
  diário cai no rodízio antigo, sem falhar.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import unicodedata
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.flamengo.roteiro import batida

ARQUIVO = Path("data/noticias_hoje.json")
MAX_IDADE_H = 30
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELO = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MARCAS_RUMOR = ("rumor", "especula", "pode ", "estaria", "negocia", "sonda", "interesse", "possível", "possivel",
                "ainda não", "ainda nao", "não confirm", "nao confirm")
HUMORES_OK = {"euforico", "neutra", "tenso", "sofrendo", "indignado", "chocado"}
HUMOR_TEMA = {"dm": "neutra", "mercado": "tenso", "jogo": "euforico", "tecnico": "neutra",
              "bastidor": "tenso", "torcida": "euforico", "geral": "neutra"}
LIVRES = {"Mengão", "Mengo", "Flamengo", "Nação", "Juninho", "Primo", "Sala", "Plantão", "Maracanã",
          "Brasileirão", "Libertadores", "Copa", "Brasil", "Rio", "Rubro-Negro", "Rubro", "Negro", "Série",
          "Fla", "Ninho", "Gávea", "Rumor", "Olha", "Segundo", "E", "É", "A", "O", "Hoje", "Agora"}
NUM_PALAVRAS = {"dois": 2, "duas": 2, "três": 3, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6, "sete": 7,
                "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "quinze": 15, "vinte": 20,
                "trinta": 30, "cem": 100, "mil": 1000, "milhão": 10**6, "milhões": 10**6, "milhoes": 10**6}
EXTENSO = {1: "Uma", 2: "Duas", 3: "Três"}


# ------------------------------------------------------------------ entrada
def carregar(caminho: Path = ARQUIVO, agora: datetime | None = None) -> list[dict]:
    """Pautas utilizáveis do coletor; lista vazia se o arquivo faltar, estiver vazio ou velho."""
    try:
        d = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except Exception:
        return []
    agora = agora or datetime.now(timezone.utc)
    try:
        coletado = datetime.fromisoformat(d["coletado_em"])
        if agora - coletado > timedelta(hours=MAX_IDADE_H):
            return []
    except Exception:
        return []
    return [p for p in d.get("pautas") or [] if str(p.get("titulo", "")).strip() and p.get("veiculos")]


def escolher(pautas: list[dict], n: int = 3) -> list[dict]:
    return sorted(pautas, key=lambda p: p.get("nota", 0), reverse=True)[:n]


# ------------------------------------------------------------------ validação
def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", t)


def _numeros(t: str) -> set[int]:
    ns = {int(n) for n in re.findall(r"\d+", t)}
    for w in _norm(t).split():
        if w in NUM_PALAVRAS:
            ns.add(NUM_PALAVRAS[w])
    return ns


def _maior_trecho_igual(a: str, b: str) -> int:
    wa, wb = _norm(a).split(), _norm(b).split()
    m = difflib.SequenceMatcher(None, wa, wb, autojunk=False).find_longest_match(0, len(wa), 0, len(wb))
    return m.size


def copia_do_titulo(titulo: str, fala: str) -> bool:
    if _maior_trecho_igual(titulo, fala) >= 6:
        return True
    return difflib.SequenceMatcher(None, _norm(titulo), _norm(fala)).ratio() > 0.8


def nomes_novos(titulo: str, texto: str) -> list[str]:
    """Palavras com maiúscula no meio da frase que não vieram do título."""
    base = set(_norm(titulo).split())
    novos = []
    for m in re.finditer(r"[\wÀ-ú-]+", texto):
        w = m.group(0)
        antes = texto[:m.start()].rstrip()
        inicio = not antes or antes.endswith((".", "!", "?", ":", "…", '"', ","))
        if w[:1].isupper() and not inicio and w not in LIVRES and _norm(w).strip() not in base:
            novos.append(w)
    return novos


def validar_item(pauta: dict, item: dict) -> dict:
    """Devolve o item limpo ou levanta ValueError com o motivo."""
    from src.flamengo.dialogos import PROIBIDO, CLUBES
    titulo = pauta["titulo"]
    fala = " ".join(str(item.get("fala", "")).split())
    tv = " ".join(str(item.get("tv", "")).split()).upper()[:30]
    zoeira = " ".join(str(item.get("zoeira", "") or "").split())
    if not (20 <= len(fala) <= 120):
        raise ValueError(f"fala com tamanho fora do limite: {fala!r}")
    if not (3 <= len(tv) <= 30):
        raise ValueError(f"manchete da TV inválida: {tv!r}")
    for texto in (fala, tv, zoeira):
        if PROIBIDO.search(texto):
            raise ValueError(f"palavra proibida: {texto}")
    if copia_do_titulo(titulo, fala):
        raise ValueError(f"fala copia o título: {fala}")
    extras = (_numeros(fala) | _numeros(tv) | _numeros(zoeira)) - _numeros(titulo) - {1}
    if extras:
        raise ValueError(f"número fora do título {sorted(extras)}: {fala}")
    novos = nomes_novos(titulo, fala) + nomes_novos(titulo, zoeira)
    if novos:
        raise ValueError(f"nome fora do título {novos}: {fala} / {zoeira}")
    baixa_t = f" {titulo.lower()} "
    for c in CLUBES:
        alvo = r"\b" + re.escape(c.strip()) + r"\b"
        if re.search(alvo, f" {(fala + ' ' + zoeira).lower()} ") and not re.search(alvo, baixa_t):
            raise ValueError(f"clube fora do título ({c.strip()})")
    if zoeira and not (8 <= len(zoeira) <= 90):
        zoeira = ""
    if pauta.get("rumor") and not any(m in fala.lower() for m in MARCAS_RUMOR):
        fala = "Rumor: " + fala[0].lower() + fala[1:]
    humor = item.get("humor") if item.get("humor") in HUMORES_OK else None
    return {"fala": fala, "tv": tv, "zoeira": zoeira, "humor": humor}


# ------------------------------------------------------------------ Groq
SISTEMA = """Você escreve o "Plantão da Sala", Reel do canal de humor @mengaodasala (torcida do Flamengo).
Juninho (torcedor do Flamengo) conta as notícias; o Primo (rival de outro time) faz uma zoeira leve.
Regras OBRIGATÓRIAS:
1. Reescreva cada notícia COM PALAVRAS PRÓPRIAS. Nunca copie o título nem trechos dele.
2. Use SOMENTE os fatos do título. Não acrescente nomes, números, datas, placares, valores, clubes ou detalhes.
3. Se "rumor" for true, a fala deixa claro que é rumor (ex.: "Rumor: ...", "Corre o rumor de que ...").
4. fala: 1 frase, até 110 caracteres, tom de torcedor animado, português do Brasil falado.
5. tv: manchete curta em MAIÚSCULAS, até 26 caracteres, sem inventar nada.
6. humor: como o torcedor recebe a notícia: "euforico" (boa), "neutra", "tenso" (incerta/rumor),
   "sofrendo" (ruim), "indignado" ou "chocado".
7. zoeira: fala curta do Primo (até 70 caracteres), provocação leve de arquibancada, sem nomes, sem números,
   sem ofensa, sem preconceito, sem tragédia, sem violência.
Responda só JSON: {"itens":[{"id":0,"fala":"...","tv":"...","humor":"neutra","zoeira":"..."}]}"""


def _groq(pautas: list[dict]) -> list[dict] | None:
    chave = os.environ.get("GROQ_API_KEY")
    if not chave:
        print("[plantao] sem GROQ_API_KEY: plantão fica de fora hoje")
        return None
    entrada = [{"id": k, "titulo": p["titulo"], "tema": p.get("tema"), "rumor": bool(p.get("rumor"))}
               for k, p in enumerate(pautas)]
    corpo = {"model": GROQ_MODELO, "temperature": 0.6, "response_format": {"type": "json_object"},
             "messages": [{"role": "system", "content": SISTEMA},
                          {"role": "user", "content": json.dumps({"noticias": entrada}, ensure_ascii=False)}]}
    req = urllib.request.Request(GROQ_URL, data=json.dumps(corpo).encode("utf-8"), method="POST",
                                 headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json",
                                          "User-Agent": "mengao-da-sala/plantao"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            resp = json.loads(r.read().decode("utf-8"))
        return json.loads(resp["choices"][0]["message"]["content"]).get("itens") or None
    except Exception as exc:
        print(f"[plantao] Groq falhou: {type(exc).__name__}: {exc}"[:200])
        return None


def reescrever(pautas: list[dict], gerador=_groq) -> list[tuple[dict, dict]]:
    """Pares (pauta, texto validado). Itens recusados ficam de fora."""
    itens = gerador(pautas) or []
    por_id = {int(i.get("id", -1)): i for i in itens if isinstance(i, dict) and str(i.get("id", "")).lstrip("-").isdigit()}
    bons = []
    for k, p in enumerate(pautas):
        if k not in por_id:
            continue
        try:
            bons.append((p, validar_item(p, por_id[k])))
        except ValueError as exc:
            print(f"[plantao] item {k} recusado: {exc}")
    return bons


# ------------------------------------------------------------------ pauta
def montar(pares: list[tuple[dict, dict]], hoje) -> dict:
    n = len(pares)
    b = [batida(f"Plantão da Sala no ar! {EXTENSO[n]} {'notícia' if n == 1 else 'notícias'} do Mengão.",
                tipo="abre", cartao="PLANTÃO DA SALA")]
    b[0].update(personagem="rubro", humor="euforico", gesto="bracos_cima", plano="close", reacao="celular")
    zoeiras = 0
    for k, (p, t) in enumerate(pares):
        nb = batida(t["fala"], tipo="noticia", cartao=t["tv"], rumor=bool(p.get("rumor")))
        nb.update(personagem="rubro", humor=t.get("humor") or HUMOR_TEMA.get(p.get("tema"), "neutra"),
                  gesto="contar" if k % 2 == 0 else "explicar", reacao="celular",
                  plano="close" if p.get("rumor") else "dupla")
        b.append(nb)
        # o Primo entra no máximo duas vezes, para o Reel ficar entre 15 e 25 s
        if t["zoeira"] and zoeiras < 2 and (k == 0 or k == n - 1):
            z = batida(t["zoeira"], tipo="reacao")
            z.update(personagem="primo", humor="debochado", gesto="celular", reacao="nao", plano="dupla")
            b.append(z)
            zoeiras += 1
    capa = f"{'A NOTÍCIA' if n == 1 else 'AS ' + EXTENSO[n].upper()} DO MENGÃO\nHOJE NA SALA"
    return {"formato": "plantao_da_sala", "humor": "euforico", "capa": capa, "batidas": b,
            "episodio": f"plantao:{hoje}",
            "noticias": [{"titulo_original": p["titulo"], "veiculos": p["veiculos"], "links": p.get("links", []),
                          "rumor": bool(p.get("rumor")), "tema": p.get("tema"), "fala": t["fala"]} for p, t in pares]}


def legenda(pauta: dict, hashtags: str) -> str:
    linhas = ["PLANTÃO DA SALA 🔴⚫", ""]
    for k, n in enumerate(pauta["noticias"], 1):
        linhas.append(f"{k}. {n['fala']}")
        fontes = ", ".join(n["veiculos"][:4])
        linhas.append(f"   Fontes: {fontes}" + (" · rumor, ainda sem confirmação" if n["rumor"] else ""))
    linhas += ["", "Textos com palavras nossas a partir das manchetes dos veículos citados. Rumor é tratado como rumor.",
               "", "Segue o @mengaodasala pra não perder nenhuma notícia do Mengão, ou manda pra um flamenguista amigo 🔴⚫",
               "", hashtags]
    return "\n".join(linhas) + "\n"


def gerar(hoje, caminho: Path = ARQUIVO, gerador=_groq) -> dict | None:
    """Pauta do Plantão ou None (sem notícia suficiente / sem texto válido)."""
    pautas = escolher(carregar(caminho))
    if len(pautas) < 2:
        print(f"[plantao] notícias insuficientes ({len(pautas)}): fica de fora hoje")
        return None
    pares = reescrever(pautas, gerador)
    if len(pares) < 2:
        print(f"[plantao] só {len(pares)} notícia(s) passaram na checagem: fica de fora hoje")
        return None
    return montar(pares, hoje)
