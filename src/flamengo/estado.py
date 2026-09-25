"""Registro durável por conteúdo; nenhuma credencial é persistida."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
REGISTRO = Path('data/publicacoes.json')


def chave(legenda, meta):
    if meta.get('jogo_id') and meta.get('formato') == 'pos_jogo_v2':
        return 'pos:' + str(meta['jogo_id'])
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
            'jogo_id':meta.get('jogo_id'), 'enquete':meta.get('enquete'),
            'duracao_segundos':meta.get('duracao_segundos'),
            'versao_editorial':meta.get('versao_editorial'), **extra}
    salvar(item)
    return item
