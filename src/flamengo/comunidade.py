"""Coleta somente votos A/B e métricas. Não publica comentários nem guarda texto pessoal."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter
import json
import re
from src.flamengo.publicar import _cfg, _req, verificar_destino
from src.flamengo.estado import ler

METRICAS = ('views','reach','shares','saved','comments','likes','ig_reels_avg_watch_time','follows')


def contar(comentarios):
    votos = {}
    for c in sorted(comentarios, key=lambda c:c.get('timestamp','')):
        # Allowlist: nenhuma frase livre vira fala de personagem; um voto por autor.
        texto = (c.get('text') or '').strip().upper()
        autor = (c.get('from') or {}).get('id') or c.get('username')
        if autor and re.fullmatch('[AB]', texto): votos[autor] = texto
    return dict(Counter(votos.values()))


def comentarios(media, base, token):
    itens, after = [], None
    for _ in range(20):
        params = {'fields':'text,from,timestamp','limit':100,'access_token':token}
        if after: params['after'] = after
        d = _req('GET', f'{base}/{media}/comments', params)
        itens.extend(d.get('data',[]))
        paging = d.get('paging',{})
        if not paging.get('next'): return itens, True
        after = paging.get('cursors',{}).get('after')
        if not after: return itens, False
    return itens, False


def main():
    verificar_destino()
    user,token,base,_ = _cfg()
    agora = datetime.now(timezone.utc)
    votos, metricas, erros = [], [], []
    posts = ler()['itens']
    conhecidos = {x.get('media_id') for x in posts}
    # Inclui publicações anteriores à adoção do registro, sem inventar formato.
    recentes = _req('GET',f'{base}/{user}/media',{'fields':'id,timestamp,media_product_type','limit':100,'access_token':token})
    posts += [{'status':'publicado','media_id':m['id'],'formato':'anterior_sem_classificacao',
               'atualizado_em':m['timestamp']} for m in recentes.get('data',[]) if m['id'] not in conhecidos and m.get('media_product_type') == 'REELS']
    for post in posts:
        if post['status'] != 'publicado' or not post.get('media_id'): continue
        if agora-datetime.fromisoformat(post['atualizado_em']) > timedelta(days=30): continue
        mid = post['media_id']
        row = {k:post.get(k) for k in ('media_id','formato','duracao_segundos','versao_editorial')}
        for m in METRICAS:
            try:
                d = _req('GET',f'{base}/{mid}/insights',{'metric':m,'access_token':token})
                dados = (d.get('data') or [{}])[0]
                row[m] = ((dados.get('values') or [{}])[0].get('value')
                          if 'values' in dados else (dados.get('total_value') or {}).get('value'))
            except RuntimeError:
                row[m] = None
                erros.append({'media_id':mid,'recurso':m,'motivo':'indisponível ou sem permissão'})
        alcance = row.get('reach')
        row['compartilhamentos_por_mil'] = 1000*row['shares']/alcance if alcance and row.get('shares') is not None else None
        row['seguidores_por_mil'] = 1000*row['follows']/alcance if alcance and row.get('follows') is not None else None
        metricas.append(row)
        if post.get('enquete'):
            try:
                cs, completa = comentarios(mid,base,token)
                contagem = contar(cs)
                votos.append({'media_id':mid,'enquete_id':post['enquete']['id'],
                              'contagem':contagem,'total':sum(contagem.values()),'completa':completa})
            except RuntimeError:
                erros.append({'media_id':mid,'recurso':'comentarios','motivo':'indisponível ou sem permissão'})
    Path('data/comunidade.json').write_text(json.dumps({'coletado_em':agora.isoformat(),'votacoes':votos},ensure_ascii=False,indent=2))
    Path('data/metricas.json').write_text(json.dumps({'coletado_em':agora.isoformat(),'posts':metricas,'indisponiveis':erros},ensure_ascii=False,indent=2))
    print(f'Coleta: {len(metricas)} posts; {len(votos)} votações; {len(erros)} campos indisponíveis.')
    # Ausência de métricas é registrada como null, nunca como zero.

if __name__ == '__main__': main()
