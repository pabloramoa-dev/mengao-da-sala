"""Registro durável por conteúdo; nenhuma credencial é persistida."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
REGISTRO = Path('data/publicacoes.json')


def chave(legenda, meta):
    if meta.get('formato') == 'story_resposta':
        return 'story-resposta:' + str(meta['dia']) + ':' + str(meta['slot'])
    if meta.get('formato') == 'palpite_cida' and meta.get('jogo_id'):
        return 'palpite:' + str(meta['jogo_id'])
    if meta.get('formato') == 'tabela_card' and meta.get('dia'):
        return 'card:' + meta['dia']
    if meta.get('jogo_id') and meta.get('formato') in {'pos_jogo_v2', 'pre_jogo'}:
        return ('pos:' if meta['formato'] == 'pos_jogo_v2' else 'pre:') + str(meta['jogo_id'])
    if meta.get('formato') == 'tabela_semanal' and meta.get('semana'):
        return 'tabela:' + meta['semana']
    return hashlib.sha256(' '.join(legenda.split()).casefold().encode()).hexdigest()[:24]


def ler():
    return json.loads(REGISTRO.read_text()) if REGISTRO.exists() else {'itens':[]}


def salvar(item):
    d = ler()
    d['itens'] = [x for x in d['itens'] if x['chave'] != item['chave']] + [item]
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRO.with_suffix('.tmp')
    tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2))
    tmp.replace(REGISTRO)


def registrar(legenda, meta, status, **extra):
    k = chave(legenda, meta)
    antigo = next((x for x in ler()['itens'] if x['chave'] == k), {})
    item = {**antigo, 'chave':k, 'formato':meta.get('formato'), 'status':status,
            'atualizado_em':datetime.now(timezone.utc).isoformat(),
            'memoria_editorial':meta.get('memoria_editorial', antigo.get('memoria_editorial', [])),
            'analise_palpite':meta.get('analise_palpite', antigo.get('analise_palpite')),
            'slot':meta.get('slot'), 'interacao':meta.get('interacao'),
            'dia':meta.get('dia'), 'palpite':meta.get('palpite'), 'jogo_utc':meta.get('jogo_utc'),
            'jogo_id':meta.get('jogo_id'), 'enquete':meta.get('enquete'),
            'semana':meta.get('semana'), 'coletado_em':meta.get('coletado_em'),
            'duracao_segundos':meta.get('duracao_segundos'),
            'engajamento':meta.get('engajamento', antigo.get('engajamento')),
            'versao_editorial':meta.get('versao_editorial'), **extra}
    salvar(item)
    return item
