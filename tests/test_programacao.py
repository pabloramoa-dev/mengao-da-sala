from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import json
import pytest
from src.flamengo import programacao as p, estado, publicar
from src.flamengo.coletor.pesquisa import validar
from src.flamengo.render import personagens_v4 as personagens, hyperframes_v3 as hf

CFG=json.loads(Path('config/programacao.json').read_text())
def dt(day,hour): return datetime(2026,10,day,hour,tzinfo=p.BRT)
def jogo(day=8,hour=21):
    return dict(id='42',utc=dt(day,hour).isoformat(),horario_confirmado=True,status={'state':'pre'},adversario='Rival',adversario_id='7',fonte='https://example.com',liga='bra.1',competicao='Brasileirão')
def feito(day=8,hour=21):
    return dict(jogo(day,hour),status={'completed':True},gols_nossos=2,gols_deles=1)

def test_pre_somente_vespera_nao_janela_24h():
    j=jogo()
    assert p.selecionar(dt(7,18),[],[j],[],CFG)[0] is None
    assert p.selecionar(dt(7,19),[],[j],[],CFG)[0]=='pre' # 26h antes
    assert p.selecionar(dt(7,23),[],[j],[],CFG)[0]=='pre'
    assert p.selecionar(dt(8,8),[],[j],[],CFG)[0] is None
    assert p.selecionar(dt(8,9),[],[j],[],CFG)[0]=='palpite'

def test_pos_so_dia_seguinte_seis_horas():
    j=feito()
    assert p.selecionar(dt(8,23),[j],[],[],CFG)[0] is None
    assert p.selecionar(dt(9,5),[j],[],[],CFG)[0] is None
    assert p.selecionar(dt(9,6),[j],[],[],CFG)[0]=='pos'
    assert p.selecionar(dt(10,12),[j],[],[],CFG)[0] is None

def test_brt_meianoite_e_utc():
    assert p.selecionar(datetime(2026,10,8,1,tzinfo=timezone.utc),[],[jogo()],[],CFG)[0]=='pre'
    assert p.selecionar(dt(7,19),[],[jogo(8,0)],[],CFG)[0]=='pre'

def test_sem_card_em_dias_reservados_ou_agenda_incompleta():
    assert p.selecionar(dt(7,18),[],[jogo()],[],CFG)[0] is None
    assert p.selecionar(dt(6,19),[],[jogo()],[],CFG)[0]=='tabela'
    with pytest.raises(RuntimeError):p.selecionar(dt(6,19),[],[],[],CFG)
    with patch.object(p.diario,'pegar',side_effect=[{'events':[]},None]),pytest.raises(RuntimeError):p.agenda_segura()

def test_recibo_bloqueia_repeticao_e_preserva_palpite(tmp_path):
    with patch.object(estado,'REGISTRO',tmp_path/'r.json'):
        m=dict(formato='palpite_cida',jogo_id='42',palpite=[2,1],dia='2026-10-08')
        estado.registrar('abc',m,'publicado')
        itens=estado.ler()['itens']
        assert itens[0]['palpite']==[2,1]
        assert p.selecionar(dt(8,9),[],[jogo()],itens,CFG)[0] is None
        assert estado.chave('mudou',m)==estado.chave('abc',m)

def test_pendente_nao_duplica_e_jogo_iniciado_nao_palpite():
    itens=[dict(formato='pre_jogo',jogo_id='42',status='publicacao_pendente')]
    assert p.selecionar(dt(7,19),[],[jogo()],itens,CFG)[0] is None
    j=jogo();j['status']={'state':'in'}
    assert p.selecionar(dt(8,19),[],[j],[],CFG)[0] is None

def test_sobreposicao_pos_pre():
    assert p.selecionar(dt(9,6),[feito()], [jogo(10)],[],CFG)[0]=='pos'
    assert p.selecionar(dt(9,19),[feito()], [jogo(10)],[],CFG)[0]=='pre'

def test_pesquisa_rejeita_evidencia_inventada_e_numero_novo():
    doc=dict(texto='O atleta ainda é dúvida para a próxima partida do Flamengo.',veiculo='Fonte',link='https://example.com',quando='2026-10-05',rumor=True)
    fato=dict(fonte=0,evidencia=doc['texto'],fala='O atleta segue como dúvida para a próxima partida.')
    assert len(validar([fato],[doc]))==1
    assert not validar([dict(fato,fala='O atleta marcou 99 gols na temporada.')],[doc])
    assert not validar([dict(fato,evidencia='Notícia completamente inventada sem fonte.')],[doc])

def test_atores_solo_nomes_e_geometria():
    cena=hf.svg_cena({'solo':'primo','batidas':[{'personagem':'primo','humor':'neutra','gesto':'explicar'}]})
    assert 'DONA CIDA' in cena and 'style="display:none"' in cena
    assert hf.NOMES=={'rubro':'GIL','primo':'DONA CIDA'}
    assert 'GIL' in personagens.gil()

def test_publicador_card_usa_image_url(tmp_path):
    with patch.object(estado,'REGISTRO',tmp_path/'r.json'),patch.object(publicar,'_cfg',return_value=('u','token','https://invalid','mengaodasala')),patch.object(publicar,'_req',side_effect=[{'id':'c'},{'status_code':'FINISHED'},{'id':'m'}]) as req:
        assert publicar.publicar_reel('https://invalid/a.jpg','card',image=True)=='m'
        assert req.call_args_list[0].args[2]['image_url'].endswith('.jpg')
        assert 'media_type' not in req.call_args_list[0].args[2]
