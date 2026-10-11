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
        ganchos=[f'Amanhã é contra o {rival}. Tá confiante ou tá com o pé atrás?',
                 f'Já tá contando com a vitória contra o {rival}? Calma aí, rapaz.',
                 f'E aí, dá pra ganhar do {rival}? Olha o que eu separei aqui.']
        gancho=ganchos[variante]
        titulo='CONFIANÇA OU PREOCUPAÇÃO?'
        finais=[('Você iria pra cima logo ou começava na calma? Conta aí.', 'ATACAR OU CONTROLAR?', 'comentario'),
                ('Manda pro amigo que vai ver esse jogo contigo.', 'PRÉVIA PARA O GRUPO', 'compartilhar'),
                ('O que tá te deixando com o pé atrás nesse jogo? Fala aí.', 'QUAL É SUA PREOCUPAÇÃO?', 'comentario')]
        noticias=[b for b in corpo if b.get('tipo')=='noticia']
        outros=[b for b in corpo if b.get('tipo')!='noticia']
        corpo=noticias+outros
    elif formato=='palpite_cida':
        n,e=p['palpite']
        insuficiente=p.get('analise_palpite',{}).get('status')=='amostra_insuficiente'
        gancho=(f'Vou de {n} a {e}, no palpite mesmo. E você?' if insuficiente else
                f'Meu palpite é {n} a {e}. Quer saber por quê? Olha só.')
        titulo=f'PALPITE DA CIDA: {n} × {e}'
        # A abertura anterior e os pedidos duplicados são substituídos, não empilhados.
        corpo=[b for b in corpo if not b['fala'].startswith(('Hoje tem Mengão,','Meu palpite é','Amanhã o Gil confere'))]
        corpo.append(batida('É só meu palpite, hein! Amanhã o Gil vem me cobrar.'))
        finais=[('Quanto vai ser? Bota teu placar aí antes do jogo!', 'QUAL É O SEU PLACAR?', 'comentario'),
                ('Manda praquele amigo que nunca concorda comigo.', 'CIDA OU SEU AMIGO?', 'compartilhar'),
                ('Vai no meu palpite ou vai chutar outro? Conta aí.', 'PLACAR + MOTIVO', 'comentario')]
    else:
        # A fala de placar já contém o resultado e, se houver, a disputa de pênaltis.
        placar=next((b for b in corpo if b.get('tipo')=='placar'),None)
        gancho='O jogo acabou. O que você mudaria?' if placar is None else placar['fala']
        if placar is not None:
            corpo.remove(placar)
        titulo='SUA RESENHA DO JOGO'
        retorno=[b for b in corpo if b['fala'].startswith('A Dona Cida palpitou')]
        corpo=retorno+[b for b in corpo if b not in retorno]
        finais=[('Qual lance não sai da tua cabeça? Conta aí.', 'QUAL LANCE MUDOU O JOGO?', 'comentario'),
                ('Manda pra quem viu o jogo contigo. Quero ver se concorda.', 'CONTINUA NO GRUPO', 'compartilhar'),
                ('Quem jogou mais pelo Mengão? Fala o nome aí.', 'SEU DESTAQUE + MOTIVO', 'comentario')]
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
