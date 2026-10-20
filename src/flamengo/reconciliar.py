"""Confere recibos pendentes sem impedir a produção de pautas independentes."""
import json
from pathlib import Path
from src.flamengo import estado, publicar


def reconciliar():
    pendentes = [i for i in estado.ler()['itens'] if i.get('status') == 'publicacao_pendente']
    resultado = {'confirmados': 0, 'falhos': 0, 'pendentes': []}
    if not pendentes:
        return resultado
    publicar.verificar_destino()
    _, token, base, _ = publicar._cfg()
    for item in pendentes:
        cid = item.get('container_id')
        if not cid:
            resultado['pendentes'].append({'chave': item['chave'], 'motivo': 'sem_container'})
            continue
        try:
            status = publicar._req('GET', f'{base}/{cid}', {'fields': 'status_code', 'access_token': token}).get('status_code')
        except Exception:
            # Remains pending: a failed GET is never evidence of a failed POST.
            resultado['pendentes'].append({'chave': item['chave'], 'motivo': 'consulta_indisponivel'})
            continue
        if status == 'PUBLISHED':
            item.update(status='publicado', confirmacao='container:PUBLISHED')
            estado.salvar(item)
            resultado['confirmados'] += 1
        elif status in {'ERROR', 'EXPIRED'}:
            item.update(status='falhou', confirmacao='container:' + status)
            estado.salvar(item)
            resultado['falhos'] += 1
        else:
            resultado['pendentes'].append({'chave': item['chave'], 'motivo': status or 'desconhecido'})
    return resultado


def main():
    resultado = reconciliar()
    Path('saida').mkdir(exist_ok=True)
    Path('saida/reconciliacao.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2))
    print(json.dumps(resultado, ensure_ascii=False))
    if resultado['pendentes']:
        print('::warning::Recibos ainda pendentes permanecem bloqueados por conteúdo; outras pautas podem ser produzidas.')


if __name__ == '__main__':
    main()
