"""Regressões do ciclo de publicação; nenhuma requisição real à Meta."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src.flamengo import publicar, estado


class PublicacaoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.reg = patch.object(estado, 'REGISTRO', Path(self.tmp.name) / 'registro.json')
        self.reg.start(); self.addCleanup(self.reg.stop)
        self.cfg = patch.object(publicar, '_cfg', return_value=('conta', 'token-falso', 'https://invalid', 'mengaodasala'))
        self.cfg.start(); self.addCleanup(self.cfg.stop)
        self.caption = Path(self.tmp.name) / 'reel.txt'
        self.caption.write_text('Legenda de teste')

    def main(self, story=False):
        args = ['publicar', '--video-url', 'https://invalid/midia', '--legenda', str(self.caption)]
        if story: args.append('--story')
        with patch('sys.argv', args), patch.object(publicar, 'verificar_destino', return_value={'username':'mengaodasala'}):
            return publicar.main()

    def test_reel_processa_e_publica_com_registro(self):
        with patch.object(publicar, '_req', side_effect=[{'data':[]}, {'id':'c1'}, {'status_code':'IN_PROGRESS'}, {'status_code':'FINISHED'}, {'id':'m1'}]) as req, patch.object(publicar.time, 'sleep'):
            self.assertEqual(self.main(), 0)
        row = estado.ler()['itens'][0]
        self.assertEqual((row['status'], row['media_id'], row['container_id']), ('publicado','m1','c1'))
        self.assertTrue(req.call_args_list[-1].args[1].endswith('/media_publish'))

    def test_story_publica_imagem(self):
        with patch.object(publicar, '_req', side_effect=[{'id':'c2'}, {'status_code':'FINISHED'}, {'id':'m2'}]) as req:
            self.main(story=True)
        params = req.call_args_list[0].args[2]
        self.assertEqual(params['media_type'], 'STORIES')
        self.assertIn('image_url', params)
        self.assertEqual(estado.ler()['itens'][0]['status'], 'publicado')

    def test_erro_de_processamento_nao_publica(self):
        with patch.object(publicar, '_req', side_effect=[{'data':[]}, {'id':'c'}, {'status_code':'ERROR'}]) as req:
            with self.assertRaisesRegex(RuntimeError, 'container ERROR'): self.main()
        self.assertEqual(estado.ler()['itens'][0]['status'], 'falhou')
        self.assertFalse(any(c.args[1].endswith('/media_publish') for c in req.call_args_list))

    def test_resposta_perdida_na_publicacao_bloqueia_reenvio(self):
        with patch.object(publicar, '_req', side_effect=[{'data':[]}, {'id':'c'}, {'status_code':'FINISHED'}, TimeoutError('resposta perdida')]):
            with self.assertRaises(TimeoutError): self.main()
        self.assertEqual(estado.ler()['itens'][0]['status'], 'publicacao_pendente')
        with patch.object(publicar, '_req', return_value={'data':[]}) as req:
            with self.assertRaisesRegex(RuntimeError, 'inconclusiva'): self.main()
        self.assertEqual(req.call_count, 1)  # somente reconciliação de leitura

    def test_reconcilia_publicacao_ja_existente(self):
        estado.registrar('Legenda de teste', {}, 'publicacao_pendente', container_id='c')
        with patch.object(publicar, '_req', return_value={'data':[{'id':'m','caption':'Legenda de teste'}]}) as req:
            self.main()
        self.assertEqual(req.call_count, 1)
        self.assertEqual(estado.ler()['itens'][0]['media_id'], 'm')
        with patch.object(publicar, '_req') as req:
            self.main()
        req.assert_not_called()

    def test_destino_errado_bloqueado(self):
        with patch.object(publicar, '_req', return_value={'username':'outra_conta'}):
            with self.assertRaisesRegex(RuntimeError, 'DESTINO BLOQUEADO'):
                publicar.verificar_destino()

    def test_timeout_processamento_nao_publica(self):
        with patch.object(publicar, '_req', return_value={'id':'c'}) as req:
            with self.assertRaises(TimeoutError):
                publicar.publicar_reel('https://invalid/video', 'teste', espera_max=0)
        self.assertEqual(req.call_count, 1)

if __name__ == '__main__': unittest.main()
