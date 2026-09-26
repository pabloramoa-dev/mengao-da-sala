"""Cards para Stories/destaques, com chamada para a votação real no Reel.
Stickers nativos e fixação de destaques precisam do aplicativo Instagram.
"""
from pathlib import Path
import argparse
import json
import textwrap
from PIL import Image, ImageDraw, ImageFont


def cartao(titulo, corpo, caminho, rodape='PARTICIPE NO REEL DO PERFIL'):
    im=Image.new('RGB',(1080,1920),'#111111');d=ImageDraw.Draw(im)
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    def f(n): return ImageFont.truetype(font,n)
    d.rectangle((0,0,1080,24),fill='#C8102E')
    d.text((80,175),'MENGÃO DA SALA',font=f(42),fill='white')
    d.rounded_rectangle((70,390,1010,1430),radius=45,fill='#C8102E')
    y=480
    for linha in textwrap.wrap(titulo.upper(),18):
        d.text((110,y),linha,font=f(68),fill='white');y+=88
    y+=65
    for linha in textwrap.wrap(corpo,29):
        d.text((110,y),linha,font=f(45),fill='white');y+=65
    d.text((80,1530),'@mengaodasala',font=f(45),fill='#E8C468')
    d.multiline_text((80,1640),'\n'.join(textwrap.wrap(rodape,30)),font=f(32),fill='white',spacing=12)
    Path(caminho).parent.mkdir(parents=True,exist_ok=True);im.save(caminho)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pauta');ap.add_argument('--out',default='saida/stories');a=ap.parse_args()
    pasta=Path(a.out);pasta.mkdir(parents=True,exist_ok=True)
    if a.pauta:
        p=json.loads(Path(a.pauta).read_text())
        enquete=p.get('enquete')
        texto=('A: '+enquete['opcoes']['A']+'\nB: '+enquete['opcoes']['B']) if enquete else 'O episódio está no perfil. Qual é a sua opinião? Entre na resenha nos comentários!'
        cartao(p['capa'].replace('\n',' '),texto,pasta/'story_do_dia.png')
        (pasta/'story_do_dia.txt').write_text('Story: '+p['capa']+' — '+__import__('datetime').datetime.now(__import__('datetime').timezone.utc).date().isoformat())
        (pasta/'story_do_dia.json').write_text(json.dumps({'formato':'story','versao_editorial':3}))
    for titulo in ('Comece aqui','Jogos','Resenha','Torcida','História'):
        cartao(titulo,'A sala da Nação rubro-negra.',pasta/(titulo.lower().replace(' ','_')+'.png'), 'PERFIL INDEPENDENTE')

if __name__=='__main__': main()
