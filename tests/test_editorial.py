import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from src.flamengo import roteiro, quadros, estado, diario, publicar
from src.flamengo.comunidade import contar
from src.flamengo.janela import deve_verificar

class EditorialTests(unittest.TestCase):
    def jogo(self):
        return {'id':'42','data':'2026-09-25','status':'FINISHED','resultado':'vitoria',
                'gols_nossos':2,'gols_deles':1,'em_casa':True,'adversario':'Visitante'}

    def test_sem_jogo_finalizado(self):
        j=self.jogo();j['status']='IN_PROGRESS'
        self.assertIsNone(roteiro.pos_jogo_v2({'jogo':j}))

    def test_estadio_sem_presumir_maracana(self):
        j=self.jogo()
        self.assertEqual(roteiro.local_do_jogo(j),'em casa')
        j['estadio']='Mané Garrincha'
        self.assertIn('Mané Garrincha',roteiro.local_do_jogo(j))

    def test_troca_precisa_ser_proxima_e_mesmo_jogador(self):
        gol=[{'nosso':True,'minuto':"45+2'",'texto':'Gol de Pedro Silva.'}]
        self.assertTrue(roteiro.gol_proximo_da_troca(gol,{'minuto':"50'",'saiu':'Pedro Silva'}))
        self.assertFalse(roteiro.gol_proximo_da_troca(gol,{'minuto':"80'",'saiu':'Pedro Silva'}))
        self.assertFalse(roteiro.gol_proximo_da_troca(gol,{'minuto':"50'",'saiu':'João Silva'}))

    def test_nota_nao_e_avaliacao_esportiva(self):
        p=roteiro.pos_jogo_v2({'jogo':self.jogo(),'cartola':{'jogadores':[{'nome':'A','pontos':2}]}})
        nota=next(b for b in p['batidas'] if b['tipo']=='nota')
        self.assertEqual(nota['dados']['rotulo'],'MAIOR PONTUAÇÃO')
        self.assertNotIn('melhor em campo',nota['fala'])

    def test_votos_sem_texto_livre_e_sem_duplicata(self):
        cs=[{'from':{'id':'1'},'text':'A','timestamp':'1'},
            {'from':{'id':'1'},'text':'B','timestamp':'2'},
            {'from':{'id':'2'},'text':'A e uma frase'},
            {'from':{'id':'3'},'text':' a '}, {'text':'B'}]
        self.assertEqual(contar(cs),{'A':1,'B':1})

    def test_resposta_exige_coleta_completa_e_minimo(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'comunidade.json'
            v={'media_id':'1','total':3,'contagem':{'A':2,'B':1},'completa':False}
            def gravar(): p.write_text(json.dumps({'coletado_em':datetime.now(timezone.utc).isoformat(),'votacoes':[v]}))
            gravar();self.assertIsNone(quadros.resposta({},p))
            v['completa']=True;gravar();self.assertIsNotNone(quadros.resposta({},p))
            self.assertIsNone(quadros.resposta({'respondidas':['1']},p))

    def test_identidade_por_jogo_independe_legenda(self):
        m={'formato':'pos_jogo_v2','jogo_id':'42'}
        self.assertEqual(estado.chave('texto A',m),estado.chave('texto B',m))

    def test_registro_atualiza_sem_duplicar(self):
        with tempfile.TemporaryDirectory() as d, patch.object(estado,'REGISTRO',Path(d)/'estado.json'):
            estado.registrar('texto',{},'gerado')
            estado.registrar('texto',{},'publicado',media_id='1')
            self.assertEqual(len(estado.ler()['itens']),1)
            self.assertEqual(estado.ler()['itens'][0]['status'],'publicado')

    def test_janela_nao_gera_partida_antiga(self):
        now=datetime.now(timezone.utc)
        self.assertFalse(deve_verificar(now,[{'id':'1','utc':(now-timedelta(days=2)).isoformat()}],None))
        self.assertTrue(deve_verificar(now,[{'id':'1','utc':(now-timedelta(hours=2)).isoformat()}],None))
        self.assertFalse(deve_verificar(now,[{'id':'1','utc':(now-timedelta(hours=2)).isoformat()}],'1'))

    def test_quadros_tem_direcao_e_dupla(self):
        p=quadros.dirigir(quadros.primo('teste'))
        self.assertEqual({b['personagem'] for b in p['batidas']},{'rubro','primo'})
        self.assertTrue(all('humor' in b and 'plano' in b for b in p['batidas']))

    def test_diario_sem_dados_tem_humor_original(self):
        with patch.object(diario,'agenda',return_value=([],[])),patch.object(diario,'tabela',return_value=None):
            p,_=diario.montar(datetime.now(timezone.utc),{},'primo_rival')
            self.assertEqual(p['formato'],'primo_rival')

if __name__ == '__main__': unittest.main()
