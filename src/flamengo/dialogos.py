"""Diálogos do Juninho x Primo Secador — roteiro com DIREÇÃO por fala.

Na v1 eram 4 frases soltas, curtas, sem conflito, sem virada e sem CTA.
Agora cada esquete segue a fórmula que já funciona nos outros canais:

    1. GANCHO     — a primeira fala já é provocação (conflito no quadro 0)
    2. ESCALADA   — 3 a 5 trocas, cada resposta sobe o tom
    3. VIRADA     — a punchline, com carimbo na tela e câmera fechando
    4. PERGUNTA   — Juninho joga pra Nação (gera comentário)
    5. CTA        — regra do canal: seguir o @mengaodasala / mandar pro amigo

Cada fala carrega a direção de cena:
    quem     rubro (Juninho) | primo (Primo Secador)
    humor    expressão de quem fala  (neutra euforico indignado tenso
             debochado rindo chocado sofrendo)
    gesto    repouso explicar apontar bracos_cima facepalm ombros cruzar
             peito celular maos_juntas contar
    reacao   o que o OUTRO faz enquanto ouve: revirar rir nao sim cruzar
             celular choque sofrer orgulho
    plano    dupla | close | impacto   (impacto = câmera fecha + tremida)
    carimbo  texto do carimbo de papel (só na virada)
    efeito   confete | nenhum

Fonte das falas: banco conferido com recortes históricos explícitos com data de corte explícita.
O torcedor rival muda por episódio; Juninho sempre ganha a comparação.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

HUMORES = {"neutra", "euforico", "indignado", "tenso", "debochado", "rindo", "chocado", "sofrendo"}
GESTOS = {"repouso", "explicar", "apontar", "bracos_cima", "facepalm", "ombros", "cruzar",
          "peito", "celular", "maos_juntas", "contar"}
REACOES = {"revirar", "rir", "nao", "sim", "cruzar", "celular", "choque", "sofrer", "orgulho"}
PLANOS = {"dupla", "close", "impacto"}

CTAS = [
    "Segue o Mengão da Sala pra não perder nenhuma resenha do Mengão!",
    "Manda esse vídeo pro flamenguista que tem um primo assim!",
    "Segue o Mengão da Sala que amanhã o primo volta. Infelizmente.",
]


def F(quem, fala, humor, gesto="explicar", reacao=None, plano="dupla", carimbo=None,
      efeito=None, legenda=None):
    return {k: v for k, v in dict(quem=quem, fala=fala, humor=humor, gesto=gesto, reacao=reacao,
                                  plano=plano, carimbo=carimbo, efeito=efeito,
                                  legenda=legenda).items() if v is not None}


# Comparações fechadas até 2025: não antecipam vencedores de 2026.
# Os números são calculados a partir dos anos; o rival erra na ficção,
# Juninho apresenta o resultado verdadeiro. Não há geração livre de fatos.
FONTE_LIB = "https://www.sportingnews.com/br/futebol/noticias/libertadores-todos-os-clubes-campeoes-do-torneio/73503f43b0e8c5160ae63734"
FONTE_FLA = "https://www.flamengo.com.br/noticias/futebol/flamengo-vence-palmeiras-e-se-torna-o-primeiro-tetracampeao-da-libertadores"
FONTE_COPA = "https://www.cbf.com.br/futebol-brasileiro/noticias/detalhes/competicoes-copa-brasil-masculino/com-quinto-titulo-flamengo-se-torna-segundo-maior-campeao-da-copa-betano-do-brasil"
LIBERTADORES = {
    "Flamengo": [1981, 2019, 2022, 2025],
    "Vasco": [1998], "Fluminense": [2023], "Botafogo": [2024],
    "Palmeiras": [1999, 2020, 2021], "Corinthians": [2012],
    "São Paulo": [1992, 1993, 2005], "Santos": [1962, 1963, 2011],
    "Grêmio": [1983, 1995, 2017], "Internacional": [2006, 2010],
    "Cruzeiro": [1976, 1997], "Atlético-MG": [2013],
}
EXTENSO = {0: "nenhum", 1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco"}
FINAIS = [
    "Você não sabe de nada! Vai pegar uma cerveja pra mim e deixa a conta das taças comigo!",
    "Primo, tua confiança é de campeão. A resposta é de recuperação!",
    "Teu palpite veio cheio. A conta das taças veio vazia!",
    "Pode procurar no celular. Só não vale editar a história!",
    "Aqui na sala o controle é meu. E nessa conta a vantagem também!",
    "Você trouxe a camisa. Esqueceu de trazer a resposta certa!",
]


def _desafio(rival, anos, recente=False):
    janela = "de 2019 a 2025" if recente else "até 2025"
    nf = sum(y >= 2019 for y in LIBERTADORES["Flamengo"]) if recente else 4
    nr = sum(y >= 2019 for y in anos) if recente else len(anos)
    assert nf > nr
    i = list(LIBERTADORES).index(rival)
    correcoes = [
        f"Errou! {janela.capitalize()}: Flamengo, {EXTENSO[nf]} títulos. {rival}, {EXTENSO[nr]}. Confiança não é taça!",
        f"Não, primo! {janela.capitalize()}, deu {EXTENSO[nf]} pro Flamengo e {EXTENSO[nr]} pro {rival}. Conta de novo!",
    ]
    return dict(chave="titulos_" + rival.lower().replace(" ", "_") + ("_recente" if recente else "_total"),
        capa=rival.upper() + "\nERROU A CONTA", rival=rival,
        fato={"competicao": "Libertadores", "periodo": janela, "flamengo": nf, "rival": nr},
        fontes=[FONTE_FLA, FONTE_LIB], falas=[
        F("rubro", f"Primo, {janela}, quem ganhou mais Libertadores: Flamengo ou {rival}?", "debochado", "contar", "revirar", "close"),
        F("primo", f"O {rival}, claro! Essa você escolheu fácil demais!", "euforico", "peito", "rir"),
        F("rubro", correcoes[int(recente)], "rindo", "contar", "choque", "impacto", carimbo=f"FLA {nf} X {nr}", efeito="confete"),
        F("primo", "Eu tava contando com as taças que a gente ainda vai ganhar!", "tenso", "celular", "rir"),
        F("rubro", "Taça imaginária? Então teu museu fica dentro da tua cabeça!", "debochado", "apontar", "sofrer", "close"),
        F("rubro", FINAIS[(i + int(recente)) % len(FINAIS)], "rindo", "apontar", "revirar", "impacto"),
        F("rubro", f"Qual amigo do {rival} ia errar essa também? Marca ele aqui!", "debochado", "contar", "celular", "close"),
    ])


BANCO = [_desafio(rival, anos, recente) for rival, anos in LIBERTADORES.items()
         if rival != "Flamengo" for recente in (False, True)]


# Copa do Brasil com recorte fechado em 2024; Grêmio empata e Cruzeiro
# supera o Flamengo, portanto nenhum dos dois entra nesta comparação.
COPA_2024 = {"Vasco": 1, "Fluminense": 1, "Botafogo": 0, "Palmeiras": 4,
             "Corinthians": 3, "São Paulo": 1, "Santos": 1,
             "Internacional": 1, "Atlético-MG": 2}
FONTE_COPA_RANK = "https://www.espn.com.br/futebol/copa-do-brasil/artigo/_/id/14411948/quem-sao-maiores-campeoes-copa-do-brasil-ranking-titulos"
FONTE_CARIOCA = "https://www.flamengo.com.br/noticias/futebol/flamengo-vence-o-fluminense-nos-penaltis-e-conquista-seu-40--titulo-do-campeonato-carioca"
FONTE_CARIOCA_RANK = "https://ge.globo.com/rj/futebol/campeonato-carioca/noticia/2026/01/10/guia-do-carioca-2026-saiba-tudo-sobre-o-campeonato-que-comeca-neste-sabado.ghtml"


def _outro_campeonato(rival, competicao, periodo, nf, nr, fontes):
    assert nf > nr
    numeros = {**EXTENSO, 21: "vinte e um", 24: "vinte e quatro", 33: "trinta e três", 40: "quarenta"}
    esq = _desafio(rival, LIBERTADORES[rival])
    esq.update(chave="titulos_" + rival.lower().replace(" ", "_") + "_" + competicao.lower().replace(" ", "_"),
               fato={"competicao": competicao, "periodo": periodo, "flamengo": nf, "rival": nr}, fontes=fontes)
    falas = esq["falas"]
    falas[0]["fala"] = f"Primo, {periodo}, quem tinha mais títulos {'do' if competicao == 'Campeonato Carioca' else 'da'} {competicao}: Flamengo ou {rival}?"
    falas[2].update(fala=f"Errou! Flamengo: {numeros[nf]}. {rival}: {numeros[nr]}. Teu palpite não ganhou taça!", carimbo=f"FLA {nf} X {nr}")
    return esq


BANCO += [_outro_campeonato(rival, "Copa do Brasil", "até 2024", 5, nr,
                           [FONTE_COPA, FONTE_COPA_RANK]) for rival, nr in COPA_2024.items()]
BANCO += [_outro_campeonato(rival, "Campeonato Carioca", "até março de 2026", 40, nr,
                           [FONTE_CARIOCA, FONTE_CARIOCA_RANK])
          for rival, nr in {"Vasco": 24, "Fluminense": 33, "Botafogo": 21}.items()]


# Novos recortes oficiais. Brasileirão em pontos corridos evita somar 1987
# sem explicar a controvérsia. Mundial distingue Intercontinental/FIFA.
FONTE_BR = "https://www.cbf.com.br/futebol-brasileiro/noticias/campeonato-brasileiro/serie-b/flamengo-e-campeao-do-brasileirao-betano-2025"
FONTE_MUNDIAL = "https://inside.fifa.com/en/news/liverpool-on-top-as-doha-welcomes-the-world"
FONTE_SUPER = "https://www.cbf.com.br/futebol-brasileiro/noticias/competicoes-campeonato-brasileiro-serie-a/a/supercopa-rei-superbet-2026-sera-a-3-final-entre-flamengo-e-corinthians"
FONTE_RECOPA = "https://www.sportingnews.com/br/futebol/noticias/campeoes-recopa-sul-americana-titulos-flamengo/3808d274433b6d6f14c55156"
FONTE_MERCOSUL = "https://arquivodabola.com.br/campeonato/copa-mercosul.html"

BR_CORRIDOS = {"Vasco": 0, "Fluminense": 2, "Botafogo": 1, "São Paulo": 3,
               "Santos": 0, "Grêmio": 0, "Internacional": 0, "Cruzeiro": 3, "Atlético-MG": 1}
SUPER_2025 = {r: int(r in {"Corinthians", "Grêmio", "Palmeiras", "São Paulo", "Atlético-MG"})
              for r in LIBERTADORES if r != "Flamengo"}


def _comparacao(rival, competicao, periodo, nf, nr, fontes, pergunta, resposta):
    e = _outro_campeonato(rival, competicao, periodo, nf, nr, fontes)
    e["falas"][0]["fala"] = pergunta
    e["falas"][2]["fala"] = resposta
    return e


for rival, nr in BR_CORRIDOS.items():
    BANCO.append(_comparacao(rival, "Brasileirão em pontos corridos", "2003 a 2025", 4, nr, [FONTE_BR, "https://www.cnnbrasil.com.br/esportes/brasileirao/brasileirao-por-pontos-corridos-veja-lista-de-todos-os-campeoes/"],
        f"De 2003 a 2025, quem ganhou mais Brasileirões: Flamengo ou {rival}?",
        f"Errou! Em pontos corridos: Flamengo, quatro. {rival}, {EXTENSO[nr]}. Olha o recorte, primo!"))
for rival in ("Vasco", "Fluminense", "Botafogo", "Cruzeiro", "Atlético-MG"):
    BANCO.append(_comparacao(rival, "Mundiais Intercontinental e FIFA", "até 2025", 1, 0, [FONTE_MUNDIAL],
        f"Até 2025, entre Flamengo e {rival}, quem ganhou Mundial Intercontinental ou da FIFA?",
        f"Errou! Flamengo, um: em oitenta e um. {rival}, nenhum nesses torneios. Taça não é palpite!"))
for rival, nr in SUPER_2025.items():
    BANCO.append(_comparacao(rival, "Supercopa do Brasil", "até 2025", 3, nr, [FONTE_SUPER],
        f"Até 2025, quem ganhou mais Supercopas do Brasil: Flamengo ou {rival}?",
        f"Errou! Flamengo, três. {rival}, {EXTENSO[nr]}. Você tá contando a vontade de ganhar!"))
for rival in ("Vasco", "Botafogo"):
    BANCO.append(_comparacao(rival, "Recopa Sul-Americana", "até 2025", 1, 0, [FONTE_RECOPA],
        f"Até 2025, quem ganhou mais Recopas: Flamengo ou {rival}?",
        f"Flamengo, um título. {rival}, nenhum. Errou com uma confiança que até me assustou!"))
for rival in ("Fluminense", "Botafogo", "Corinthians", "São Paulo", "Santos", "Grêmio", "Internacional", "Cruzeiro", "Atlético-MG"):
    BANCO.append(_comparacao(rival, "Copa Mercosul", "1998 a 2001", 1, 0, [FONTE_MERCOSUL],
        f"Na Mercosul, de 1998 a 2001, quem ganhou mais: Flamengo ou {rival}?",
        f"Errou! Flamengo, um. {rival}, nenhum. A competição acabou e teu palpite continua perdido!"))

# Edições e fases individuais não são somadas a totais de Mundial/Libertadores.
# Permitem abordar os demais troféus sem alegar uma superioridade inexistente.
EDICOES = [
    ("Copa Ouro", 1996, "São Paulo", "https://flaestatistica.com.br/titulos/1990"),
    ("Copa dos Campeões", 2001, "São Paulo", "https://www.flamengo.com.br/noticias/novidades/beto-ex-jogador-do-flamengo-e-o-entrevistado-da-radio-fla"),
    ("Torneio Rio-São Paulo", 1961, "Vasco", "https://www.rsssfbrasil.com/miscellaneous/matdecrjsp.htm"),
    ("Taça Guanabara", 2025, "Fluminense", "https://www.flamengo.com.br/noticias/futebol/em-ano-inesquecivel--flamengo-levanta-sete-tacas"),
    ("Taça Rio", 2019, "Vasco", "https://www.flamengo.com.br/flatv/Futebol/free?page=31"),
    ("Derby das Américas", 2025, "Palmeiras", "https://www.flamengo.com.br/noticias/futebol/em-ano-inesquecivel--flamengo-levanta-sete-tacas"),
    ("Copa Challenger", 2025, "Botafogo", "https://www.flamengo.com.br/noticias/futebol/em-ano-inesquecivel--flamengo-levanta-sete-tacas"),
]
for competicao, ano, rival, fonte in EDICOES:
    e = _comparacao(rival, competicao, f"edição de {ano}", 1, 0, [fonte],
        f"Quem ganhou a {competicao} de {ano}: Flamengo ou {rival}?",
        f"Errou! Essa taça é do Flamengo! O {rival} não ganhou essa edição. Vai estudar, primo!")
    e["fato"]["criterio"] = "vencedor desta edição; não total histórico"
    if competicao in {"Derby das Américas", "Copa Challenger"}:
        e["fato"]["nota"] = "troféu de fase da Intercontinental; não é título mundial completo"
    BANCO.append(e)


def escolher_banco(data, usados=()):
    livres = [b for b in BANCO if "primo:" + b["chave"] not in usados] or BANCO
    i = int(hashlib.sha256(str(data).encode()).hexdigest(), 16) % len(livres)
    return livres[i]


# =============================================================================
#  VALIDAÇÃO (vale para o banco e para o que vier da Groq)
# =============================================================================
PROIBIDO = re.compile(r"\b(porra|caralho|merda|puta|viado|macaco|burro|idiota|lixo|vagabund)\w*", re.I)


def validar(falas):
    """Devolve a lista limpa ou levanta ValueError com o motivo."""
    if not isinstance(falas, list) or not (5 <= len(falas) <= 10):
        raise ValueError("esquete precisa de 5 a 10 falas")
    limpas = []
    for f in falas:
        quem = f.get("quem")
        fala = (f.get("fala") or "").strip()
        if quem not in ("rubro", "primo") or not fala:
            raise ValueError(f"fala inválida: {f}")
        if len(fala) > 120:
            raise ValueError(f"fala longa demais ({len(fala)}): {fala}")
        if PROIBIDO.search(fala):
            raise ValueError(f"palavra proibida: {fala}")
        limpas.append(F(quem, fala,
                        f.get("humor") if f.get("humor") in HUMORES else "neutra",
                        f.get("gesto") if f.get("gesto") in GESTOS else "explicar",
                        f.get("reacao") if f.get("reacao") in REACOES else None,
                        f.get("plano") if f.get("plano") in PLANOS else "dupla",
                        (f.get("carimbo") or None) and str(f["carimbo"])[:22].upper(),
                        f.get("efeito") if f.get("efeito") == "confete" else None))
    if len({f["quem"] for f in limpas}) < 2:
        raise ValueError("esquete precisa dos dois personagens")
    if limpas[0]["quem"] != "rubro" or "?" not in limpas[0]["fala"]:
        raise ValueError("Juninho abre com uma pergunta de títulos")
    if limpas[-1]["quem"] != "rubro" or "?" not in limpas[-1]["fala"]:
        raise ValueError("última fala é do Juninho e é pergunta pra Nação")
    if not any(f.get("carimbo") for f in limpas):
        # a virada é a penúltima fala do primo ou do Juninho antes da pergunta
        limpas[-2].update(plano="impacto", carimbo="ZOEIRA")
    return limpas


# =============================================================================
#  CHECAGEM DE FATO (só para o que vem da Groq)
# =============================================================================
# Clube citado fora dos DADOS do dia = invenção provável -> esquete recusada.
CLUBES = ["palmeiras", "corinthians", "são paulo", "sao paulo", "santos", "vasco", "fluminense",
          "botafogo", "grêmio", "gremio", "internacional", "inter ", "atlético", "atletico", "galo",
          "cruzeiro", "bahia", "fortaleza", "ceará", "ceara", "sport", "vitória", "vitoria",
          "bragantino", "juventude", "athletico", "coritiba", "goiás", "goias", "cuiabá", "cuiaba",
          "mirassol", "remo", "paysandu", "chapecoense", "américa", "america-mg", "river", "boca",
          "racing", "estudiantes", "peñarol", "penarol", "nacional", "liverpool", "real madrid",
          "barcelona", "chelsea", "manchester", "psg", "bayern", "benfica", "porto"]
# Palavras com maiúscula que podem aparecer no meio da frase sem ser invenção.
LIVRES = {"Mengão", "Mengo", "Flamengo", "Nação", "Juninho", "Primo", "Sala", "Maracanã",
          "Brasileirão", "Libertadores", "Copa", "Brasil", "Mundial", "Rio", "Zico", "Gávea",
          "Rubro", "Negro", "Rubro-Negro", "Série", "A", "Deus", "Cartola", "Instagram", "VIP", "TV"}
NUMEROS = {"zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "tres": 3, "quatro": 4,
           "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11,
           "doze": 12, "treze": 13, "quatorze": 14, "catorze": 14, "quinze": 15, "dezesseis": 16,
           "dezessete": 17, "dezoito": 18, "dezenove": 19, "vinte": 20, "trinta": 30,
           "quarenta": 40, "cinquenta": 50, "sessenta": 60, "setenta": 70, "oitenta": 80,
           "noventa": 90}
FATO_NUMERICO = re.compile(r"\b([\wçãéêíóôú]+(?:\s+e\s+[\wçãéêíóôú]+)?)\s+(pontos?|gols?|rodadas?|jogos?|"
                           r"vitórias?|derrotas?|empates?|títulos?|lugar|posições?|de vantagem|"
                           r"de diferença|anos?)\b", re.I)


def _numero(expr):
    expr = expr.lower().strip()
    if expr.isdigit():
        return int(expr)
    total, achou = 0, False
    for p in expr.split():
        if p in NUMEROS:
            total += NUMEROS[p]
            achou = True
    return total if achou else None


def checar_fatos(falas, contexto):
    """Recusa (ValueError) clube, nome próprio ou número que não esteja nos DADOS."""
    base = json.dumps(contexto or {}, ensure_ascii=False).lower()
    nums = {int(n) for n in re.findall(r"-?\d+", base)} | {abs(int(n)) for n in re.findall(r"-?\d+", base)}
    for f in falas:
        fala = f["fala"]
        baixa = f" {fala.lower()} "
        for c in CLUBES:
            if re.search(r"\b" + re.escape(c.strip()) + r"\b", baixa) and c.strip() not in base:
                raise ValueError(f"clube fora dos dados ({c.strip()}): {fala}")
        for m in re.finditer(r"[\wÀ-ú-]+", fala):
            w = m.group(0)
            anterior = fala[:m.start()].rstrip()
            inicio_frase = not anterior or anterior.endswith((".", "!", "?", ":", "…", '"'))
            if w[:1].isupper() and not inicio_frase and w not in LIVRES and w.lower() not in base:
                raise ValueError(f"nome próprio fora dos dados ({w}): {fala}")
        for m in FATO_NUMERICO.finditer(fala):
            n = _numero(m.group(1).split()[-1] if " e " not in m.group(1) else m.group(1))
            if n is not None and n > 1 and n not in nums:        # "um gol", "uma vitória" é jeito de falar
                raise ValueError(f"número fora dos dados ({m.group(0)}): {fala}")
    return falas


# =============================================================================
#  GROQ — esquete nova todo dia, com o contexto REAL do dia
# =============================================================================
SISTEMA_ESQUETE = "Juninho pergunta; rival erra; Juninho corrige com títulos verificados e vence a resenha."


def esquete_groq(contexto: dict | None):
    """Comparações de títulos usam exclusivamente o banco conferido.

    A IA livre não consegue garantir a correção da resposta e a vantagem
    do Flamengo; o rodízio com memória mantém a diversidade do banco.
    """
    return None


def cta(data):
    return CTAS[int(hashlib.md5(str(data).encode()).hexdigest(), 16) % len(CTAS)]
