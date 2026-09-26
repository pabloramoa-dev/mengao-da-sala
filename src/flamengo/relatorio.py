"""Comparações descritivas, sem declarar causalidade ou preencher ausências com zero."""
from collections import defaultdict
from pathlib import Path
import json
import statistics


def resumir(posts):
    grupos=defaultdict(list)
    for p in posts: grupos[p.get('formato','desconhecido')].append(p)
    out={}
    for nome,grupo in grupos.items():
        out[nome]={'n':len(grupo)}
        for m in ('compartilhamentos_por_mil','seguidores_por_mil','ig_reels_avg_watch_time'):
            vals=[p[m] for p in grupo if isinstance(p.get(m),(int,float))]
            out[nome][m]={'n':len(vals),'mediana':statistics.median(vals) if vals else None}
    return out


def main():
    p=Path('data/metricas.json')
    d=json.loads(p.read_text()) if p.exists() else {'posts':[]}
    linhas=['# Experimento editorial — últimos 30 dias','',
            'Comparação descritiva; jogos, horários e assuntos diferentes influenciam o resultado.',
            'Tempo médio assistido: valor em milissegundos conforme a API. Ausência não é zero.',
            '', '| Formato | Posts | Compartilhamentos/1.000 alcançados (mediana) |',
            '|---|---:|---:|']
    for nome,row in resumir(d['posts']).items():
        m=row['compartilhamentos_por_mil']['mediana']
        linhas.append(f'| {nome} | {row["n"]} | {round(m,2) if m is not None else "indisponível"} |')
    linhas += ['', 'Revisão semanal: reunir pelo menos cinco episódios de cada formato antes de comparar; não interpretar isso como teste causal.',
               'Acompanhar duração real, abertura, assunto e rodada. Manter horários estáveis durante a comparação.',
               'Ações de perfil e permissões pendentes: ver docs/OPERACAO_V3.md.']
    Path('docs').mkdir(exist_ok=True)
    Path('docs/RESULTADOS_30_DIAS.md').write_text('\n'.join(linhas)+'\n')

if __name__=='__main__': main()
