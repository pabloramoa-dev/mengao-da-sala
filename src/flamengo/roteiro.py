"""Roteirista do canal: snapshot de dados -> batidas de fala/legenda.

Interface igual a dos outros canais: cada batida e um dict
{'fala': ..., 'legenda': ..., 'tipo': ..., 'dados': {...}}.
'fala' vai para o Kokoro (numero por extenso, virgula decimal),
'legenda' vai para o karaoke.

Tres formatos:
    situacao  - manha, todo dia, so com dado de tabela (100% automatico)
    pos_jogo  - so com partida FINISHED (100% automatico)
    noticia   - texto vindo de RSS, sempre com aprovacao humana antes

Humor do personagem: 'euforico' ou 'indignado'. Nunca neutro - canal de
torcedor sem emocao nao gera comentario.
"""
from __future__ import annotations

UNIDADES = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete",
            "oito", "nove", "dez", "onze", "doze", "treze", "quatorze", "quinze",
            "dezesseis", "dezessete", "dezoito", "dezenove"]
DEZENAS = {20: "vinte", 30: "trinta", 40: "quarenta", 50: "cinquenta",
           60: "sessenta", 70: "setenta", 80: "oitenta", 90: "noventa"}
ORDINAIS = ["", "primeiro", "segundo", "terceiro", "quarto", "quinto", "sexto",
            "sétimo", "oitavo", "nono", "décimo", "décimo primeiro",
            "décimo segundo", "décimo terceiro", "décimo quarto", "décimo quinto",
            "décimo sexto", "décimo sétimo", "décimo oitavo", "décimo nono",
            "vigésimo"]


def por_extenso(n: int) -> str:
    """0 a 99 por extenso — a voz lê melhor que dígito."""
    if n < 20:
        return UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        return DEZENAS[d * 10] + ("" if u == 0 else f" e {UNIDADES[u]}")
    return str(n)


def ordinal(n: int) -> str:
    return ORDINAIS[n] if 0 < n < len(ORDINAIS) else f"{n}º"


def batida(fala: str, legenda: str | None = None, tipo: str = "nenhum", **dados) -> dict:
    return {"fala": fala, "legenda": legenda or fala, "tipo": tipo, "dados": dados}


# ------------------------------------------------------------------ situacao
def situacao(snap: dict) -> dict:
    t = snap["tabela"]
    lidera = t["posicao"] == 1
    humor = "euforico" if lidera else "indignado"

    if lidera:
        abre = (f"O Mengão segue na liderança, com {por_extenso(t['pontos'])} pontos "
                f"em {por_extenso(t['jogos'])} jogos.")
        meio = (f"São {por_extenso(abs(t['diferenca']))} de vantagem para o "
                f"{t['rival_nome']}. Dá pra dormir tranquilo? Não mesmo.")
    else:
        abre = (f"O Flamengo está em {ordinal(t['posicao'])} lugar, com "
                f"{por_extenso(t['pontos'])} pontos.")
        meio = (f"O {t['rival_nome']} tem {por_extenso(t['rival_pontos'])}. "
                "A conta ainda fecha, mas não dá mais pra vacilar.")

    fecha = f"Faltam {por_extenso(t['jogos_restantes'])} jogos. Cada um vale um ano de piada."
    prox = snap.get("proximo_jogo")
    if prox:
        fecha = (f"Faltam {por_extenso(t['jogos_restantes'])} jogos, e o próximo é "
                 f"contra o {prox['adversario']}.")

    return {
        "formato": "situacao",
        "humor": humor,
        "capa": f"{t['posicao']}º LUGAR · {t['pontos']} PONTOS" if not lidera else
                f"LÍDER COM {t['pontos']} PONTOS",
        "batidas": [
            batida(abre, tipo="tabela", posicao=t["posicao"], pontos=t["pontos"]),
            batida(meio, tipo="rival", rival=t["rival_nome"]),
            batida(fecha, tipo="proximo"),
            batida("Segue o Mengão da Sala que aqui a Nação acompanha rodada por rodada.", tipo="cta"),
        ],
    }


# ------------------------------------------------------------------ pos-jogo
def pos_jogo(snap: dict) -> dict | None:
    jogo = snap.get("ultimo_jogo")
    if not jogo or jogo["status"] != "FINISHED" or jogo["resultado"] is None:
        return None  # trava: sem jogo confirmado, nao existe video

    placar_fala = f"{por_extenso(jogo['gols_nossos'])} a {por_extenso(jogo['gols_deles'])}"
    placar_tela = f"{jogo['gols_nossos']} x {jogo['gols_deles']}"
    onde = "no Maracanã" if jogo["mandante"] else "fora de casa"

    if jogo["resultado"] == "vitoria":
        humor = "euforico"
        abre = f"Vitória! {placar_fala} no {jogo['adversario']}, {onde}."
        meio = "Time no jeito, torcida no bolso, e a tabela agradece."
    elif jogo["resultado"] == "empate":
        humor = "indignado"
        abre = f"Empate. {placar_fala} com o {jogo['adversario']}, {onde}."
        meio = "Ponto é ponto, mas esse a gente devia ter ganho e todo mundo sabe."
    else:
        humor = "indignado"
        abre = f"Derrota. {placar_fala} para o {jogo['adversario']}, {onde}."
        meio = "Não dá pra jogar assim. A semana vai ser longa, e com razão."

    t = snap["tabela"]
    fecha = (f"Com isso, o Flamengo fica em {ordinal(t['posicao'])} lugar, "
             f"com {por_extenso(t['pontos'])} pontos.")

    return {
        "formato": "pos_jogo",
        "humor": humor,
        "capa": f"{jogo['casa']} {jogo['gols_casa']} x {jogo['gols_fora']} {jogo['fora']}".upper(),
        "batidas": [
            batida(abre, legenda=abre.replace(placar_fala, placar_tela.replace(" x ", " a ")), tipo="placar",
                   placar=placar_tela),
            batida(meio, tipo="reacao"),
            batida(fecha, tipo="tabela", posicao=t["posicao"]),
            batida("Comenta aí o que você achou do time hoje.", tipo="cta"),
        ],
    }


# ------------------------------------------------------------------- noticia
def noticia(titulo: str, resumo: str, humor: str = "indignado") -> dict:
    """Recebe texto JA REESCRITO com palavras proprias. Nunca copie a materia.

    Este formato sempre passa por aprovacao humana antes de publicar.
    """
    return {
        "formato": "noticia",
        "humor": humor,
        "capa": titulo.upper()[:38],
        "aprovacao_humana": True,
        "batidas": [
            batida(titulo, tipo="manchete"),
            batida(resumo, tipo="contexto"),
            batida("Segue o Mengão da Sala pra não perder o próximo capítulo.", tipo="cta"),
        ],
    }


# ============================================================ pós-jogo v2
# Usa data/analise.json do coletor (ESPN + Cartola + Groq já checada).
# Regra: número e fato vêm SEMPRE do dado (ESPN/Cartola); da Groq só entra o que
# passou na checagem, e mesmo assim como tempero, nunca como fato novo.
import hashlib

NOMES_CURTOS = {"Red Bull Bragantino": "Bragantino", "São Paulo": "São Paulo",
                "Independiente del Valle": "Del Valle", "Estudiantes de La Plata": "Estudiantes"}

GIRIAS = {
    "vitoria_lider": ["Segue o líder!", "Segue o líder, Nação!", "É o Mengão lá em cima!"],
    "vitoria": ["Vitória do Mengão!", "Dá-lhe, Mengo!", "É Flamengo, Nação!"],
    "empate": ["Empate.", "Ficou no empate.", "Um pontinho só."],
    "derrota": ["Derrota.", "Não deu, Nação.", "Dia ruim pro Mengão."],
}
CTA = {
    "vitoria": ["Pra você, quem foi o melhor em campo? Comenta aí!",
                "Qual foi o craque do jogo? Deixa o nome nos comentários!"],
    "empate": ["Quem deixou a desejar hoje? Comenta o nome.",
               "Faltou o quê pra vencer? Comenta aí."],
    "derrota": ["Quem foi o pior em campo? Comenta o nome.",
                "De quem é a culpa hoje? Comenta aí."],
}


def _escolha(lista: list[str], semente: str) -> str:
    """Rodízio determinístico por jogo — o mesmo jogo sempre dá a mesma frase,
    jogos diferentes variam."""
    h = int(hashlib.md5(semente.encode()).hexdigest(), 16)
    return lista[h % len(lista)]


def decimal_fala(x: float) -> str:
    inteiro = int(abs(x))
    dec = round((abs(x) - inteiro) * 10)
    sinal = "menos " if x < 0 else ""
    return sinal + (por_extenso(inteiro) + (f" vírgula {por_extenso(dec)}" if dec else ""))


def _curto(nome: str | None, apelidos: list[str]) -> str:
    if not nome:
        return ""
    for a in apelidos:
        if a and (a.lower() in nome.lower() or nome.lower() in a.lower()):
            return a
    return NOMES_CURTOS.get(nome, nome)


def pos_jogo_v2(analise: dict, tabela: dict | None = None) -> dict | None:
    jogo = analise.get("jogo") or {}
    if jogo.get("resultado") is None:
        return None                                   # trava: sem placar confirmado
    res = jogo["resultado"]
    semente = str(jogo.get("id", "")) + jogo.get("data", "")
    cartola = (analise.get("cartola") or {}).get("jogadores") or []
    apelidos = [j["nome"] for j in cartola]
    adv = NOMES_CURTOS.get(jogo.get("adversario"), jogo.get("adversario"))
    nos, eles = jogo["gols_nossos"], jogo["gols_deles"]
    placar_fala = f"{por_extenso(nos)} a {por_extenso(eles)}"
    placar_tela = f"{nos} x {eles}"
    onde = "no Maracanã" if jogo.get("em_casa") else "fora de casa"
    lider = bool(tabela and tabela.get("posicao") == 1)

    chave = "vitoria_lider" if (res == "vitoria" and lider) else res
    grito = _escolha(GIRIAS[chave], semente)
    placar_fala = placar_fala[0].upper() + placar_fala[1:]
    if res == "vitoria":
        abre = f"{grito} {placar_fala} no {adv}, {onde}."
        humor = "euforico"
    elif res == "empate":
        abre = f"{grito} {placar_fala} com o {adv}, {onde}."
        humor = "tenso"
    else:
        abre = f"{grito} {placar_fala} pro {adv}, {onde}."
        humor = "indignado"

    batidas = [batida(abre, legenda=abre.replace(placar_fala, placar_tela.replace(" x ", " a ")),
                      tipo="placar", placar=placar_tela)]

    # melhor (vitória) ou pior (empate/derrota) — número do Cartola, sempre
    if cartola:
        alvo = cartola[0] if res == "vitoria" else cartola[-1]
        rotulo = "o melhor" if res == "vitoria" else "o pior"
        fala = (f"Pro Cartola, {rotulo} em campo foi o {alvo['nome']}, "
                f"com {decimal_fala(alvo['pontos'])} pontos.")
        legenda = fala.replace(decimal_fala(alvo["pontos"]), f"{alvo['pontos']:.1f}".replace(".", ","))
        batidas.append(batida(fala, legenda=legenda, tipo="nota",
                              nome=alvo["nome"], nota=alvo["pontos"]))

    # a mexida do técnico — prioridade: 1) a que a Groq apontou E a ESPN confirma
    # (é a que a imprensa está discutindo); 2) tirar quem acabou de marcar;
    # 3) tirar o melhor do Cartola; 4) a última troca
    subs = [s for s in jogo.get("substituicoes", []) if s.get("saiu") and not s.get("lesao")]
    if subs:
        def sobrenome(n):
            return (n or "").lower().split()[-1] if n else "#"
        groq_mex = ((analise.get("analise") or {}).get("mexida_do_tecnico") or {})
        marcadores = " ".join(g.get("texto", "") for g in jogo.get("gols", [])
                              if g.get("nosso")).lower()
        topo = [j["nome"].lower() for j in cartola[:2]]
        s = (next((x for x in subs if sobrenome(x["saiu"]) == sobrenome(groq_mex.get("saiu"))), None)
             or next((x for x in subs if sobrenome(x["saiu"]) in marcadores), None)
             or next((x for x in subs if any(t in x["saiu"].lower() for t in topo)), None)
             or subs[-1])
        saiu, entrou = _curto(s["saiu"], apelidos), _curto(s["entrou"], apelidos)
        minuto = (s.get("minuto") or "").replace("'", "").split("+")[0]
        fala = (f"E aos {por_extenso(int(minuto)) if minuto.isdigit() else minuto} minutos, "
                f"o técnico tirou o {saiu} e botou o {entrou}.")
        batidas.append(batida(fala, legenda=fala.replace(por_extenso(int(minuto)), minuto)
                              if minuto.isdigit() else fala, tipo="mexida",
                              minuto=minuto, saiu=saiu, entrou=entrou))
        if sobrenome(s["saiu"]) in marcadores:
            gancho = f"Logo depois do {saiu} fazer o gol!"
        elif any(t in s["saiu"].lower() for t in topo):
            gancho = f"Logo o {saiu}, que tava voando no jogo."
        else:
            gancho = None
        if gancho:
            batidas.append(batida(gancho, tipo="mexida", minuto=minuto, saiu=saiu, entrou=entrou))
        batidas.append(batida("Mexeu certo ou errou feio?", tipo="pergunta"))

    batidas.append(batida(_escolha(CTA[res], semente + "cta"), tipo="cta"))
    topo = {"vitoria_lider": "SEGUE O LÍDER", "vitoria": "VITÓRIA DO MENGÃO",
            "empate": "SÓ UM PONTO", "derrota": "NÃO DEU"}[chave]
    capa = f"{topo}\n{placar_tela} {adv}".upper()
    return {"formato": "pos_jogo_v2", "humor": humor, "capa": capa, "batidas": batidas}
