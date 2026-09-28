"""Recuperação explícita de Reels já renderizados, com a trava de duplicação normal."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from src.flamengo import diario, estado


def validar(item):
    run = str(item['run_id'])
    tag = str(item['tag'])
    if not run.isdigit() or not re.fullmatch(r'\d{12}', tag):
        raise ValueError('run_id/tag inválidos')
    return run, tag


def main():
    repo = os.environ['GITHUB_REPOSITORY']
    if repo != 'pabloramoa-dev/mengao-da-sala':
        raise RuntimeError('Recuperação restrita ao Mengão da Sala')
    itens = json.loads(Path('config/recuperacao.json').read_text())['itens']
    for item in itens:
        run, tag = validar(item)
        with TemporaryDirectory() as pasta:
            subprocess.run(['gh', 'run', 'download', run, '--repo', repo,
                            '--name', 'reel-diario-' + tag, '--dir', pasta], check=True)
            raiz = Path(pasta)
            legenda = raiz / 'saida' / f'diario_{tag}.txt'
            pauta = raiz / 'data' / 'pauta_diario.json'
            meta = legenda.with_suffix('.json')
            if not all(p.is_file() for p in (legenda, pauta, meta)):
                raise RuntimeError('Artefato incompleto; nenhuma publicação iniciada')
            url = f'https://github.com/{repo}/releases/download/diario-{tag}/REEL.mp4'
            subprocess.run([sys.executable, '-m', 'src.flamengo.publicar',
                            '--video-url', url, '--legenda', str(legenda)], check=True)
            # Somente atualiza o rodízio quando há recibo confirmado.
            k = estado.chave(legenda.read_text().strip(), json.loads(meta.read_text()))
            recibo = next(x for x in estado.ler()['itens'] if x['chave'] == k)
            if recibo['status'] != 'publicado':
                raise RuntimeError('Recibo de publicação ausente')
            diario.registrar(str(pauta))
            if item.get('story'):
                # Reaproveita o card já pronto. Identidade estável em novas tentativas.
                story = raiz / 'story_recuperado.txt'
                story.write_text('Story de recuperação: ' + tag)
                story.with_suffix('.json').write_text(json.dumps({'formato':'story','versao_editorial':3}))
                subprocess.run([sys.executable, '-m', 'src.flamengo.publicar', '--story',
                                '--video-url', f'https://github.com/{repo}/releases/download/diario-{tag}/story_do_dia.png',
                                '--legenda', str(story)], check=True)

if __name__ == '__main__': main()
