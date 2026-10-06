from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import json
import pytest
from src.flamengo.coletor import pesquisa as p, leitor
from src.flamengo import estado
from src.flamengo.palpite import calcular

AGORA=datetime(2026,10,6,12,tzinfo=timezone.utc)

def test_extracao_real_remove_menu_e_preserva_data():
    texto='O Flamengo concluiu a preparação para enfrentar o adversário. O treinador orientou o elenco no campo e encerrou a atividade com trabalho de finalização. '
    html='<html><head><title>Preparação do Flamengo</title><meta property="article:published_time" content="2026-10-06T09:00:00-03:00"></head><body><nav>Menu publicidade contato</nav><article><h1>Preparação do Flamengo</h1>'+''.join('<p>'+texto+f' Na etapa {i}, foram realizadas atividades específicas com o grupo.'+'</p>' for i in range(5))+'</article></body></html>'
    d=leitor.extrair(html,'https://www.flamengo.com.br/noticias/treino')
    assert d['leitor']=='trafilatura' and d['data_pagina']=='2026-10-06'
    assert 'Menu publicidade' not in d['texto']

@pytest.mark.parametrize('data',['2025-10-06','2026-10-07',None,'inválido'])
def test_datas_velhas_futuras_ausentes_rejeitadas(data):
    assert not p.recente(data,AGORA)

def test_falha_direta_usa_jina_sem_inventar_data():
    txt='Published Time: 2026-10-06T09:00:00Z\nMarkdown Content:\n'+('Informação da partida. '*30)
    with patch.object(leitor,'url_publica'),patch.object(leitor,'baixar',side_effect=[OSError(),(txt,'https://r.jina.ai/teste')]):
        d=leitor.ler('https://example.com/noticia')
    assert d['leitor']=='jina' and d['data_pagina']=='2026-10-06T09:00:00Z'

def test_feed_novo_nao_valida_artigo_antigo_e_textos_duplicados():
    ns=[dict(titulo='Flamengo contra Rival',tema='jogo',rumor=False,artigos=[dict(link=f'https://example.com/{i}',quando=AGORA.isoformat(),veiculo='Fonte')]) for i in range(3)]
    ds=[dict(texto='texto antigo',data_pagina='2025-10-06',link='a',leitor='trafilatura')]+[dict(texto='mesma reportagem '*40,data_pagina='2026-10-06',link=str(i),leitor='trafilatura') for i in range(2)]
    with patch.object(p,'pautas_partida',return_value=ns),patch.object(p,'ler_materia',side_effect=ds):
        assert len(p.documentos({'adversario':'Rival'},AGORA))==1

def test_memoria_so_publicados_e_persiste_no_recibo(tmp_path):
    f=dict(id='f1',fala='Segundo a fonte, o atleta segue em recuperação.',link='https://example.com',publicado_em=AGORA.isoformat())
    with patch.object(estado,'REGISTRO',tmp_path/'registro.json'):
        m=dict(formato='pre_jogo',jogo_id='1',memoria_editorial=[f],analise_palpite={'status':'ok'})
        estado.registrar('legenda',m,'gerado')
        assert not p.memoria_recente(AGORA+timedelta(minutes=5))
        item=estado.registrar('legenda',m,'publicado')
        item['atualizado_em']=AGORA.isoformat();estado.salvar(item)
        assert p.memoria_recente(AGORA)==[f]
        assert p.repetida(f,p.memoria_recente(AGORA))
        assert not p.memoria_recente(AGORA+timedelta(days=8))

def test_enriquecimento_insere_fato_e_respeita_memoria(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY','teste-local')
    texto='O treinador confirmou o treino nesta manhã antes da partida.'
    doc=dict(texto=texto,rumor=False,quando=AGORA.isoformat(),veiculo='Fonte',link='https://example.com',leitor='trafilatura')
    resposta={'choices':[{'message':{'content':json.dumps({'fatos':[dict(fonte=0,evidencia=texto,fala='O treinador confirmou o treino antes da partida.')]})}}]}
    class Resposta:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self):return json.dumps(resposta).encode()
    def pauta():return dict(formato='pre_jogo',batidas=[{},{}],fontes=[])
    with patch.object(p,'documentos',return_value=[doc]),patch.object(p,'memoria_recente',return_value=[]),patch.object(p.urllib.request,'urlopen',return_value=Resposta()):
        r=p.enriquecer(pauta(),{'adversario':'Rival'},AGORA)
        assert r['pesquisa']['status']=='ok' and len(r['batidas'])==3
    with patch.object(p,'documentos',return_value=[doc]),patch.object(p,'memoria_recente',return_value=r['memoria_editorial']),patch.object(p.urllib.request,'urlopen',return_value=Resposta()):
        assert len(p.enriquecer(pauta(),{},AGORA)['batidas'])==2

def jogos(gf,ga):
    return [dict(id=str(i),utc=(AGORA-timedelta(days=i+1)).isoformat(),status={'completed':True},gols_nossos=gf,gols_deles=ga,em_casa=i%2==0) for i in range(8)]

def test_palpite_reage_a_gols_e_nao_somente_numero_de_vitorias():
    a=calcular({'em_casa':True},jogos(3,0),jogos(1,0),AGORA)
    b=calcular({'em_casa':True},jogos(1,0),jogos(3,0),AGORA)
    assert a['placar'][0]>a['placar'][1]
    assert b['placar'][0]<b['placar'][1]
    assert not a['calibrado']

def test_palpite_nao_usa_futuro_placar_ausente_ou_jogo_incompleto():
    js=jogos(2,1)
    for j in js: j['status']={'completed':False}
    assert calcular({},js,jogos(1,1),AGORA)['placar'] is None
    js=jogos(2,1)
    for j in js:j['utc']=(AGORA+timedelta(days=1)).isoformat()
    assert calcular({},js,jogos(1,1),AGORA)['status']=='amostra_insuficiente'

def test_mando_altera_pesos_e_neutro_nao_tem_vantagem():
    js=jogos(0,0)
    for j in js:j['gols_nossos']=4 if j['em_casa'] else 0
    casa=calcular({'em_casa':True},js,jogos(1,1),AGORA)
    fora=calcular({'em_casa':False},js,jogos(1,1),AGORA)
    assert casa['estimativas'][0]>fora['estimativas'][0]
    a=calcular({'em_casa':True,'campo_neutro':True},js,jogos(1,1),AGORA)
    b=calcular({'em_casa':False,'campo_neutro':True},js,jogos(1,1),AGORA)
    assert a['estimativas']==b['estimativas']
