"""Verifica pesquisa e palpite com dados públicos, sem voz nem publicação."""
import json
from datetime import datetime, timezone
from pathlib import Path
from src.flamengo import programacao, diario
from src.flamengo.coletor.pesquisa import enriquecer


def main():
    agora=datetime.now(timezone.utc)
    feitos,futuros=programacao.agenda_segura()
    if not futuros:
        print('Sem próxima partida confirmada para diagnóstico.')
        return
    j=futuros[0]
    rivais,_=diario.agenda(j['adversario_id'])
    p=programacao.palpite(j,feitos,rivais,agora)
    p=enriquecer(p,j,agora)
    saida=Path('saida/diagnostico_pesquisa.json')
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(json.dumps(p,ensure_ascii=False,indent=2))
    print(json.dumps({'partida':j['adversario'],'pesquisa':p['pesquisa']['status'],
                      'documentos':p['pesquisa'].get('documentos_lidos',0),
                      'leitores':p['pesquisa'].get('leitores',[]),
                      'palpite':p['analise_palpite']['status'],
                      'amostras':[p['analise_palpite'][t]['jogos'] for t in ('flamengo','adversario')]},ensure_ascii=False))


if __name__=='__main__':main()
