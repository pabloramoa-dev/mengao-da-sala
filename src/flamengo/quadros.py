"""Quadros originais: humor ficcional, participação real e direção por batida."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
from src.flamengo.roteiro import batida

ENQUETE = {'id': 'estilo', 'pergunta': 'Para o próximo jogo: atacar desde o início ou controlar primeiro?',
           'opcoes': {'A': 'atacar desde o início', 'B': 'controlar primeiro'}}
HUMOR = [
 ('controle', 'CADÊ O CONTROLE?', [
  'Eu tinha uma missão: assistir ao jogo sentado.',
  'Antes da bola rolar, já perdi o controle remoto e o lugar no sofá.',
  'A escalação está pronta. A sala, nem perto.',
  'Na sua casa, quem comanda o controle?']),
 ('almofada', 'A ALMOFADA FICA', [
  'Ninguém mexe nessa almofada!',
  'Foi desse lado que eu sentei na última vitória.',
  'Análise tática? Hoje a minha é decoração de interiores.',
  'Qual é a sua mania de dia de jogo?']),
 ('calma', 'HOJE EU FICO CALMO', [
  'Hoje eu vou assistir tranquilo.',
  'Essa foi a frase mais otimista que eu falei esta semana.',
  'A bola nem rolou e eu já estou andando pela sala.',
  'Você vê o jogo sentado ou faz caminhada pela casa?']),
 ('replay', 'EU JÁ VI ESSE LANCE', [
  'No replay eu também peço para entrar!',
  'Eu sei o resultado do lance. Meu coração ainda não recebeu o aviso.',
  'Aqui em casa, replay também vale susto.',
  'Quem aí reage ao mesmo lance duas vezes?']),
 ('vizinho', 'O VIZINHO JÁ SABE', [
  'O vizinho nem precisa ligar a televisão.',
  'Pela minha sala, ele sabe se o jogo está bom ou complicado.',
  'Só não confia no meu silêncio. É quando eu estou mais nervoso.',
  'Você é o torcedor silencioso ou o narrador da casa?']),
 ('camisa', 'A CAMISA ESCOLHIDA', [
  'Escolher a camisa demora mais que escolher o jantar.',
  'Esta ganhou clássico. Aquela acompanhou uma virada.',
  'No fim, eu levo duas para o sofá. Vai que precisa de substituição.',
  'Você tem uma camisa preferida para assistir?']),
]
PRIMOS = [
 ('sofa', [('primo','Você chama isso de estádio? É um sofá!'),
           ('rubro','Respeita. Esse sofá já viveu muita decisão.'),
           ('primo','E onde fica a torcida visitante?'),
           ('rubro','Na cadeira. E sem pegar o controle!')]),
 ('calma', [('primo','Você prometeu que ia ficar calmo.'),
            ('rubro','Estou calmo. Só estou aquecendo na sala.'),
            ('primo','Para entrar no segundo tempo?'),
            ('rubro','Para buscar água sem perder o lance!')]),
 ('analista', [('primo','Agora você virou treinador?'),
               ('rubro','Aqui do sofá eu enxergo tudo.'),
               ('primo','Inclusive o controle que você perdeu?'),
               ('rubro','Esse está fazendo marcação individual na almofada.')]),
]


def _index(data, n):
    return int(hashlib.sha256(str(data).encode()).hexdigest(), 16) % n


def sofa(data, usados=()):
    livres = [x for x in HUMOR if 'sofa:' + x[0] not in usados] or HUMOR
    chave, capa, falas = livres[_index(data, len(livres))]
    return {'formato':'o_sofa_nao_aguenta','humor':'debochado','capa':capa,
            'episodio':'sofa:' + chave,
            'batidas':[batida(f, tipo='pergunta' if i == len(falas)-1 else 'reacao') for i,f in enumerate(falas)]}


def primo(data, usados=()):
    livres = [x for x in PRIMOS if 'primo:' + x[0] not in usados] or PRIMOS
    chave, dialogo = livres[_index(data, len(livres))]
    return {'formato':'primo_rival','humor':'debochado','capa':'O PRIMO CHEGOU',
            'episodio':'primo:' + chave,
            'batidas':[dict(batida(f, tipo='reacao'), personagem=p) for p,f in dialogo] + [batida('Quem é esse primo na sua família? Conta aqui!',tipo='pergunta')]}


def nacao_escala():
    b = [batida('Hoje quem escolhe a ideia de jogo é você!', tipo='abre'),
         batida('A: atacar desde o início. B: controlar primeiro.', tipo='reacao', cartao='A: ATACAR\nB: CONTROLAR'),
         batida('Comente A ou B. A sala volta para discutir o resultado.', tipo='pergunta', cartao='A OU B?')]
    return {'formato':'a_nacao_escala','humor':'tenso','capa':'VOCÊ ESCOLHE', 'enquete':ENQUETE, 'batidas':b}


def resposta(estado, caminho=Path('data/comunidade.json')):
    if not caminho.exists(): return None
    d = json.loads(caminho.read_text())
    coleta = datetime.fromisoformat(d['coletado_em'])
    if datetime.now(timezone.utc) - coleta > timedelta(days=3): return None
    for v in d.get('votacoes', []):
        if v['media_id'] in estado.get('respondidas', []) or v['total'] < 3 or not v.get('completa'): continue
        a,b = v['contagem'].get('A',0),v['contagem'].get('B',0)
        resultado = 'A votação ficou empatada.' if a == b else (
            'Entre os votos válidos coletados, venceu ' + ENQUETE['opcoes']['A' if a>b else 'B'] + '.')
        return {'formato':'a_nacao_respondeu','humor':'debochado','capa':'A SALA VOTOU',
                'responde_media_id':v['media_id'],
                'batidas':[batida('Vocês escolheram. Agora vamos à resenha!',tipo='abre'),
                           batida(resultado,tipo='reacao'),
                           batida(f'Foram {a} votos em A e {b} em B.',tipo='reacao',cartao=f'A: {a}  B: {b}'),
                           batida('Qual jogador seria importante para esse jeito de jogar?',tipo='pergunta')]}
    return None


def eu_avisei(jogo, registros):
    anterior = next((x for x in registros if x.get('jogo_id') == jogo.get('id') and x.get('formato') == 'hoje_tem_mengao' and x.get('status') == 'publicado'), None)
    if not anterior: return None
    frase = {'vitoria':'Depois da vitória, até o sofá parece mais confortável.',
             'empate':'Depois do empate, fiquei refazendo o jogo na cabeça.',
             'derrota':'Depois da derrota, respirei fundo. No próximo jogo estou aqui de novo.'}[jogo['resultado']]
    return {'formato':'eu_avisei','humor':'debochado','capa':'ANTES E DEPOIS', 'jogo_id':jogo['id'],
            'episodio':'retorno:' + str(jogo['id']),
            'batidas':[batida('Lembra da nossa chamada antes desse jogo?',tipo='abre'),
                       batida(frase,tipo='reacao'),
                       batida('A sua confiança mudou depois da partida?',tipo='pergunta')]}


def dirigir(pauta):
    p = deepcopy(pauta)
    curto = p['formato'] in {'primo_rival','o_sofa_nao_aguenta','eu_avisei'}
    p['duracao_alvo'] = [12,20] if curto else [35,50] if p['formato'] == 'voce_sabia' else [20,35]
    p['versao_editorial'] = 3
    for i,b in enumerate(p['batidas']):
        b.setdefault('personagem','rubro')
        b.setdefault('humor','tenso' if b['tipo'] == 'pergunta' else p['humor'] if i%2 == 0 else 'debochado')
        b.setdefault('plano','close' if i == 0 or b['tipo'] == 'pergunta' else 'aberto')
        b.setdefault('gesto','perguntar' if b['tipo'] == 'pergunta' else 'explicar')
    # A pergunta exibida precisa ser a mesma que está sendo falada.
    for b in p['batidas']:
        if b['tipo'] == 'pergunta': b['dados'].setdefault('cartao', 'SUA VEZ, NAÇÃO')
    return p
