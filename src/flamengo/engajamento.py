"""Direção editorial dos solos: gancho, informação e uma ação por episódio."""
from copy import deepcopy
from hashlib import sha256
from src.flamengo.roteiro import batida


def aplicar(pauta, jogo):
    p=deepcopy(pauta)
    formato=p['formato']
    if formato not in {'pre_jogo','palpite_cida','pos_jogo_v2'}:
        return p
    if p.get('engajamento',{}).get('versao')==1:
        return p
    variante=int(sha256((str(jogo.get('id'))+formato).encode()).hexdigest(),16)%3
    rival=jogo.get('adversario') or 'o adversário'
    antigas=p['batidas']
    corpo=[b for b in antigas if b.get('tipo') not in {'abre','cta','pergunta'}]
    if formato=='pre_jogo':
        ganchos=[f'Flamengo contra {rival}: confiança ou preocupação?',
                 f'Antes de cravar vitória contra {rival}, olha esse confronto.',
                 f'Como você jogaria contra {rival}? Vamos aos fatos.']
        gancho=ganchos[variante]
        titulo='CONFIANÇA OU PREOCUPAÇÃO?'
        finais=[('Comente: atacar desde o início ou controlar primeiro? E por quê?', 'ATACAR OU CONTROLAR?', 'comentario'),
                ('Manda esta prévia para quem vai assistir ao jogo com você.', 'PRÉVIA PARA O GRUPO', 'compartilhar'),
                ('Qual é sua maior preocupação para esse jogo? Conta nos comentários.', 'QUAL É SUA PREOCUPAÇÃO?', 'comentario')]
        noticias=[b for b in corpo if b.get('tipo')=='noticia']
        outros=[b for b in corpo if b.get('tipo')!='noticia']
        corpo=noticias+outros
    elif formato=='palpite_cida':
        n,e=p['palpite']
        insuficiente=p.get('analise_palpite',{}).get('status')=='amostra_insuficiente'
        gancho=(f'No feeling: {n} a {e}. Você concorda comigo?' if insuficiente else
                f'Meu palpite é {n} a {e}. Vou te contar por quê.')
        titulo=f'PALPITE DA CIDA: {n} × {e}'
        # A abertura anterior e os pedidos duplicados são substituídos, não empilhados.
        corpo=[b for b in corpo if not b['fala'].startswith(('Hoje tem Mengão,','Meu palpite é','Amanhã o Gil confere'))]
        corpo.append(batida('É opinião de torcedora. Amanhã o Gil compara com o resultado.'))
        finais=[('Deixa seu placar nos comentários antes de a bola rolar.', 'QUAL É O SEU PLACAR?', 'comentario'),
                ('Manda para aquele amigo que sempre discorda do meu palpite.', 'CIDA OU SEU AMIGO?', 'compartilhar'),
                ('Concorda comigo? Comenta seu placar e o motivo.', 'PLACAR + MOTIVO', 'comentario')]
    else:
        # A fala de placar já contém o resultado e, se houver, a disputa de pênaltis.
        placar=next((b for b in corpo if b.get('tipo')=='placar'),None)
        gancho='O jogo acabou. O que você mudaria?' if placar is None else placar['fala']
        if placar is not None:
            corpo.remove(placar)
        titulo='SUA RESENHA DO JOGO'
        retorno=[b for b in corpo if b['fala'].startswith('A Dona Cida palpitou')]
        corpo=retorno+[b for b in corpo if b not in retorno]
        finais=[('Qual lance mudou o jogo para você? Conta nos comentários.', 'QUAL LANCE MUDOU O JOGO?', 'comentario'),
                ('Manda esta resenha para quem assistiu ao jogo com você.', 'CONTINUA NO GRUPO', 'compartilhar'),
                ('Quem foi o destaque do Flamengo? Comenta o nome e o motivo.', 'SEU DESTAQUE + MOTIVO', 'comentario')]
    fala,cartao,acao=finais[variante]
    abertura=batida(gancho,tipo='abre',cartao=titulo)
    abertura.update(plano='close',gesto='apontar')
    fim=batida(fala,tipo='cta',cartao=cartao)
    fim.update(plano='close',gesto='perguntar' if acao=='comentario' else 'apontar')
    for i,b in enumerate(corpo):
        b['plano']='close' if b.get('tipo') in {'noticia','placar','mexida'} or i%3==2 else 'aberto'
    p['batidas']=[abertura]+corpo+[fim]
    p['capa']=titulo+'\n'+rival.upper()
    p['engajamento']={'versao':1,'variante':variante,'gancho':gancho,'acao':acao,'cta':fala}
    return p
