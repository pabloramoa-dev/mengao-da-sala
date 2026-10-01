import json
import re
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from src.flamengo import diario, plantao, quadros, roteiro
from src.flamengo.render import hyperframes_v3 as V
from src.flamengo.render import personagens_v3 as P

FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
FIXTURE = Path(__file__).with_name('fixture_noticias.json')
RAIZ = Path(__file__).resolve().parents[1]


class RigTests(unittest.TestCase):
    def test_rig_tem_todas_as_camadas_expressoes_e_bocas(self):
        defs = P.defs()
        for q, fn in (('rubro', P.juninho), ('primo', P.primo)):
            svg = fn()
            for ident in P.ids(q):
                self.assertIn(f'id="{ident}"', svg, ident)
            for e in P.EXPRESSOES:
                self.assertIn(f'id="{q}-exp-{e}"', defs)
                self.assertIn(f'id="{q}-rep-{e}"', defs)
            for f in P.FORMAS_FALA:
                self.assertIn(f'id="{q}-fala-{f}"', defs)
            self.assertIn(f'id="{q}-tampa"', defs)
        self.assertEqual(len(re.findall(r'id="([^"]+)"', defs)), len(set(re.findall(r'id="([^"]+)"', defs))))

    def test_oito_expressoes_minimas_e_cinco_bocas(self):
        self.assertEqual(set(P.EXPRESSOES), {'neutra', 'euforico', 'indignado', 'debochado', 'rindo', 'chocado', 'sofrendo', 'tenso'})
        self.assertEqual(len(P.FORMAS_FALA), 5)
        self.assertTrue(set(P.VISEMA.values()) <= set(P.FORMAS_FALA))

    def test_bocas_seguem_o_audio_sem_repetir_formato(self):
        cues = [{'start': 0, 'end': .2, 'value': 'X'}, {'start': .2, 'end': .4, 'value': 'D'},
                {'start': .4, 'end': .5, 'value': 'D'}, {'start': .5, 'end': .7, 'value': 'F'},
                {'start': 3, 'end': 4, 'value': 'D'}]
        trocas = V.bocas(cues, 0.1, 1.0)
        self.assertEqual([f for _, f in trocas], ['fechada', 'aberta', 'redonda'])
        self.assertTrue(all(.1 <= t <= 1.0 for t, _ in trocas))

    def test_piscar_a_cada_dois_a_cinco_segundos(self):
        for q in ('rubro', 'primo'):
            t = V.piscadas(q, 60)
            gaps = [b - a for a, b in zip(t, t[1:])]
            self.assertTrue(gaps and all(2 <= g <= 5 for g in gaps), gaps)
            self.assertEqual(t, V.piscadas(q, 60))      # determinístico


class ComposicaoTests(unittest.TestCase):
    def conteudo(self):
        b = [roteiro.batida('Gol do Mengão! Virou!', tipo='placar', placar='2 x 1'),
             roteiro.batida('Eu nem vi <script>alert(1)</script>', tipo='reacao')]
        b[0].update(personagem='rubro', humor='euforico', gesto='bracos_cima')
        b[1].update(personagem='primo', humor='sofrendo', gesto='facepalm')
        p = quadros.dirigir({'formato': 'pos_jogo_v2', 'humor': 'euforico', 'capa': 'VIROU <b>', 'batidas': b})
        segs, t = [], 0.0
        for i, _ in enumerate(p['batidas']):
            segs.append({'ini': t, 'fim_fala': t + 1.6, 'fim': t + 1.8})
            t += 1.8
        return dict(p, segs=segs)

    def escrever(self, c):
        d = tempfile.mkdtemp()
        proj = Path(d)
        (proj / 'assets').mkdir()
        (proj / 'assets/composition_v3.css').write_text((RAIZ / 'video/assets/composition_v3.css').read_text())
        cues = [{'start': 0, 'end': .3, 'value': 'D'}, {'start': .3, 'end': .6, 'value': 'B'}]
        return V.escrever_composicao(c, proj, FONT, cues), (proj / 'index.html').read_text()

    @unittest.skipUnless(FONT.is_file(), 'fonte DejaVu ausente')
    def test_composicao_anima_rig_e_marca_versao(self):
        meta, html = self.escrever(self.conteudo())
        self.assertEqual(meta['versao_visual'], 'hyperframes-v3')
        self.assertEqual(meta['personagens'], 'rig-svg-v3')
        self.assertIn('window.__timelines["mengao-v3"]', html)
        self.assertIn('#rubro-fala-aberta', html)            # boca pelo áudio
        self.assertIn('#primo-exp-sofrendo', html)           # expressão de quem fala
        self.assertIn('#tremor', html)                        # tremida no gol
        self.assertIn('#rubro-pisca', html)
        self.assertIn('#rubro-respira', html)
        self.assertIn('2 × 1', html)                          # placar na TV

    @unittest.skipUnless(FONT.is_file(), 'fonte DejaVu ausente')
    def test_texto_externo_e_escapado_e_termina_com_cta(self):
        c = self.conteudo()
        self.assertEqual(c['batidas'][-1]['tipo'], 'cta')
        self.assertIn('flamenguista amigo', c['batidas'][-1]['fala'])
        _, html = self.escrever(c)
        self.assertNotIn('<script>alert', html)
        self.assertNotIn('VIROU <b>', html)

    def test_quem_ouve_reage(self):
        b = dict(roteiro.batida('Primo, viu a tabela?'), personagem='rubro', humor='euforico', gesto='apontar')
        self.assertEqual(V.direcao(b, 'rubro'), ('euforico', 'apontar'))
        self.assertEqual(V.direcao(dict(b, reacao='sofrer'), 'primo'), ('sofrendo', 'facepalm'))


class PlantaoTests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads(FIXTURE.read_text())
        self.agora = datetime.fromisoformat(self.d['coletado_em']) + timedelta(hours=2)

    def gravar(self, dados):
        f = Path(tempfile.mkdtemp()) / 'noticias.json'
        f.write_text(json.dumps(dados, ensure_ascii=False))
        return f

    def test_sem_arquivo_vazio_ou_velho_nao_tem_plantao(self):
        self.assertEqual(plantao.carregar(Path('/nao/existe.json')), [])
        self.assertEqual(plantao.carregar(self.gravar(dict(self.d, pautas=[])), self.agora), [])
        velho = self.agora + timedelta(hours=40)
        self.assertEqual(plantao.carregar(self.gravar(self.d), velho), [])
        self.assertEqual(len(plantao.carregar(self.gravar(self.d), self.agora)), 4)

    def test_recusa_copia_numero_e_nome_inventados(self):
        p = self.d['pautas'][0]
        with self.assertRaises(ValueError):
            plantao.validar_item(p, {'fala': p['titulo'] + '!', 'tv': 'TREINO'})
        with self.assertRaises(ValueError):
            plantao.validar_item(p, {'fala': 'O Mengão treinou fechado e venceu por 3 a 0 o coletivo.', 'tv': 'TREINO'})
        with self.assertRaises(ValueError):
            plantao.validar_item(p, {'fala': 'O Mengão treinou fechado e o Fulano brilhou no coletivo.', 'tv': 'TREINO'})
        ok = plantao.validar_item(p, {'fala': 'O Mengão fechou os portões no último treino antes de sábado!', 'tv': 'treino fechado'})
        self.assertEqual(ok['tv'], 'TREINO FECHADO')

    def test_rumor_e_dito_como_rumor(self):
        p = self.d['pautas'][1]
        t = plantao.validar_item(p, {'fala': 'Uma proposta chega por um meia da base do Mengão.', 'tv': 'PROPOSTA NA BASE'})
        self.assertTrue(t['fala'].startswith('Rumor:'))

    def test_pauta_tem_tres_noticias_fontes_na_legenda_e_cta(self):
        f = self.gravar(dict(self.d, coletado_em=datetime.now(timezone.utc).isoformat()))
        pauta = plantao.gerar(date(2026, 10, 1), f, gerador=lambda _p: self.d['textos_ficticios'])
        self.assertEqual(pauta['formato'], 'plantao_da_sala')
        self.assertEqual(len(pauta['noticias']), 3)
        self.assertEqual(pauta['batidas'][0]['personagem'], 'rubro')
        self.assertIn('primo', {b['personagem'] for b in pauta['batidas']})
        self.assertLessEqual(sum(b['personagem'] == 'primo' for b in pauta['batidas']), 2)
        dirigida = quadros.dirigir(pauta)
        self.assertEqual(dirigida['batidas'][-1]['tipo'], 'cta')
        self.assertEqual(dirigida['duracao_alvo'], [15, 25])
        leg = diario.legenda_post(dirigida)
        self.assertIn('Fontes: Veículo Exemplo A, Veículo Exemplo B', leg)
        self.assertIn('rumor', leg)
        for n in pauta['noticias']:
            self.assertFalse(plantao.copia_do_titulo(n['titulo_original'], n['fala']))

    def test_groq_indisponivel_devolve_none(self):
        f = self.gravar(dict(self.d, coletado_em=datetime.now(timezone.utc).isoformat()))
        self.assertIsNone(plantao.gerar(date(2026, 10, 1), f, gerador=lambda _p: None))
        with patch.dict('os.environ', {}, clear=True):
            self.assertIsNone(plantao._groq(self.d['pautas']))


class RodizioTests(unittest.TestCase):
    def estado(self, hoje, humores):
        hist = [{'data': (hoje - timedelta(days=k + 1)).isoformat(), 'formato': 'o_sofa_nao_aguenta'} for k in range(humores)]
        return {'historico': hist, 'formato': 'conta_do_titulo'}

    def test_humor_no_maximo_duas_vezes_por_semana(self):
        quarta = date(2026, 9, 30)
        self.assertEqual(quarta.weekday(), 2)
        self.assertEqual(diario.vez_do_dia(self.estado(quarta, 0), quarta), 'humor')
        self.assertEqual(diario.vez_do_dia(self.estado(quarta, 2), quarta), 'plantao')
        quinta = date(2026, 10, 1)
        self.assertEqual(diario.vez_do_dia(self.estado(quinta, 0), quinta), 'plantao')

    def montar(self, agora, estado, plantao_ret):
        with patch.object(diario, 'agenda', return_value=([], [])), patch.object(diario, 'tabela', return_value=None), \
                patch.object(quadros, 'resposta', return_value=None), \
                patch.object(plantao, 'gerar', return_value=plantao_ret) as g:
            return diario.montar(agora, estado), g

    def test_plantao_e_padrao_em_dia_sem_jogo(self):
        agora = datetime(2026, 10, 1, 14, 7, tzinfo=timezone.utc)      # quinta
        (pauta, motivo), g = self.montar(agora, {}, {'formato': 'plantao_da_sala', 'batidas': []})
        self.assertEqual(pauta['formato'], 'plantao_da_sala')
        g.assert_called_once()

    def test_sem_noticias_cai_no_rodizio_antigo_sem_humor_acima_do_limite(self):
        agora = datetime(2026, 10, 1, 14, 7, tzinfo=timezone.utc)
        hoje = agora.astimezone(diario.BRT).date()
        (pauta, motivo), _ = self.montar(agora, self.estado(hoje, 2), None)
        self.assertIsNotNone(pauta)
        self.assertNotIn(pauta['formato'], diario.HUMOR_FMT)
        self.assertIn('rodízio', motivo)

    def test_registrar_guarda_historico(self):
        with tempfile.TemporaryDirectory() as d:
            est = Path(d) / 'diario.json'
            pauta = Path(d) / 'pauta.json'
            pauta.write_text(json.dumps({'formato': 'plantao_da_sala', 'episodio': 'plantao:2026-10-01', 'batidas': []}))
            with patch.object(diario, 'ESTADO', est):
                diario.registrar(str(pauta))
            h = json.loads(est.read_text())['historico']
            self.assertEqual(h[-1]['formato'], 'plantao_da_sala')


if __name__ == '__main__':
    unittest.main()
