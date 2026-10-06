from src.flamengo.engajamento import aplicar
from src.flamengo.roteiro import batida
from src.flamengo.quadros import dirigir


def test_pre_preserva_noticia_e_fonte_e_tem_uma_acao():
    p=dict(formato='pre_jogo',humor='tenso',fontes=['fonte'],batidas=[batida('Olá',tipo='abre'),batida('Horário confirmado.'),batida('Segundo a fonte, o atleta é dúvida.',tipo='noticia'),batida('Pergunta velha?',tipo='pergunta'),batida('Siga e compartilhe!',tipo='cta')])
    r=dirigir(aplicar(p,{'id':'1','adversario':'Santos'}))
    assert r['batidas'][1]['fala']=='Segundo a fonte, o atleta é dúvida.'
    assert r['fontes']==['fonte']
    assert sum(b['tipo']=='cta' for b in r['batidas'])==1
    assert p['batidas'][0]['fala']=='Olá'
    assert aplicar(r,{'id':'1','adversario':'Santos'})==r


def test_cida_revela_palpite_sem_duplicar_nem_apagar_incerteza():
    p=dict(formato='palpite_cida',palpite=[1,1],analise_palpite={'status':'amostra_insuficiente'},batidas=[batida('Hoje tem Mengão, e eu já tenho meu palpite!'),batida('Hoje a amostra está curta.'),batida('Meu palpite é 1 a 1. É opinião!'),batida('Amanhã o Gil confere se eu acertei.')])
    r=aplicar(p,{'id':'1','adversario':'Santos'})
    texto=' '.join(b['fala'] for b in r['batidas'])
    assert texto.count('1 a 1')==1 and 'feeling' in texto and 'amostra está curta' in texto


def test_pos_preserva_penaltis_e_comparacao_da_cida():
    p=dict(formato='pos_jogo_v2',batidas=[batida('Abertura',tipo='abre'),batida('Ficou 1 a 1. A decisão foi nos pênaltis.',tipo='placar'),batida('Pênaltis: 4 a 3.',tipo='placar'),batida('A Dona Cida palpitou 2 a 1. Não acertou.')])
    r=aplicar(p,{'id':'2','adversario':'Santos'})
    assert 'pênaltis' in r['batidas'][0]['fala']
    assert r['batidas'][1]['fala'].startswith('A Dona Cida')
    assert any('4 a 3' in b['fala'] for b in r['batidas'])
