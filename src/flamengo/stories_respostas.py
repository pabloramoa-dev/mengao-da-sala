"""Stories diários com perguntas por resposta; sem stickers ou coleta de DMs."""
import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from src.flamengo import diario, estado, programacao, publicar

PERGUNTAS = [
    ('memoria', 'MEMÓRIA RUBRO-NEGRA', 'Qual jogo do Flamengo você gostaria de reviver?'),
    ('camisa', 'O MANTO DA TORCIDA', 'Qual camisa do Flamengo é a sua favorita?'),
    ('idolo', 'ÍDOLO DA NAÇÃO', 'Qual jogador fez você se apaixonar pelo Flamengo?'),
    ('ritual', 'SEU DIA DE JOGO', 'Qual é a sua superstição para assistir ao Mengão?'),
    ('companhia', 'RESENHA DA TORCIDA', 'Com quem você mais gosta de assistir ao Flamengo?'),
    ('estadio', 'NA ARQUIBANCADA', 'Qual foi seu primeiro jogo do Flamengo no estádio?'),
    ('emocao', 'GOL INESQUECÍVEL', 'Qual gol do Flamengo fez você gritar mais alto?'),
]


def selecionar(agora, feitos, futuros, itens):
    local=agora.astimezone(programacao.BRT)
    hoje=local.date()
    if not feitos and not futuros:
        raise RuntimeError('Agenda indisponível: não assumir dia livre.')
    dia=lambda j: diario._utc(j['utc']).astimezone(programacao.BRT).date()
    jogos=[j for j in futuros if dia(j)==hoje]
    cards=[]
    if jogos:
        for j in jogos:
            if not j.get('horario_confirmado') or j.get('status',{}).get('state')!='pre' or diario._utc(j['utc'])<=agora:
                continue
            if local.hour<9:continue
            horario=diario._utc(j['utc']).astimezone(programacao.BRT)
            confronto = f"{j['adversario']} × Flamengo" if j.get("em_casa") is False else f"Flamengo × {j['adversario']}"
            contexto=f"HOJE · {horario:%H:%M} BRT\n{confronto}\n{j['competicao']}"
            for slot,titulo,pergunta in [
                ('vencedor','QUEM LEVA ESSA?',f"Flamengo, empate ou {j['adversario']}? Quem você acha que vence?"),
                ('placar','SEU PALPITE VALE A RESENHA','Qual vai ser o placar? Escreva os gols do Flamengo primeiro.')]:
                cards.append(dict(slot=slot+':'+str(j['id']),titulo=titulo,pergunta=pergunta,contexto=contexto,
                                  jogo_id=j['id'],jogo_utc=j['utc'],fontes=[j['fonte']]))
    elif any(dia(j)==hoje for j in feitos):
        return [] # Não soltar pergunta de dia livre após partida encerrada hoje.
    elif local.hour>=12:
        amanha=next((j for j in futuros if dia(j)==hoje+timedelta(days=1)),None)
        ontem=next((j for j in reversed(feitos) if dia(j)==hoje-timedelta(days=1)),None)
        if amanha and amanha.get('horario_confirmado'):
            h=diario._utc(amanha['utc']).astimezone(programacao.BRT)
            slot,titulo,pergunta='vespera','AMANHÃ TEM MENGÃO',f"Contra {amanha['adversario']}, você está confiante ou preocupado? Por quê?"
            contexto=f"AMANHÃ · {h:%H:%M} BRT\n{amanha['competicao']}"
        elif ontem:
            slot,titulo,pergunta='resenha','A RESENHA CONTINUA','Quem foi o destaque do Flamengo? Responda com o nome e o motivo.'
            contexto=f"Depois de Flamengo × {ontem['adversario']}"
        else:
            slot,titulo,pergunta=PERGUNTAS[hoje.toordinal()%len(PERGUNTAS)]
            contexto='HOJE QUEM FALA É A TORCIDA'
        cards=[dict(slot=slot,titulo=titulo,pergunta=pergunta,contexto=contexto)]
    saida=[]
    for c in cards:
        c.update(formato='story_resposta',dia=hoje.isoformat(),versao_editorial=5,
                 coletado_em=agora.isoformat(),interacao='resposta_ao_story')
        c['legenda']=f"Story {c['dia']} {c['slot']}: {c['pergunta']}"
        chave=estado.chave(c['legenda'],c)
        if not any(x.get('chave')==chave and x.get('status') in {'publicado','publicacao_pendente'} for x in itens):
            saida.append(c)
    return saida


def renderizar(c, caminho):
    from PIL import Image, ImageDraw, ImageFont
    im=Image.new('RGB',(1080,1920),'#11141c');d=ImageDraw.Draw(im)
    fonte='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    def f(n):return ImageFont.truetype(fonte,n)
    d.polygon([(680,0),(1080,0),(1080,1920),(920,1920)],fill='#4e1324')
    d.rectangle((65,230,150,241),fill='#ed2043')
    d.text((65,165),'MENGÃO DA SALA',font=f(40),fill='white')
    def bloco(texto,y,largura,tamanho,cor,max_altura):
        for n in range(tamanho,23,-2):
            linhas=[]
            for par in texto.splitlines():
                linha=''
                for palavra in par.split():
                    teste=(linha+' '+palavra).strip()
                    if d.textlength(teste,font=f(n))>largura and linha:
                        linhas.append(linha);linha=palavra
                    else:linha=teste
                linhas.append(linha)
            if len(linhas)*(n+15)<=max_altura:break
        for linha in linhas:
            d.text((80,y),linha,font=f(n),fill=cor);y+=n+15
        return y
    bloco(c['contexto'],320,890,39,'#e9bf65',240)
    bloco(c['titulo'],650,900,64,'white',220)
    d.rounded_rectangle((55,920,1025,1400),radius=36,fill='#c51034')
    bloco(c['pergunta'],970,900,57,'white',380)
    d.text((80,1500),'RESPONDA A ESTE STORY',font=f(38),fill='#e9bf65')
    d.text((80,1570),'Participe da resenha.',font=f(31),fill='white')
    d.text((80,1650),'@mengaodasala',font=f(32),fill='#adb5c7')
    Path(caminho).parent.mkdir(parents=True,exist_ok=True)
    im.save(caminho,format='JPEG',quality=92)


def executar(ensaio=False):
    agora=datetime.now(timezone.utc)
    feitos,futuros=programacao.agenda_segura()
    cards=selecionar(agora,feitos,futuros,estado.ler()['itens'])
    pasta=Path('saida/stories_respostas');pasta.mkdir(parents=True,exist_ok=True)
    for i,c in enumerate(cards):
        nome=f'story_{i}'
        imagem=pasta/(nome+'.jpg');texto=pasta/(nome+'.txt')
        renderizar(c,imagem)
        texto.write_text(c['legenda'])
        texto.with_suffix('.json').write_text(json.dumps(c,ensure_ascii=False,indent=2))
        if ensaio:continue
        # Reconsultar imediatamente antes de enviar: adiado, iniciado, virada do dia.
        f,u=programacao.agenda_segura()
        atuais=selecionar(datetime.now(timezone.utc),f,u,estado.ler()['itens'])
        atual=next((a for a in atuais if a['dia']==c['dia'] and a['slot']==c['slot']),None)
        if not atual or any(atual.get(k)!=c.get(k) for k in ('jogo_utc','contexto','pergunta')):
            raise RuntimeError('Agenda do Story mudou; gerar novamente na próxima execução.')
        publicar.verificar_destino()
        tag=f"stories-{os.environ['GITHUB_RUN_ID']}-{os.environ.get('GITHUB_RUN_ATTEMPT','1')}-{i}"
        subprocess.run(['gh','release','create',tag,str(imagem),'--title',tag,'--notes','Pergunta da torcida nos Stories'],check=True)
        url=f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/releases/download/{tag}/{imagem.name}"
        subprocess.run(['python','-m','src.flamengo.publicar','--story','--video-url',url,'--legenda',str(texto)],check=True)
    print(f'Stories preparados: {len(cards)}; ensaio={ensaio}')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--ensaio',action='store_true');a=ap.parse_args()
    executar(a.ensaio)
