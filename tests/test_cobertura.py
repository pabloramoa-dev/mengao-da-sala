from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import json
from pathlib import Path
import pytest
from src.flamengo import cobertura as c, diario, estado, roteiro, dialogos
from src.flamengo.coletor import pos_jogo
from src.flamengo.render import hyperframes as hf

NOW=datetime(2026,10,5,23,tzinfo=timezone.utc)
CFG={'ativado_em':'2026-10-01T07:30:00+00:00','pre_horas':24,'recuperar_pos_dias':7,'tabela_hora_brt':19}


def jogo(id='1', horas=12, liga='bra.1'):
    return {'id':id,'utc':(NOW+timedelta(hours=horas)).isoformat(),'liga':liga,'competicao':'Torneio',
            'horario_confirmado':True,'adversario':'Rival','adversario_id':'2','fonte':'https://www.espn.com/',
            'gols_nossos':2,'gols_deles':1}


def linhas():
    return [{'id':diario.FLA if n==1 else str(n),'time':'Flamengo' if n==1 else f'Time {n}',
             'rank':n,'points':61-n,'gamesPlayed':28,'wins':18,'ties':6,'losses':4,'pointDifferential':30-n}
            for n in range(1,21)]


def test_fila_pre_pos_e_semana_independentes():
    assert c.selecionar(NOW,[jogo(horas=-4)],[jogo('2')],[],CFG)[0]=='pos'
    itens=[{'formato':'pos_jogo_v2','jogo_id':'1','status':'publicado'}]
    assert c.selecionar(NOW,[jogo(horas=-4)],[jogo('2')],itens,CFG)[0]=='pre'
    itens.append({'formato':'pre_jogo','jogo_id':'2','status':'publicado'})
    assert c.selecionar(NOW,[jogo(horas=-4)],[jogo('2')],itens,CFG)[0]=='tabela'
    itens.append({'formato':'tabela_semanal','semana':'2026-W41','status':'publicado'})
    assert c.selecionar(NOW,[jogo(horas=-4)],[jogo('2')],itens,CFG)[0] is None


def test_agenda_vazia_nao_significa_cobertura_completa():
    with pytest.raises(RuntimeError): c.selecionar(NOW,[],[],[],CFG)


def test_nao_publica_partidas_antigas_pre_fora_da_janela_ou_horario_incerto():
    antes=NOW-timedelta(hours=5)
    j=jogo(horas=30)
    assert c.selecionar(antes,[jogo(horas=-200)],[j],[],CFG)[0] is None
    j=jogo(horas=4);j['horario_confirmado']=False
    assert c.selecionar(antes,[jogo(horas=-200)],[j],[],CFG)[0] is None


def test_pendente_bloqueia_reenvio():
    it=[{'formato':'pos_jogo_v2','jogo_id':'1','status':'publicacao_pendente'}]
    assert c.selecionar(NOW,[jogo(horas=-2)],[jogo(horas=100)],it,CFG)[0]=='tabela'


def test_pre_inclui_competicao_horario_e_forma_sem_inventar_escalacao():
    p=c.pre_jogo(jogo(liga='conmebol.recopa'),[jogo(horas=-2)],[],NOW)
    texto=' '.join(b['fala'] for b in p['batidas'])
    assert 'Torneio' in texto and 'uma vitórias' not in texto
    assert 'uma vitória' in texto and 'escalação' not in texto and p['jogo_id']=='1'
    assert p['fontes']


def test_tabela_todas_equipes_no_video_e_legenda():
    p=c.tabela_semanal(linhas(),'2026-W41',NOW)
    grupos=[b['dados']['linhas'] for b in p['batidas'] if b['tipo']=='classificacao']
    assert len(grupos)==4 and sum(map(len,grupos))==20
    assert len(c.legenda(p))<=2200
    assert 'Time 20' in c.legenda(p)


def test_tabela_incompleta_e_outra_temporada_sao_bloqueadas():
    d={'season':{'year':2025}}
    with patch.object(diario,'pegar',return_value=d),pytest.raises(ValueError):c.ler_tabela(NOW)
    d={'season':{'year':2026},'children':[]}
    with patch.object(diario,'pegar',return_value=d),pytest.raises(ValueError):c.ler_tabela(NOW)


def test_deduplicacao_por_jogo_e_semana_independe_texto():
    for meta in ({'formato':'pre_jogo','jogo_id':'1'}, {'formato':'tabela_semanal','semana':'2026-W41'}):
        assert estado.chave('A',meta)==estado.chave('B',meta)
    assert estado.chave('A',{'formato':'pre_jogo','jogo_id':'1'}) != estado.chave('A',{'formato':'pos_jogo_v2','jogo_id':'1'})


def test_agenda_all_recupera_liga_sem_usar_url_privada():
    e={'id':'42','date':NOW.isoformat(),'season':{'displayName':'2026 Recopa'},'competitions':[{
        'status':{'type':{'completed':True}},'competitors':[
            {'team':{'id':'819','displayName':'Flamengo'},'score':{'displayValue':'2','$ref':'http://sports.core.api.espn.pvt/v2/sports/soccer/leagues/conmebol.recopa/events/42/scores'}},
            {'team':{'id':'2','displayName':'Rival'},'score':{'displayValue':'1'}}]}]}
    with patch.object(diario,'pegar',return_value={'events':[e]}) as req:
        feitos,_=diario.agenda('819')
    assert feitos[0]['liga']=='conmebol.recopa'
    assert feitos[0]['competicao']=='Recopa Sul-Americana'
    assert all('/all/teams/819/schedule' in call.args[0] for call in req.call_args_list)


def test_post_empate_em_copa_nao_inventa_ponto_e_estatisticas():
    j={'id':'1','data':NOW.isoformat(),'liga':'conmebol.libertadores','status':'FINISHED','resultado':'empate',
       'gols_nossos':1,'gols_deles':1,'adversario':'Rival','em_casa':True,'estatisticas':{'819':{'totalShots':'12','shotsOnTarget':'4','possessionPct':'61.5'}}}
    p=roteiro.pos_jogo_v2({'jogo':j},{'posicao':1})
    text=' '.join(b['fala'] for b in p['batidas'])
    assert 'Um ponto' not in text and 'doze vezes' in text and 'Quatro foram no gol' in text


def test_penaltis_nao_vira_vitoria_no_tempo_normal():
    d={'header':{'competitions':[{'status':{'type':{'completed':True}},'competitors':[
        {'id':'819','team':{'displayName':'Flamengo'},'score':'0','shootoutScore':'5'},
        {'id':'2','team':{'displayName':'Rival'},'score':'0','shootoutScore':'4'}]}]},'boxscore':{'teams':[]}}
    with patch.object(pos_jogo,'pegar',return_value=(200,d)):
        j=pos_jogo.detalhes({'fla_id':'819','liga':'bra.camp.carioca','id':'1','data':NOW.isoformat()})
    assert j['resultado']=='vitoria' and j['penaltis']=={'nos':5,'eles':4}
    assert 'decisão foi nos pênaltis' in roteiro.pos_jogo_v2({'jogo':j})['batidas'][1]['fala']


def test_renderer_tabela_preserva_vinte_equipes_e_escapa_textos(tmp_path):
    p=c.tabela_semanal(linhas(),'2026-W41',NOW)
    t=0;p['segs']=[]
    for _ in p['batidas']:
        p['segs'].append({'ini':t,'fim_fala':t+4,'fim':t+4.1});t+=4.1
    (tmp_path/'assets').mkdir();(tmp_path/'assets/composition.css').write_text('')
    hf.escrever_composicao(p,tmp_path,Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    txt=(tmp_path/'index.html').read_text()
    assert txt.count('<table class="standings">')==4 and 'Time 20' in txt
    assert txt.count('class="flamengo"')==1


def test_titulos_todos_recortes_favoraveis_e_santos_sem_titulo_desde_2003():
    for e in dialogos.BANCO:
        dialogos.validar(e['falas'])
        assert e['fato']['flamengo']>e['fato']['rival']
    assert dialogos.BR_CORRIDOS['Santos']==0
