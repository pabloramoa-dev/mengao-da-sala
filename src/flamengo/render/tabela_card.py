"""Card JPEG 1080x1350 com classificação completa e Flamengo em destaque."""
import argparse
import json
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from src.flamengo import diario


def renderizar(p, destino):
    im=Image.new('RGB',(1080,1350),'#10131b');d=ImageDraw.Draw(im)
    def font(n): return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',n)
    def text(x,y,t,n=24,cor='white'): d.text((x,y),str(t),font=font(n),fill=cor)
    text(48,35,'MENGÃO DA SALA',25,'#ffcc66')
    text(48,84,'BRASILEIRÃO',52)
    fla=next(x for x in p['classificacao'] if x['id']==diario.FLA)
    text(48,153,f"FLAMENGO  •  {fla['rank']}º  •  {fla['points']} PONTOS",29,'#ffcc66')
    text(48,212,'POS.   CLUBE',22,'#b2b9c8')
    for x,t in [(685,'PTS'),(785,'J'),(875,'V'),(965,'SG')]: text(x,212,t,22,'#b2b9c8')
    for i,r in enumerate(p['classificacao']):
        y=255+i*46
        d.rounded_rectangle((35,y-3,1045,y+39),radius=9,fill='#c8102e' if r['id']==diario.FLA else ('#202634' if i%2==0 else '#161c27'))
        text(52,y,r['rank']);text(145,y,r['time'][:28])
        for x,k in [(685,'points'),(785,'gamesPlayed'),(875,'wins'),(965,'pointDifferential')]:text(x,y,r[k])
    when=datetime.fromisoformat(p['coletado_em']).astimezone(diario.BRT)
    text(48,1200,f'CONSULTADA EM {when:%d/%m/%Y • %H:%M} BRT',22,'#b2b9c8')
    text(48,1240,'Fonte: ESPN • Jogos a menos importam.',21,'#b2b9c8')
    text(48,1290,'@mengaodasala',22,'#ffcc66')
    destino=Path(destino);destino.parent.mkdir(parents=True,exist_ok=True);im.save(destino,quality=95)
    destino.with_suffix('.txt').write_text(p['legenda_post'])
    destino.with_suffix('.json').write_text(json.dumps(p,ensure_ascii=False))
    return destino

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--pauta',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    renderizar(json.loads(Path(a.pauta).read_text()),a.out)
