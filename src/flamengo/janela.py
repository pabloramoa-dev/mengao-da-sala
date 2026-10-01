"""Sondagem leve; render/coleta aprofundada apenas quando há partida recente."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import os
from src.flamengo.diario import agenda, FLA, _utc


def deve_verificar(agora, jogos, ultimo):
    return any(j.get('id') != ultimo and timedelta(0) <= agora-_utc(j['utc']) <= timedelta(hours=24) for j in jogos)


def main():
    feitos, futuros = agenda(FLA)
    if not feitos and not futuros:
        raise RuntimeError('Agenda indisponível: não é possível concluir que não há partida. Tentar novamente.')
    if feitos:
        print('Último jogo encerrado na fonte:', feitos[-1]['id'], feitos[-1]['utc'])
    if futuros:
        print('Próximo jogo na fonte:', futuros[0]['id'], futuros[0]['utc'])
    p = Path('data/ultimo_video.json')
    ultimo = json.loads(p.read_text()).get('id') if p.exists() else None
    ativo = deve_verificar(datetime.now(timezone.utc), feitos, ultimo)
    with open(os.environ['GITHUB_OUTPUT'],'a') as f: f.write(f'ativo={str(ativo).lower()}\n')
    print('Partida encerrada recente ainda não registrada:', ativo)
    with open(os.environ.get('GITHUB_STEP_SUMMARY', os.devnull), 'a') as f:
        f.write('- Pós-jogo: ' + ('partida elegível; verificar publicação.\n' if ativo else
                                 'nenhuma partida elegível; geração e publicação não executadas.\n'))

if __name__ == '__main__': main()
