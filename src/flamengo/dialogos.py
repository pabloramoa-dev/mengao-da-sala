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

Fonte das falas, em ordem: Groq (com dados REAIS do dia no prompt, validada
aqui) -> banco escrito à mão (abaixo). Sem chave ou resposta inválida, o banco
segura o dia sem ninguém perceber.
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


# =============================================================================
#  BANCO — esquetes atemporais (não citam placar, tabela nem jogador)
# =============================================================================
BANCO = [
    dict(chave="sofa_estadio", capa="O PRIMO\nCHEGOU", falas=[
        F("primo", "Você chama isso de estádio? É um sofá com televisão, primo.", "debochado", "ombros", "revirar"),
        F("rubro", "Respeita! Esse sofá já viu mais título que o teu time inteiro.", "indignado", "apontar", "choque", "close"),
        F("primo", "E essa almofada rubro-negra aí? É o setor VIP?", "debochado", "apontar", "cruzar"),
        F("rubro", "É a arquibancada! E ela tem regra: secador senta no chão.", "euforico", "explicar", "revirar"),
        F("primo", "No chão? Eu sou visita!", "chocado", "peito", "rir"),
        F("rubro", "Visita que seca vira mobília. Pega ali o controle, mobília.", "rindo", "apontar", "sofrer",
          "impacto", carimbo="VIROU MÓVEL"),
        F("rubro", "E na tua casa, quem é o secador do sofá? Marca ele aqui!", "debochado", "contar", "celular", "close"),
    ]),
    dict(chave="calma", capa="HOJE EU\nFICO CALMO", falas=[
        F("primo", "Você prometeu pra tua mãe que hoje ia ver o jogo calmo.", "debochado", "celular", "sim"),
        F("rubro", "E eu tô calmíssimo. Olha a minha respiração: ahhh.", "tenso", "maos_juntas", "revirar", "close"),
        F("primo", "Primo, a bola nem rolou e você já roeu a unha do pé.", "rindo", "apontar", "sofrer"),
        F("rubro", "É técnica de concentração! O Mengão sente a energia da sala.", "indignado", "peito", "rir"),
        F("primo", "Então manda uma energia pra zaga, que ela tá precisando.", "debochado", "ombros", "choque",
          "impacto", carimbo="SECOU!"),
        F("rubro", "Sai da minha sala! Com calma. Mas sai!", "indignado", "apontar", "rir", "close"),
        F("rubro", "Você vê o jogo sentado ou vira treinador em pé na sala? Conta aí!", "euforico", "explicar", "celular"),
    ]),
    dict(chave="treinador", capa="O TÉCNICO\nDO SOFÁ", falas=[
        F("primo", "Olha ele! Virou treinador de novo. Já pediu três substituições.", "debochado", "contar", "orgulho"),
        F("rubro", "Daqui do sofá eu enxergo o jogo todo. O técnico só enxerga o gramado!", "euforico", "explicar", "revirar"),
        F("primo", "E o controle remoto? Você enxerga onde ele tá?", "rindo", "apontar", "choque"),
        F("rubro", "O controle tá fazendo marcação individual na almofada.", "tenso", "maos_juntas", "rir", "close"),
        F("primo", "Pois é, a única marcação que funcionou hoje.", "debochado", "cruzar", "sofrer",
          "impacto", carimbo="TOMOU"),
        F("rubro", "Primo, você tá a um comentário de assistir no celular. Lá fora.", "indignado", "apontar", "celular"),
        F("rubro", "E você, Nação, qual substituição faria hoje? Escreve aqui embaixo!", "neutra", "contar", "sim", "close"),
    ]),
    dict(chave="camisa", capa="A CAMISA\nDA SORTE", falas=[
        F("primo", "Por que você tá vestindo duas camisas uma em cima da outra?", "chocado", "apontar", "orgulho"),
        F("rubro", "Uma é a da sorte. A outra é reserva, caso a primeira canse.", "euforico", "peito", "revirar", "close"),
        F("primo", "Camisa não cansa, primo. Quem cansa é quem convive contigo.", "debochado", "ombros", "choque"),
        F("rubro", "Ri agora. Na última vez que eu tirei ela, a gente levou gol.", "tenso", "explicar", "rir"),
        F("primo", "Então tira as duas que eu quero ver.", "rindo", "celular", "sofrer", "impacto", carimbo="SECADOR"),
        F("rubro", "Nunca! Essa camisa só sai daqui depois do título.", "euforico", "bracos_cima", "revirar", efeito="confete"),
        F("rubro", "Qual é a tua mania de dia de jogo? Conta que eu não julgo!", "debochado", "contar", "celular", "close"),
    ]),
    dict(chave="vizinho", capa="O VIZINHO\nJÁ SABE", falas=[
        F("primo", "Teu vizinho bateu aqui perguntando se tá tudo bem.", "debochado", "celular", "choque"),
        F("rubro", "Tá tudo ótimo! Eu só gritei um pouquinho no lance.", "neutra", "ombros", "revirar"),
        F("primo", "Um pouquinho? O alarme do carro dele disparou!", "chocado", "bracos_cima", "rir", "close"),
        F("rubro", "Isso é o alarme torcendo junto. Até o carro é Mengão!", "euforico", "peito", "sofrer"),
        F("primo", "O carro dele é do meu time, primo.", "debochado", "cruzar", "choque",
          "impacto", carimbo="ALARME SECADOR"),
        F("rubro", "Então é por isso que ele apita toda vez que o Mengão ataca.", "rindo", "apontar", "sofrer"),
        F("rubro", "Na tua rua, quem é o vizinho que sabe o placar pelo teu grito? Comenta!", "euforico", "explicar", "sim", "close"),
    ]),
    dict(chave="resenha_zap", capa="O GRUPO\nDA FAMÍLIA", falas=[
        F("primo", "Já mandei no grupo da família: hoje o Mengão tropeça.", "debochado", "celular", "choque"),
        F("rubro", "Você manda isso toda semana. Toda semana você apaga depois.", "indignado", "apontar", "sofrer", "close"),
        F("primo", "Eu não apago. Eu só arquivo a conversa.", "tenso", "maos_juntas", "rir"),
        F("rubro", "Arquiva e sai do grupo por três dias. A tia até perguntou se você viajou.", "rindo", "contar", "sofrer"),
        F("primo", "Eu fui fazer um retiro espiritual.", "sofrendo", "peito", "rir",
          "impacto", carimbo="RETIRO DO SECADOR"),
        F("rubro", "Retiro não, primo. É o esconderijo de todo domingo.", "euforico", "ombros", "revirar"),
        F("rubro", "Tem um primo desses no teu grupo? Marca ele aqui, sem dó!", "debochado", "contar", "celular", "close"),
    ]),
    dict(chave="pipoca", capa="A PIPOCA\nPÉ-QUENTE", falas=[
        F("primo", "Posso pegar um pouco da pipoca?", "neutra", "apontar", "nao"),
        F("rubro", "Não! Essa pipoca é pé-quente. Cada milho estourado é um gol.", "indignado", "explicar", "revirar", "close"),
        F("primo", "Então me dá umas duas, que eu quero ver você sofrer.", "debochado", "celular", "choque"),
        F("rubro", "Pipoca de secador estoura pra dentro. Deus me livre.", "chocado", "maos_juntas", "rir"),
        F("primo", "Primo, você precisa de ajuda.", "rindo", "ombros", "orgulho"),
        F("rubro", "Ajuda eu tenho. Chama Nação. São quarenta milhões!", "euforico", "bracos_cima", "revirar",
          "impacto", carimbo="QUARENTA MILHÕES", efeito="confete"),
        F("rubro", "Qual comida não pode faltar no teu dia de jogo? Conta aí!", "neutra", "contar", "sim", "close"),
    ]),
    dict(chave="replay", capa="EU JÁ VI\nESSE LANCE", falas=[
        F("primo", "Você tá gritando no replay, primo. O lance já acabou.", "debochado", "apontar", "nao"),
        F("rubro", "O lance acabou. O meu coração ainda não recebeu o aviso!", "tenso", "peito", "revirar", "close"),
        F("primo", "E se no replay a bola não entrar?", "debochado", "ombros", "choque"),
        F("rubro", "Aí a gente vê de novo, até entrar!", "euforico", "bracos_cima", "rir", efeito="confete"),
        F("primo", "Isso não é torcida. É teimosia.", "chocado", "cruzar", "orgulho"),
        F("rubro", "Teimosia é o teu time chegar no fim do ano achando que tem chance.", "rindo", "apontar", "sofrer",
          "impacto", carimbo="PEGOU PESADO"),
        F("rubro", "Você também comemora o gol no replay? Confessa aqui embaixo!", "euforico", "explicar", "celular", "close"),
    ]),
]


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
    if limpas[0]["quem"] != "primo":
        raise ValueError("gancho é do primo (é ele que chega provocando)")
    if limpas[-1]["quem"] != "rubro" or "?" not in limpas[-1]["fala"]:
        raise ValueError("última fala é do Juninho e é pergunta pra Nação")
    if not any(f.get("carimbo") for f in limpas):
        # a virada é a penúltima fala do primo ou do Juninho antes da pergunta
        limpas[-2].update(plano="impacto", carimbo="ZOEIRA")
    return limpas


# =============================================================================
#  GROQ — esquete nova todo dia, com o contexto REAL do dia
# =============================================================================
SISTEMA_ESQUETE = """Você escreve esquetes curtas de humor para o Instagram @mengaodasala.
Personagens (ficção, desenho animado):
- JUNINHO (quem="rubro"): flamenguista apaixonado, dono da sala, exagerado, bom de resposta,
  fala gíria carioca leve ("Nação", "Mengão", "segue o líder", "primo").
- PRIMO SECADOR (quem="primo"): primo que visita só pra secar o Flamengo. Irônico, contido,
  vive no celular. NUNCA diz qual é o time dele.
Regras obrigatórias:
- 6 a 8 falas. A 1ª é do primo e já provoca. Cada resposta sobe o tom. Uma VIRADA engraçada
  perto do fim (marque "plano":"impacto" e um "carimbo" de até 3 palavras).
- A última fala é do Juninho e é uma PERGUNTA para a torcida comentar.
- Cada fala com no máximo 110 caracteres, frases faladas, naturais, sem hashtag e sem emoji.
- Só use fatos que estão em DADOS. Não invente placar, jogador, lesão, contratação nem polêmica.
  Se DADOS vier vazio, faça humor atemporal de sala (sofá, controle, mania, família, vizinho).
- Zoeira leve de futebol. Proibido palavrão, ofensa pessoal, preconceito, violência, política.
- Números por extenso na fala (ex.: "três pontos").
Responda SÓ JSON: {"capa":"TÍTULO CURTO EM 2 LINHAS COM \\n","falas":[{"quem":"primo|rubro",
"fala":"...","humor":"...","gesto":"...","reacao":"...","plano":"dupla|close|impacto",
"carimbo":"... ou null","efeito":"confete ou null"}]}
humor: neutra euforico indignado tenso debochado rindo chocado sofrendo
gesto: repouso explicar apontar bracos_cima facepalm ombros cruzar peito celular maos_juntas contar
reacao (o que o outro faz ouvindo): revirar rir nao sim cruzar celular choque sofrer orgulho"""


def esquete_groq(contexto: dict | None):
    chave = os.environ.get("GROQ_API_KEY")
    if not chave or os.environ.get("FLAMENGO_DIALOGO_IA", "1") == "0":
        return None
    try:
        from src.flamengo.coletor.pos_jogo import GROQ_URL, escolher_modelo, pegar
        modelo = escolher_modelo(chave)
        if not modelo:
            return None
        corpo = {"model": modelo, "temperature": 0.9, "max_tokens": 1800,
                 "response_format": {"type": "json_object"},
                 "messages": [{"role": "system", "content": SISTEMA_ESQUETE},
                              {"role": "user", "content": "DADOS:\n" + json.dumps(contexto or {}, ensure_ascii=False)[:4000]}]}
        if modelo.startswith("openai/gpt-oss"):
            corpo["reasoning_effort"] = "low"
        cod, resp = pegar(GROQ_URL, dados=json.dumps(corpo).encode("utf-8"),
                          cab={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"})
        bruto = json.loads(resp["choices"][0]["message"]["content"])
        falas = validar(bruto.get("falas"))
        capa = str(bruto.get("capa") or "O PRIMO\nCHEGOU").upper()[:28]
        print(f"[esquete] Groq ({modelo}): {len(falas)} falas")
        return dict(chave="ia", capa=capa, falas=falas)
    except Exception as exc:                     # qualquer falha -> banco
        print(f"[esquete] Groq recusada, usando o banco: {exc}")
        return None


def cta(data):
    return CTAS[int(hashlib.md5(str(data).encode()).hexdigest(), 16) % len(CTAS)]
