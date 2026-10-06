"""Palpite editorial transparente. Médias empíricas, sem probabilidades calibradas."""
import math
from datetime import timedelta
from src.flamengo import diario


def amostra(jogos, agora):
    unicos = {}
    for j in jogos:
        try:
            data = diario._utc(j['utc'])
            gf, ga = j.get('gols_nossos'), j.get('gols_deles')
            if not j.get('status', {}).get('completed'):
                continue
            if not agora - timedelta(days=180) <= data < agora:
                continue
            if any(type(g) is not int or g < 0 for g in (gf, ga)):
                continue
            unicos[str(j.get('id') or j['utc'])] = j
        except (KeyError, ValueError, TypeError):
            continue
    return sorted(unicos.values(), key=lambda j: diario._utc(j['utc']))[-8:]


def resumo(jogos, agora, casa):
    js = amostra(jogos, agora)
    # Mesmo mando recebe peso maior; partidas mais recentes também.
    pesos = [(0.85 ** (len(js)-i-1)) * (1.5 if casa is not None and j.get('em_casa') == casa else 1)
             for i, j in enumerate(js)]
    total = sum(pesos)
    return dict(jogos=len(js), vitorias=sum(j['gols_nossos'] > j['gols_deles'] for j in js),
                marcados=sum(j['gols_nossos']*w for j,w in zip(js,pesos))/total if total else None,
                sofridos=sum(j['gols_deles']*w for j,w in zip(js,pesos))/total if total else None,
                ultimo=js[-1]['utc'] if js else None,
                fontes=list(dict.fromkeys(j['fonte'] for j in js if j.get('fonte'))))


def calcular(jogo, feitos, rivais, agora):
    casa = jogo.get('em_casa') if not jogo.get('campo_neutro') else None
    f = resumo(feitos, agora, casa)
    r = resumo(rivais, agora, not casa if casa is not None else None)
    base = dict(metodo='medias_recentes_mando_v1', flamengo=f, adversario=r,
                calibrado=False, fontes=list(dict.fromkeys(f['fontes']+r['fontes'])))
    if min(f['jogos'], r['jogos']) < 3:
        return dict(base, status='amostra_insuficiente', placar=None)
    gols = [(f['marcados']+r['sofridos'])/2, (r['marcados']+f['sofridos'])/2]
    # Arredondamento editorial, não probabilidade de placar exato.
    return dict(base, status='ok', placar=[math.floor(round(g, 6)+0.5) for g in gols],
                estimativas=[round(g, 2) for g in gols])
