"""Pauta do post diário do @mengaodasala (dias em que o pós-jogo não fala).

Decide o formato do dia só com dado REAL (ESPN, sem chave) ou fato de história
já conferido na web, e grava a pauta pronta para o gerar.py:

    python -m src.flamengo.diario --out data/pauta_diario.json [--formato X] [--forcar]

Formatos (regra-mãe do editorial: nunca o mesmo dois dias seguidos):
    hoje_tem_mengao - dia de jogo (sempre ganha a vez)
    conta_do_titulo - tabela: posição, pontos, vice, jogos restantes, próximo jogo
    contagem        - quantos dias até o Mengão voltar a campo (Data FIFA etc.)
    zoeira_rival    - rival (Flu, Vasco, Bota, Palmeiras) perdeu nos últimos 4 dias
    voce_sabia      - fato de história do banco FATOS (conferido), sem repetir

Saída com código 3 = "hoje não tem post diário" (dia seguinte a jogo, pós-jogo
já cobre; ou post do dia já feito). O workflow entende como pular.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.flamengo.roteiro import batida, ordinal, por_extenso

ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"
STANDINGS = "https://site.api.espn.com/apis/v2/sports/soccer/bra.1/standings"
UA = "Mozilla/5.0 (X11; Linux x86_64) mengao-da-sala/0.3"
FLA = "819"
LIGAS = {"bra.1": "Brasileirão", "conmebol.libertadores": "Libertadores",
         "bra.copa_do_brazil": "Copa do Brasil"}
RIVAIS = {"3445": "Fluminense", "3454": "Vasco", "6086": "Botafogo", "2029": "Palmeiras"}
BRT = timezone(timedelta(hours=-3))
ESTADO = Path("data/diario.json")
ORDEM = ["conta_do_titulo", "voce_sabia", "contagem", "zoeira_rival"]
HASHTAGS = "#Flamengo #Mengão #NaçãoRubroNegra #Brasileirão #CRF"
NOMES = {"Red Bull Bragantino": "Bragantino", "Estudiantes de La Plata": "Estudiantes",
         "Vasco da Gama": "Vasco", "Athletico Paranaense": "Athletico",
         "Atlético-MG": "Galo", "Independiente del Valle": "Del Valle"}

# Banco de fatos — cada um conferido em fonte pública antes de entrar aqui.
# Regra do editorial: nada de letra de hino, nada de tragédia, nada inventado.
FATOS = [
    {"id": "fundacao", "capa": "VOCÊ SABIA?\n1895",
     "cartao": "17/11/1895",
     "falas": ["O Flamengo nasceu no dia dezessete de novembro de mil oitocentos e noventa e cinco.",
               "E nasceu clube de regata, no remo. O futebol só chegou dezesseis anos depois.",
               "Ou seja: antes de ser o Mais Querido do Brasil, o Mengão era do mar."],
     "legendas": ["O Flamengo nasceu em 17 de novembro de 1895.",
                  "E nasceu clube de regata, no remo. O futebol só chegou 16 anos depois.",
                  None]},
    {"id": "mundial81", "capa": "VOCÊ SABIA?\nTÓQUIO 1981",
     "cartao": "3 x 0 LIVERPOOL",
     "falas": ["Em dezembro de mil novecentos e oitenta e um, em Tóquio, o Flamengo enfrentou o Liverpool.",
               "Resultado: três a zero, e o Mengão campeão do mundo.",
               "Aquele time do Zico até hoje é lembrado como um dos maiores da história."],
     "legendas": ["Em dezembro de 1981, em Tóquio, o Flamengo enfrentou o Liverpool.",
                  "Resultado: 3 a 0, e o Mengão campeão do mundo.", None]},
    {"id": "liberta81", "capa": "VOCÊ SABIA?\nA PRIMEIRA",
     "cartao": "LIBERTADORES 1981",
     "falas": ["A primeira Libertadores do Flamengo veio em mil novecentos e oitenta e um.",
               "A decisão foi contra o Cobreloa, do Chile.",
               "E no mesmo ano ainda veio o Mundial. Ano que a Nação não esquece."],
     "legendas": ["A primeira Libertadores do Flamengo veio em 1981.",
                  "A decisão foi contra o Cobreloa, do Chile.", None]},
    {"id": "zico508", "capa": "VOCÊ SABIA?\nO MAIOR DE TODOS",
     "cartao": "ZICO · 508 GOLS",
     "falas": ["O maior artilheiro da história do Flamengo é o Zico.",
               "Foram quinhentos e oito gols com a camisa rubro-negra.",
               "Não é à toa que chamam de Galinho de Quintino."],
     "legendas": ["O maior artilheiro da história do Flamengo é o Zico.",
                  "Foram 508 gols com a camisa rubro-negra.", None]},
    {"id": "lima2019", "capa": "VOCÊ SABIA?\nLIMA 2019",
     "cartao": "2 x 1 RIVER",
     "falas": ["Final da Libertadores de dois mil e dezenove, em Lima.",
               "O River vencia por um a zero até os minutos finais.",
               "Aí o Gabigol fez dois, e o Mengão virou pra dois a um. Bicampeão da América."],
     "legendas": ["Final da Libertadores de 2019, em Lima.",
                  "O River vencia por 1 a 0 até os minutos finais.",
                  "Aí o Gabigol fez dois, e o Mengão virou pra 2 a 1. Bicampeão da América."]},
    {"id": "dobradinha2019", "capa": "VOCÊ SABIA?\nO ANO MÁGICO",
     "cartao": "2019 · DOBRADINHA",
     "falas": ["Em dois mil e dezenove o Flamengo ganhou a Libertadores e o Brasileirão.",
               "E os dois títulos vieram em dois dias seguidos.",
               "Sábado a América, domingo o Brasil. Ano pra contar pros netos."],
     "legendas": ["Em 2019 o Flamengo ganhou a Libertadores e o Brasileirão.",
                  "E os dois títulos vieram em dois dias seguidos.", None]},
    {"id": "guayaquil2022", "capa": "VOCÊ SABIA?\nO TRI",
     "cartao": "LIBERTADORES 2022",
     "falas": ["O tri da Libertadores veio em dois mil e vinte e dois, em Guayaquil, no Equador.",
               "Um a zero no Athletico Paranaense, gol do Gabigol.",
               "Três finais de Libertadores em quatro anos. Isso é Flamengo."],
     "legendas": ["O tri da Libertadores veio em 2022, em Guayaquil, no Equador.",
                  "1 a 0 no Athletico Paranaense, gol do Gabigol.", None]},
    {"id": "tetra2025", "capa": "VOCÊ SABIA?\nO TETRA",
     "cartao": "LIBERTADORES 2025",
     "falas": ["Em dois mil e vinte e cinco o Flamengo virou o primeiro brasileiro tetracampeão da Libertadores.",
               "Final em Lima, contra o Palmeiras. Um a zero, gol do Danilo.",
               "O vice, de novo, ficou olhando a festa."],
     "legendas": ["Em 2025 o Flamengo virou o primeiro brasileiro tetracampeão da Libertadores.",
                  "Final em Lima, contra o Palmeiras. 1 a 0, gol do Danilo.", None]},
]


# ------------------------------------------------------------------ coleta
def pegar(url: str):
    time.sleep(1.0)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except Exception as exc:                       # sem dado = formato fica de fora
        print(f"[diario] falhou {url[:90]}: {exc}")
        return None


def _curto(nome: str | None) -> str:
    return NOMES.get(nome or "", nome or "")


def _jogo(e: dict, liga: str, time_id: str) -> dict:
    comp = (e.get("competitions") or [{}])[0]
    nos = next((c for c in comp.get("competitors", []) if str((c.get("team") or {}).get("id")) == time_id), {})
    eles = next((c for c in comp.get("competitors", []) if c is not nos), {})

    def gols(c):
        s = c.get("score")
        s = s.get("displayValue") if isinstance(s, dict) else s
        return int(s) if str(s or "").isdigit() else None

    return {"id": e.get("id"), "liga": liga, "competicao": LIGAS.get(liga, liga),
            "utc": e.get("date", ""), "status": ((comp.get("status") or {}).get("type") or {}),
            "adversario": _curto((eles.get("team") or {}).get("displayName")),
            "em_casa": nos.get("homeAway") == "home",
            "estadio": (comp.get("venue") or {}).get("fullName"),
            "gols_nossos": gols(nos), "gols_deles": gols(eles)}


def agenda(time_id: str, ligas=LIGAS) -> tuple[list[dict], list[dict]]:
    """(encerrados, futuros) do time, em todas as competições, por data."""
    feitos, futuros = [], []
    for liga in ligas:
        for extra in ("", "?fixture=true"):
            d = pegar(f"{ESPN}/{liga}/teams/{time_id}/schedule{extra}") or {}
            for e in d.get("events", []):
                j = _jogo(e, liga, time_id)
                if j["status"].get("completed"):
                    feitos.append(j)
                elif j["status"].get("state") == "pre":
                    futuros.append(j)
    uniq = lambda l: list({j["id"]: j for j in l}.values())
    return (sorted(uniq(feitos), key=lambda j: j["utc"]),
            sorted(uniq(futuros), key=lambda j: j["utc"]))


def tabela() -> dict | None:
    d = pegar(STANDINGS)
    if not d:
        return None
    ent = [e for g in (d.get("children") or [d]) for e in (g.get("standings") or {}).get("entries", [])]

    def st(e, n):
        return next((s.get("value") for s in e.get("stats", []) if s.get("name") == n), None)

    linhas = sorted(({"id": str(e["team"]["id"]), "time": _curto(e["team"]["displayName"]),
                      "pos": int(st(e, "rank") or 99), "pts": int(st(e, "points") or 0),
                      "j": int(st(e, "gamesPlayed") or 0)} for e in ent), key=lambda l: l["pos"])
    nossa = next((l for l in linhas if l["id"] == FLA), None)
    if not nossa:
        return None
    rival = linhas[1] if nossa["pos"] == 1 else linhas[0]
    return {"posicao": nossa["pos"], "pontos": nossa["pts"], "jogos": nossa["j"],
            "rival_nome": rival["time"], "rival_pontos": rival["pts"],
            "diferenca": nossa["pts"] - rival["pts"], "jogos_restantes": max(0, 38 - nossa["j"])}


def _utc(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _hora_brt(j: dict) -> str:
    t = _utc(j["utc"]).astimezone(BRT)
    return f"{t.hour}h" + (f"{t.minute:02d}" if t.minute else "")


def _hora_fala(j: dict) -> str:
    t = _utc(j["utc"]).astimezone(BRT)
    return f"às {por_extenso(t.hour)}" + (f" e {por_extenso(t.minute)}" if t.minute else "") + \
           (" da noite" if t.hour >= 18 else " da tarde" if t.hour >= 12 else " da manhã")


def _contra(j: dict) -> str:
    return f"{'Flamengo x ' + j['adversario'] if j['em_casa'] else j['adversario'] + ' x Flamengo'}"


# ---------------------------------------------------------------- roteiros
def hoje_tem_mengao(prox: dict, t: dict | None) -> dict:
    onde = "no Maracanã" if prox["em_casa"] and "Maracan" in (prox.get("estadio") or "") else \
           ("em casa" if prox["em_casa"] else "fora de casa")
    b = [batida("Hoje tem Mengão!", tipo="abre"),
         batida(f"É contra o {prox['adversario']}, {onde}, pelo {prox['competicao']}.",
                tipo="jogo", cartao=_contra(prox).upper()),
         batida(f"A bola rola {_hora_fala(prox)}.",
                legenda=f"A bola rola às {_hora_brt(prox)}, horário de Brasília.",
                tipo="hora", cartao=_hora_brt(prox).upper())]
    if t and t["posicao"] == 1 and prox["liga"] == "bra.1":
        b.append(batida("Líder em campo. É pra ganhar e seguir lá em cima.", tipo="tabela",
                        posicao=1, pontos=t["pontos"]))
    b.append(batida("Crava aí nos comentários: qual vai ser o placar?", tipo="pergunta",
                    cartao="CRAVA O PLACAR"))
    return {"formato": "hoje_tem_mengao", "humor": "euforico",
            "capa": f"HOJE TEM MENGÃO\n{_contra(prox)}".upper(), "batidas": b}


def conta_do_titulo(t: dict, prox: dict | None) -> dict:
    lider = t["posicao"] == 1
    if lider:
        b = [batida(f"O Mengão é o líder do Brasileirão, com {por_extenso(t['pontos'])} pontos.",
                    legenda=f"O Mengão é o líder do Brasileirão, com {t['pontos']} pontos.",
                    tipo="tabela", posicao=1, pontos=t["pontos"]),
             batida(f"O vice é o {t['rival_nome']}, {por_extenso(abs(t['diferenca']))} pontos atrás.",
                    legenda=f"O vice é o {t['rival_nome']}, {abs(t['diferenca'])} pontos atrás.",
                    tipo="rival", cartao=f"+{t['diferenca']} NA FRENTE")]
    else:
        b = [batida(f"O Flamengo está em {ordinal(t['posicao'])} lugar, com {por_extenso(t['pontos'])} pontos.",
                    legenda=f"O Flamengo está em {t['posicao']}º lugar, com {t['pontos']} pontos.",
                    tipo="tabela", posicao=t["posicao"], pontos=t["pontos"]),
             batida(f"O líder é o {t['rival_nome']}, com {por_extenso(t['rival_pontos'])}.",
                    legenda=f"O líder é o {t['rival_nome']}, com {t['rival_pontos']}.",
                    tipo="rival", cartao=f"{t['diferenca']} DO LÍDER")]
    falta = t["jogos_restantes"]
    fala = f"Faltam {por_extenso(falta)} rodadas."
    leg = f"Faltam {falta} rodadas."
    if prox:
        fala += f" A próxima é contra o {prox['adversario']}."
        leg += f" A próxima é contra o {prox['adversario']}."
    b.append(batida(fala, legenda=leg, tipo="proximo", cartao=f"FALTAM {falta}"))
    b.append(batida("Dá pra dormir tranquilo? Comenta aí.", tipo="pergunta",
                    cartao="DÁ PRA DORMIR TRANQUILO?"))
    capa = (f"LÍDER COM {t['pontos']}\n+{t['diferenca']} NO VICE" if lider
            else f"{t['posicao']}º LUGAR\n{t['pontos']} PONTOS")
    return {"formato": "conta_do_titulo", "humor": "euforico" if lider else "tenso",
            "capa": capa, "batidas": b}


def contagem(prox: dict, dias: int) -> dict:
    data = _utc(prox["utc"]).astimezone(BRT)
    dia = f"{data.day:02d}/{data.month:02d}"
    b = [batida(f"Faltam {por_extenso(dias)} dias pro Mengão voltar a campo.",
                legenda=f"Faltam {dias} dias pro Mengão voltar a campo.",
                tipo="contagem", cartao=f"{dias} DIAS"),
         batida(f"Vai ser contra o {prox['adversario']}, pelo {prox['competicao']}.",
                tipo="jogo", cartao=_contra(prox).upper()),
         batida(f"Dia {por_extenso(data.day)}, {_hora_fala(prox)}.",
                legenda=f"Dia {dia}, às {_hora_brt(prox)}, horário de Brasília.",
                tipo="hora", cartao=dia),
         batida("Até lá, a Nação sofre de abstinência. Quem mais?", tipo="pergunta",
                cartao="ABSTINÊNCIA DE MENGÃO")]
    return {"formato": "contagem", "humor": "tenso",
            "capa": f"FALTAM {dias} DIAS\nPRO MENGÃO", "batidas": b}


def zoeira_rival(nome: str, j: dict) -> dict:
    placar = f"{j['gols_nossos']} x {j['gols_deles']}"
    fala_placar = f"{por_extenso(j['gols_deles'])} a {por_extenso(j['gols_nossos'])}"
    b = [batida(f"Alô, torcida do {nome}...", tipo="abre"),
         batida(f"Perdeu de {fala_placar} pro {j['adversario']}, pelo {j['competicao']}.",
                legenda=f"Perdeu de {j['gols_deles']} a {j['gols_nossos']} pro {j['adversario']}, "
                        f"pelo {j['competicao']}.",
                tipo="placar", placar=f"{nome} {placar} {j['adversario']}".upper()),
         batida("Aqui na sala a gente assistiu. E secou com carinho.", tipo="reacao"),
         batida(f"Marca aquele amigo do {nome} nos comentários.", tipo="pergunta",
                cartao="MARCA O AMIGO")]
    return {"formato": "zoeira_rival", "humor": "debochado",
            "capa": f"ALÔ, {nome}...\n{placar}".upper(), "batidas": b}


def voce_sabia(f: dict) -> dict:
    b = []
    for i, (fala, leg) in enumerate(zip(f["falas"], f["legendas"])):
        extra = {"cartao": f["cartao"]} if i == 0 else {}
        b.append(batida(fala, legenda=leg or fala, tipo="fato", **extra))
    b.append(batida("Sabia dessa? Comenta aí e manda pra um flamenguista.", tipo="pergunta",
                    cartao="SABIA DESSA?"))
    return {"formato": "voce_sabia", "humor": "euforico", "capa": f["capa"], "batidas": b,
            "fato": f["id"]}


# ----------------------------------------------------------------- escolha
def legenda_post(pauta: dict) -> str:
    capa = pauta["capa"].replace("\n", " · ")
    linhas = [f"{capa} 🔴⚫", ""]
    linhas += [b["legenda"] for b in pauta["batidas"] if b["tipo"] not in ("pergunta", "abre")]
    perg = next((b["legenda"] for b in pauta["batidas"] if b["tipo"] == "pergunta"), None)
    if perg:
        linhas += ["", perg + " 👇"]
    linhas += ["", "Segue o @mengaodasala 🔴⚫", "", HASHTAGS]
    return "\n".join(linhas) + "\n"


def montar(agora: datetime, estado: dict, so: str | None = None) -> tuple[dict | None, str]:
    feitos, futuros = agenda(FLA)
    hoje = agora.astimezone(BRT).date()
    ultimo = feitos[-1] if feitos else None
    prox = futuros[0] if futuros else None

    if ultimo and not so and (agora - _utc(ultimo["utc"])) < timedelta(hours=30):
        return None, f"jogo encerrado há menos de 30h ({ultimo['adversario']}) — pós-jogo cobre"

    if prox and _utc(prox["utc"]).astimezone(BRT).date() == hoje and so in (None, "hoje_tem_mengao"):
        return hoje_tem_mengao(prox, tabela()), "dia de jogo"

    candidatos: dict[str, dict] = {}
    t = tabela()
    if t:
        candidatos["conta_do_titulo"] = conta_do_titulo(t, prox)
    if prox:
        dias = (_utc(prox["utc"]).astimezone(BRT).date() - hoje).days
        if dias >= 2:
            candidatos["contagem"] = contagem(prox, dias)
    if not so or so == "zoeira_rival":
        for rid, nome in RIVAIS.items():
            f_, _ = agenda(rid, ligas=("bra.1", "conmebol.libertadores", "bra.copa_do_brazil",
                                       "conmebol.sudamericana"))
            j = f_[-1] if f_ else None
            if j and j["gols_nossos"] is not None and j["gols_nossos"] < j["gols_deles"] \
                    and (agora - _utc(j["utc"])) < timedelta(days=4) \
                    and estado.get("zoeira_jogo") != j["id"]:
                candidatos["zoeira_rival"] = zoeira_rival(nome, j)
                candidatos["zoeira_rival"]["jogo_rival"] = j["id"]
                break
    usados = set(estado.get("fatos_usados", []))
    livres = [f for f in FATOS if f["id"] not in usados] or FATOS
    semente = int(hashlib.md5(hoje.isoformat().encode()).hexdigest(), 16)
    candidatos["voce_sabia"] = voce_sabia(livres[semente % len(livres)])

    if so:
        if so not in candidatos:
            raise SystemExit(f"formato {so} indisponível hoje (sem dado real): {list(candidatos)}")
        return candidatos[so], "forçado"

    anterior = estado.get("formato")
    i0 = (ORDEM.index(anterior) + 1) if anterior in ORDEM else 0
    for k in range(len(ORDEM)):
        f = ORDEM[(i0 + k) % len(ORDEM)]
        if f in candidatos and f != anterior:
            return candidatos[f], f"rodízio (ontem: {anterior})"
    return None, "nenhum formato disponível"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--formato", choices=["hoje_tem_mengao", *ORDEM])
    ap.add_argument("--forcar", action="store_true", help="ignora 'post de hoje já feito'")
    a = ap.parse_args()

    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    agora = datetime.now(timezone.utc)
    hoje = agora.astimezone(BRT).date().isoformat()
    if estado.get("data") == hoje and not a.forcar:
        print(f"[diario] post de hoje ({hoje}) já feito: {estado.get('formato')}")
        return 3
    pauta, motivo = montar(agora, estado, a.formato)
    print(f"[diario] {motivo}")
    if pauta is None:
        return 3
    pauta["legenda_post"] = legenda_post(pauta)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(pauta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[diario] formato: {pauta['formato']}")
    for b in pauta["batidas"]:
        print("   ·", b["fala"])
    print("----- LEGENDA -----\n" + pauta["legenda_post"])
    return 0


def registrar(pauta_path: str) -> None:
    """Chamado DEPOIS do vídeo gerado: grava o estado para o rodízio."""
    pauta = json.loads(Path(pauta_path).read_text(encoding="utf-8"))
    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    estado["data"] = datetime.now(timezone.utc).astimezone(BRT).date().isoformat()
    estado["formato"] = pauta["formato"]
    if pauta.get("fato"):
        estado["fatos_usados"] = (estado.get("fatos_usados", []) + [pauta["fato"]])[-(len(FATOS) - 1):]
    if pauta.get("jogo_rival"):
        estado["zoeira_jogo"] = pauta["jogo_rival"]
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[diario] estado: {estado}")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--registrar":
        registrar(sys.argv[2])
        sys.exit(0)
    sys.exit(main())
