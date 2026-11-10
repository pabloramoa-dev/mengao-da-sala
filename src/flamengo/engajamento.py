"""Direção editorial dos solos: gancho, informação e uma ação por episódio."""
from copy import deepcopy
from hashlib import sha256
from src.flamengo.roteiro import batida


def aplicar(pauta, jogo):
    p=deepcopy(pauta)
    formato=p['formato']
    if formato not in {'pre_jogo','palpite_cida','pos_jogo_v2'}:
        return p
    if p.get('engajamento',{}).get('versao')==2:
        return p
    variante=int(sha256((str(jogo.get('id'))+formato).encode()).hexdigest(),16)%3
    rival=jogo.get('adversario') or 'o adversário'
    antigas=p['batidas']
    corpo=[b for b in antigas if b.get('tipo') not in {'abre','cta','pergunta'}]
    if formato=='pre_jogo':
        titulo='GANHAR É OBRIGAÇÃO!'
        noticias=[b for b in corpo if b.get('tipo')=='noticia']
        outros=[b for b in corpo if b.get('tipo')!='noticia']
        forma = [b for b in outros if b['fala'].startswith('Peguei os últimos') or b['tipo']=='tabela']
        corpo=(noticias or forma)[:1] or [batida('Pra mim, quando o Flamengo chama o rival pro próprio campo, entrega a iniciativa. Eu prefiro pressionar lá na frente.')]
        gancho=f'Contra o {rival}, eu iria pra cima desde o primeiro minuto. Meu palpite é vitória do Mengão.'
        final=(f'Manda pra quem vai ver Flamengo e {rival} contigo.', 'MANDA PRA QUEM VAI VER', 'compartilhar')
    elif formato=='palpite_cida':
        n,e=p['palpite']
        # Regra editorial fixa: Cida é sempre otimista e nunca prevê empate/derrota.
        if n <= e:
            n = e + 1
            p['palpite'] = [n, e]
        insuficiente=p.get('analise_palpite',{}).get('status')=='amostra_insuficiente'
        gancho=(f'Vou de {n} a {e} pro Flamengo! Comigo é Mengão sempre. E você?' if insuficiente else
                f'Meu palpite é {n} a {e} pro Flamengo! Pode vir quem for!')
        titulo=f'PALPITE DA CIDA: {n} × {e}'
        # A abertura anterior e os pedidos duplicados são substituídos, não empilhados.
        corpo=[b for b in corpo if not b['fala'].startswith(('Hoje tem Mengão,','Meu palpite é','Amanhã o Gil confere'))]
        corpo.append(batida('Aqui é Flamengo, ganhar é obrigação! Depois do apito o Gil confere meu palpite.'))
        final=(f'Manda pra quem já deu palpite contra o {rival}.', 'MANDA PRA QUEM PALPITOU', 'compartilhar')
    else:
        # A fala de placar já contém o resultado e, se houver, a disputa de pênaltis.
        placar=next((b for b in corpo if b.get('tipo')=='placar'),None)
        gancho='O jogo acabou. O que você mudaria?' if placar is None else placar['fala']
        if placar is not None:
            corpo.remove(placar)
        titulo='SUA RESENHA DO JOGO'
        retorno=[b for b in corpo if b['fala'].startswith('A Dona Cida palpitou')]
        destaque = next((b for b in corpo if b.get('tipo') in {'gol','mexida'}), None)
        penaltis = [b for b in corpo if b.get('tipo')=='placar']
        contexto = next((b for b in corpo if b.get('dados',{}).get('cartao')), None)
        corpo = retorno[:1] + penaltis + ([destaque or contexto] if destaque or contexto else [])
        final=(f'Manda pra quem perdeu o jogo contra o {rival}.', 'MANDA PRA QUEM PERDEU O JOGO', 'compartilhar')
    fala,cartao,acao=final
    abertura=batida(gancho,tipo='abre',cartao=titulo)
    if formato == 'pos_jogo_v2' and placar is not None:
        abertura = deepcopy(placar)
        titulo = p.get('capa') or titulo
    abertura.update(plano='close',gesto='apontar')
    fim=batida(fala,tipo='cta',cartao=cartao)
    fim.update(plano='close',gesto='perguntar' if acao=='comentario' else 'apontar')
    for i,b in enumerate(corpo):
        b['plano']='close' if b.get('tipo') in {'noticia','placar','mexida'} or i%3==2 else 'aberto'
    p['batidas']=[abertura]+corpo+[fim]
    p['capa']=titulo if formato=='pos_jogo_v2' else titulo+'\n'+rival.upper()
    p['engajamento']={'versao':2,'variante':variante,'gancho':gancho,'acao':acao,'cta':fala}
    return p
