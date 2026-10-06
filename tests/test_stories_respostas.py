from datetime import datetime, timedelta
from src.flamengo import estado, programacao
from src.flamengo.stories_respostas import selecionar, renderizar

def dt(d,h):return datetime(2026,10,d,h,tzinfo=programacao.BRT)
def jogo():return dict(id='42',utc=dt(8,19).isoformat(),adversario='Santos',competicao='Brasileirão',fonte='https://example.com',status={'state':'pre'},horario_confirmado=True)

def test_dia_jogo_dois_stories_depois_nove_e_nunca_apos_inicio():
    j=jogo()
    assert selecionar(dt(8,8),[],[j],[])==[]
    cards=selecionar(dt(8,9),[],[j],[])
    assert len(cards)==2 and cards[0]['slot']!=cards[1]['slot']
    assert '19:00' in cards[0]['contexto'] and 'Santos' in cards[0]['pergunta']
    assert selecionar(dt(8,19),[],[j],[])==[]
    j['status']={'state':'in'}
    assert selecionar(dt(8,18),[],[j],[])==[]

def test_retoma_apenas_story_faltante():
    cards=selecionar(dt(8,10),[],[jogo()],[])
    for status in ('publicado','publicacao_pendente'):
        itens=[dict(chave=estado.chave(cards[0]['legenda'],cards[0]),status=status)]
        assert selecionar(dt(8,10),[],[jogo()],itens)==[cards[1]]

def test_data_local_e_perguntas_rotativas():
    j=jogo();j['utc']=dt(20,19).isoformat()
    a=selecionar(dt(6,12),[],[j],[]);b=selecionar(dt(7,12),[],[j],[])
    assert a[0]['pergunta']!=b[0]['pergunta']
    assert not selecionar(dt(6,11),[],[j],[])
    assert a[0]['dia']=='2026-10-06'

def test_vespera_pos_e_sem_falso_dia_livre():
    assert selecionar(dt(7,12),[],[jogo()],[])[0]['slot']=='vespera'
    j=jogo();j['status']={'completed':True}
    assert selecionar(dt(9,12),[j],[],[])[0]['slot']=='resenha'
    assert not selecionar(dt(8,23),[j],[],[])

def test_jpeg_vertical(tmp_path):
    from PIL import Image
    c=selecionar(dt(8,9),[],[jogo()],[])[0]
    caminho=tmp_path/'story.jpg';renderizar(c,caminho)
    with Image.open(caminho) as im:assert im.size==(1080,1920) and im.format=='JPEG'
