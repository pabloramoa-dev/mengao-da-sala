"""Sondagem leve; render/coleta aprofundada apenas quando há partida recente."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import os
from src.flamengo.diario import agenda, FLA, _utc


def deve_verificar(agora, jogos, ultimo):
    return any(j.get('id') != ultimo and timedelta(0) <= agora-_utc(j['utc']) <= timedelta(hours=8) for j in jogos)


def main():
    feitos, futuros = agenda(FLA)
    p = Path('data/ultimo_video.json')
    ultimo = json.loads(p.read_text()).get('id') if p.exists() else None
    ativo = deve_verificar(datetime.now(timezone.utc), feitos, ultimo)
    with open(os.environ['GITHUB_OUTPUT'],'a') as f: f.write(f'ativo={str(ativo).lower()}\n')
    print('Partida encerrada recente ainda não registrada:', ativo)

if __name__ == '__main__': main()
