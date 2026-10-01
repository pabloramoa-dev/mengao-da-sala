import json
import re
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from src.flamengo import gerar, roteiro
from src.flamengo.render import hyperframes as hf

FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')


class HyperFramesTests(unittest.TestCase):
    def conteudo(self):
        return {'formato': 'primo_rival', 'humor': 'euforico', 'capa': 'TESTE DA SALA',
                'batidas': [dict(roteiro.batida('Primo, veio assistir ao jogo?', tipo='reacao'), personagem='rubro'),
                            dict(roteiro.batida('Eu vim pela pipoca. E você?', tipo='pergunta'), personagem='primo')],
                'segs': [{'ini': 0, 'fim_fala': 2, 'fim': 2.12}, {'ini': 2.12, 'fim_fala': 4, 'fim': 4.3}]}

    def test_timing_recusa_fala_fora_do_intervalo_e_sobreposicao(self):
        c = self.conteudo()
        self.assertAlmostEqual(hf.validar_conteudo(c), 5.7)
        c['segs'][1]['ini'] = 1
        with self.assertRaises(ValueError):
            hf.validar_conteudo(c)
        c = self.conteudo()
        c['segs'][1]['fim_fala'] = 8
        with self.assertRaises(ValueError):
            hf.validar_conteudo(c)
        c = self.conteudo()
        c['segs'].pop()
        with self.assertRaises(ValueError):
            hf.validar_conteudo(c)

    def test_paineis_preservam_fatos_e_nao_inventam_estatisticas(self):
        p = {'capa': 'JOGO'}
        placar = hf.painel(p, roteiro.batida('Dois a um.', tipo='placar', placar='2 x 1'), 1)
        self.assertEqual(placar['titulo'], '2 × 1')
        self.assertEqual(placar['efeito'], 'campo')
        nota = hf.painel(p, roteiro.batida('Pontuação no Cartola.', tipo='nota', nota=7.4, nome='José', rotulo='MAIOR PONTUAÇÃO'), 1)
        self.assertEqual(nota['titulo'], 'JOSÉ\n7,4')
        self.assertIn('Cartola', nota['subtitulo'])
        tabela = hf.painel(p, roteiro.batida('Na tabela.', tipo='tabela', posicao=2), 1)
        self.assertEqual(tabela['titulo'], '2º LUGAR')
        self.assertNotIn('PONTOS', tabela['titulo'])
        troca = hf.painel(p, roteiro.batida('Troca.', tipo='mexida', saiu='José', entrou='João', minuto='65'), 1)
        self.assertEqual(troca['titulo'], 'SAI JOSÉ\nENTRA JOÃO')

    def test_legenda_e_texto_externo_sao_escapados_e_cauda_segura_cta(self):
        c = self.conteudo()
        c['capa'] = 'TESTE <img src=x onerror=alert(1)>'
        c['batidas'][1]['fala'] = 'Marca o primo <script>alert(1)</script>!'
        c['batidas'][1]['tipo'] = 'cta'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'assets').mkdir()
            (p / 'assets/composition.css').write_text('')
            m = hf.escrever_composicao(c, p, FONT)
            txt = (p / 'index.html').read_text()
        self.assertNotIn('<script>alert(1)</script>', txt)
        self.assertNotIn('<img src=x', txt)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;!', txt)
        tail_panel = re.search(r'id="panel1"[^>]*data-start="([\d.]+)"[^>]*data-duration="([\d.]+)"', txt)
        self.assertAlmostEqual(sum(float(x) for x in tail_panel.groups()), m['duracao_segundos'])
        self.assertEqual(m['motor'], 'hyperframes')
        self.assertEqual(m['resolucao'], [1080, 1920])

    def test_motor_padrao_cobre_solo_e_dupla_sem_exigir_nova_fala(self):
        for b in [[roteiro.batida('Um torcedor no sofá.', tipo='reacao')], self.conteudo()['batidas']]:
            pauta = dict(formato='o_sofa_nao_aguenta', humor='euforico', capa='SALA', batidas=b)
            with tempfile.TemporaryDirectory() as d, patch.dict('os.environ', {}, clear=True), patch.object(gerar, 'gerar_v3', return_value=Path(d)/'video.mp4') as render:
                gerar.gerar({'pauta': pauta}, 'diario', Path(d)/'video.mp4')
                dirigido = render.call_args.args[0]
                # as falas da pauta ficam intactas; a direção só acrescenta o CTA final do canal
                self.assertEqual([x['fala'] for x in dirigido['batidas']][:len(b)], [x['fala'] for x in b])
                self.assertEqual(dirigido['batidas'][-1]['tipo'], 'cta')

    def test_motor_anterior_continua_acessivel_para_recuperacao(self):
        pauta = dict(formato='o_sofa_nao_aguenta', humor='euforico', capa='SALA',
                     batidas=[roteiro.batida('Um torcedor no sofá.', tipo='reacao')])
        with tempfile.TemporaryDirectory() as d, patch.dict('os.environ', {'FLAMENGO_MOTOR': 'dupla'}, clear=True), \
                patch.object(gerar, 'gerar_hyperframes', return_value=Path(d)/'video.mp4') as antigo, \
                patch.object(gerar, 'gerar_v3') as novo:
            gerar.gerar({'pauta': pauta}, 'diario', Path(d)/'video.mp4')
            antigo.assert_called_once()
            novo.assert_not_called()

    def test_placar_nao_confirmado_continua_bloqueado_antes_do_render(self):
        analise = {'jogo': {'status': 'IN_PROGRESS', 'resultado': None}}
        with patch.object(gerar, 'gerar_hyperframes') as render, patch.object(gerar, 'gerar_v3') as render_v3:
            self.assertIsNone(gerar.gerar({'analise': analise}, 'pos_jogo_v2', Path('x.mp4')))
            render_v3.assert_not_called()
            render.assert_not_called()

    def test_video_sem_audio_ou_com_duracao_errada_nao_passa_para_publicacao(self):
        base = {'streams': [{'codec_type': 'video', 'width': 1080, 'height': 1920, 'avg_frame_rate': '30/1'}], 'format': {'duration': '5.7'}}
        with patch.object(hf.subprocess, 'run') as run:
            run.return_value.stdout = json.dumps(base)
            with self.assertRaises(RuntimeError):
                hf.conferir_video(Path('video.mp4'), 5.7)
            base['streams'].append({'codec_type': 'audio'})
            base['format']['duration'] = '3'
            run.return_value.stdout = json.dumps(base)
            with self.assertRaises(RuntimeError):
                hf.conferir_video(Path('video.mp4'), 5.7)


if __name__ == '__main__':
    unittest.main()
