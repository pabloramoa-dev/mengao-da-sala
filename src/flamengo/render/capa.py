"""Capa dos Reels, com texto na área central da grade."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONTE = Path(__file__).resolve().parents[3] / 'video/assets/fonts/BarlowCondensed-Bold.ttf'


def criar(pauta, destino):
    imagem = Image.new('RGB', (1080, 1920), '#17171b')
    d = ImageDraw.Draw(imagem)
    for y in (370, 615, 1170, 1415):
        d.rectangle((0, y, 1080, y + 90), fill='#ad1129')
    def linha(texto, y, tamanho, cor):
        fonte = ImageFont.truetype(str(FONTE), tamanho)
        while fonte.getlength(texto) > 940 and tamanho > 16:
            tamanho -= 2
            fonte = ImageFont.truetype(str(FONTE), tamanho)
        d.text((540, y), texto, font=fonte, fill=cor, anchor='mm')
    linhas = pauta['capa'].upper().splitlines()
    if pauta['formato'] in {'pre_jogo','palpite_cida'} and pauta.get('palpite'):
        nos, eles = pauta['palpite']
        linhas = [f'{nos} × {eles}', 'PALPITE']
    if pauta['formato'] == 'tabela_card':
        fla = next(r for r in pauta['classificacao'] if str(r['id']) == '819')
        linhas = [f"{fla['rank']}º LUGAR", 'BRASILEIRÃO']
    linha('MENGÃO DA SALA', 550, 52, '#ffcc66')
    linha(linhas[0], 855, 230, 'white')
    linha(' · '.join(linhas[1:]) or 'FLAMENGO', 1050, 110, '#ffcc66')
    if pauta.get('rival'):
        linha('FLAMENGO × ' + pauta['rival'].upper(), 1320, 65, 'white')
    imagem.save(destino, quality=94)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pauta', type=Path)
    parser.add_argument('destino', type=Path)
    args = parser.parse_args()
    criar(json.loads(args.pauta.read_text()), args.destino)
