"""Fixtures explicitamente fictícias para render, sem rede nem publicação."""
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from src.flamengo import programacao as p, diario

def main():
    out=Path('saida');out.mkdir(exist_ok=True)
    j=dict(id='teste-ficticio',utc=datetime(2026,10,8,21,tzinfo=p.BRT).isoformat(),liga='bra.1',competicao='Brasileirão',
           adversario='Adversário fictício',adversario_id='7',fonte='https://example.com/fixture',horario_confirmado=True,
           status={'state':'pre'},gols_nossos=2,gols_deles=1,em_casa=True,estadio='Estádio de teste')
    final=dict(j,status={'completed':True})
    tabela=[dict(id=diario.FLA if n==3 else str(900+n),time='Flamengo' if n==3 else f'Equipe {n}',rank=n,points=65-n,gamesPlayed=28,wins=18,ties=4,losses=6,pointDifferential=30-n) for n in range(1,21)]
    detalhe=dict(j,status='FINISHED',resultado='vitoria',data=j['utc'],fla_id=diario.FLA)
    with patch.dict('os.environ',{'GROQ_API_KEY':''}),patch.object(p.estado,'ler',return_value={'itens':[]}),patch.object(diario,'agenda',return_value=([],[])),patch.object(diario,'tabela',return_value=None),patch.object(p.pos_jogo,'detalhes',return_value=detalhe),patch.object(p.base,'ler_tabela',return_value=tabela):
        for nome, dia,hora,feitos,futuros in [('pre',7,19,[],[j]),('palpite',8,9,[],[j]),('pos',9,12,[final],[]),('tabela',6,19,[],[j])]:
            with patch.object(p,'agenda_segura',return_value=(feitos,futuros)):
                pauta=p.montar(datetime(2026,10,dia,hora,tzinfo=p.BRT))
            pauta['capa']='TESTE FICTÍCIO • '+pauta['capa']
            (out/f'{nome}_pauta.json').write_text(json.dumps(pauta,ensure_ascii=False,indent=2))

def render_silencioso():
    """Validação visual sem enviar textos a nenhum provedor de voz."""
    import wave
    from src.flamengo.render import hyperframes_v3
    raiz=Path(__file__).resolve().parents[1]
    for nome in ('pre','palpite','pos'):
        pauta=json.loads((raiz/'saida'/f'{nome}_pauta.json').read_text())
        bats=pauta['batidas'][:3]
        segs=[dict(ini=i*2,fim_fala=i*2+1.7,fim=(i+1)*2,quem=b['personagem']) for i,b in enumerate(bats)]
        conteudo=dict(pauta,batidas=bats,segs=segs)
        trab=raiz/'saida'/f'trab_{nome}_visual';trab.mkdir(parents=True,exist_ok=True)
        wav=trab/'silencio.wav'
        with wave.open(str(wav),'w') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(44100);f.writeframes(b'\x00\x00'*44100*6)
        hyperframes_v3.renderizar(conteudo,{'master':wav},raiz/'saida'/f'{nome}_teste.mp4',trab,raiz)

if __name__=='__main__':
    import sys
    main()
    if '--render-silencioso' in sys.argv:render_silencioso()
