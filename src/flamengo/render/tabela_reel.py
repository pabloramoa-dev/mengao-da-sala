"""Reel vertical de dez segundos com os dados do card e a posição do Flamengo."""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path
from src.flamengo.render.capa import FONTE
from src.flamengo.render import grafico


def renderizar(pauta, destino):
    raiz = FONTE.parents[3]
    linhas = sorted(pauta['classificacao'], key=lambda r: int(r['rank']))
    fla = next(r for r in linhas if str(r['id']) == '819')
    partes = [linhas[i:i+5] for i in range(0, len(linhas), 5)]
    paineis, anim = [], []
    for i, grupo in enumerate(partes):
        inicio, passo = i * 10 / len(partes), 10 / len(partes)
        rows = ''.join(f'<tr class="{"fla" if str(r["id"])=="819" else ""}"><td>{int(r["rank"])}º</td><td>{escape(r["time"])}</td><td>{int(r["points"])}</td><td>{int(r["gamesPlayed"])}</td></tr>' for r in grupo)
        dados = [(f"{r['rank']}º", int(r['points']), str(r['id'])=='819') for r in grupo]
        chart, barras = grafico.barras(f"pontos{i}", dados, max(int(r['points']) for r in linhas))
        anim.append(grafico.animar(barras, inicio))
        paineis.append(f'<section class="clip" data-start="{inicio}" data-duration="{passo}" data-track-index="1" id="grupo{i}"><table><thead><tr><th>POS</th><th>CLUBE</th><th>PTS</th><th>J</th></tr></thead><tbody>{rows}</tbody></table>{chart}</section>')
        anim.append(f'tl.fromTo("#grupo{i} tbody tr",{{x:45,opacity:0}},{{x:0,opacity:1,duration:.25,stagger:.06}},{inicio});')
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        projeto = Path(tmp)
        shutil.copy(FONTE, projeto/'barlow.ttf')
        shutil.copy(raiz/'video/node_modules/gsap/dist/gsap.min.js', projeto/'gsap.js')
        (projeto/'index.html').write_text(f'''<!doctype html><html><head><meta charset="utf-8"><style>
        @font-face{{font-family:Barlow;src:url(barlow.ttf)}}*{{box-sizing:border-box}}body{{margin:0;color:white;font-family:Barlow,sans-serif}}
        #root{{position:relative;width:1080px;height:1920px;background:#16171d;padding:260px 65px}}header,footer{{font-size:44px;color:#ffce72}}h1{{font-size:94px;margin:45px 0 10px}}h2{{background:#b71932;padding:24px;font-size:60px;margin:0}}section{{position:absolute;top:650px;width:950px}}table{{border-collapse:collapse;width:100%;font-size:52px}}td,th{{text-align:left;border-bottom:3px solid #4c4348;padding:14px 9px}}th{{font-size:34px;color:#ffce72}}.fla{{background:#a3122a}}footer{{position:absolute;top:1490px}}
        </style></head><body><div id="root" data-composition-id="tabela" data-width="1080" data-height="1920" data-start="0" data-duration="10" data-fps="30"><header>MENGÃO DA SALA</header><h1>BRASILEIRÃO</h1><h2>FLAMENGO · {int(fla["rank"])}º · {int(fla["points"])} PONTOS</h2>{''.join(paineis)}<footer>Fonte: ESPN · @mengaodasala</footer></div>
        <script src="gsap.js"></script><script>const tl=gsap.timeline({{paused:true}});{''.join(anim)}window.__timelines={{tabela:tl}};</script></body></html>''')
        cli = raiz/'video/node_modules/hyperframes/bin/hyperframes.mjs'
        subprocess.run(['node', str(cli), 'render', tmp, '--output', str(destino.resolve()), '--fps','30','--workers','2','--no-browser-gpu'], check=True, env={**os.environ,'HYPERFRAMES_NO_TELEMETRY':'1'})
    dur = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(destino)]))
    if abs(dur-10) > .1:
        raise ValueError(f'Duração inesperada da tabela: {dur}')
    destino.with_suffix('.txt').write_text(pauta['legenda_post'])
    destino.with_suffix('.json').write_text(json.dumps(dict(pauta,duracao_segundos=dur,midia='reel'),ensure_ascii=False))


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--pauta',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    renderizar(json.loads(args.pauta.read_text()),args.out)
