"""Fila independente: pré por partida, pós confirmado e tabela por semana.
Dados estruturados da ESPN; fonte, coleta e limitações seguem no conteúdo.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import urllib.request
from src.flamengo import diario, estado, quadros, roteiro
from src.flamengo.coletor import pos_jogo

BRT = diario.BRT
RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / 'config/cobertura.json'


def configuracao():
    return json.loads(CONFIG.read_text())


def publicado(formato, jogo_id=None, semana=None, itens=()):
    return any(x.get('status') in {'publicado', 'publicacao_pendente'} and x.get('formato') == formato
               and (jogo_id is None or str(x.get('jogo_id')) == str(jogo_id))
               and (semana is None or x.get('semana') == semana) for x in itens)


def selecionar(agora, feitos, futuros, itens, cfg):
    """Não mistura diário e cobertura; drena pendências em ordem cronológica."""
    if not feitos and not futuros:
        raise RuntimeError('Agenda indisponível ou vazia; cobertura não pode ser confirmada.')
    marco = datetime.fromisoformat(cfg['ativado_em'])
    # Recibo inconclusivo também bloqueia seleção; precisa de reconciliação.
    for j in feitos:
        if marco <= diario._utc(j['utc']) <= agora and agora-diario._utc(j['utc']) <= timedelta(days=cfg['recuperar_pos_dias']):
            if not publicado('pos_jogo_v2', j['id'], itens=itens):
                return 'pos', j
    for j in futuros:
        delta = diario._utc(j['utc'])-agora
        if j.get('horario_confirmado') and timedelta(0) < delta <= timedelta(hours=cfg['pre_horas']):
            if not publicado('pre_jogo', j['id'], itens=itens):
                return 'pre', j
    local = agora.astimezone(BRT)
    segunda = local.date()-timedelta(days=local.weekday())
    hora = datetime.combine(segunda, datetime.min.time(), BRT)+timedelta(hours=cfg['tabela_hora_brt'])
    ano, sem, _ = local.isocalendar()
    chave = f'{ano}-W{sem:02d}'
    if local >= hora and not publicado('tabela_semanal', semana=chave, itens=itens):
        return 'tabela', {'semana': chave}
    return None, None


def forma(jogos, antes, limite=5):
    js = [j for j in jogos if diario._utc(j['utc']) < antes and j.get('gols_nossos') is not None
          and j.get('gols_deles') is not None][-limite:]
    return {'jogos': len(js), 'vitorias': sum(j['gols_nossos'] > j['gols_deles'] for j in js),
            'empates': sum(j['gols_nossos'] == j['gols_deles'] for j in js),
            'derrotas': sum(j['gols_nossos'] < j['gols_deles'] for j in js)}


def quantidade(n, singular, plural, feminino=False):
    numero = ('uma' if feminino else 'um') if n == 1 else ('duas' if feminino else 'dois') if n == 2 else roteiro.por_extenso(n)
    return numero + ' ' + (singular if n == 1 else plural)


def pre_jogo(j, feitos, rivais, agora, tabela=None):
    data = diario._utc(j['utc']).astimezone(BRT)
    meses = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']
    dia = roteiro.por_extenso(data.day) + ' de ' + meses[data.month-1]
    h = data.hour % 12 or 12
    horario = 'à meia-noite' if data.hour == 0 else 'ao meio-dia' if data.hour == 12 else 'à uma' if h == 1 else 'às ' + roteiro.por_extenso(h)
    horario += ' e meia' if data.minute == 30 else (' e ' + roteiro.por_extenso(data.minute) if data.minute else '')
    if data.hour not in {0,12}: horario += ' da noite' if data.hour >= 18 else ' da tarde' if data.hour >= 12 else ' da manhã'
    artigo = 'pelo' if j['competicao'].startswith(('Brasileirão','Campeonato','Mundial','Torneio','Derby')) else 'pela'
    b = [roteiro.batida('E aí, tá confiante pra esse jogo?', tipo='abre'),
         roteiro.batida(f"O Flamengo pega o {j['adversario']} {artigo} {j['competicao']}, dia {dia}, {horario}.",
                        cartao=f"{j['adversario']} · {data:%d/%m %H:%M} BRT")]
    fase = (j.get('fase') or '').lower().replace('-', '').replace(' ', '')
    rotulo = next((nome for termo,nome in [('quarterfinal','quartas de final'),('semifinal','semifinal'),('roundof16','oitavas de final')] if termo in fase), None)
    if rotulo:
        b.append(roteiro.batida('Agora é '+rotulo+'. Mata-mata, hein? Não dá pra bobear.', cartao=rotulo.upper()))
    if j.get('estadio'):
        estadio = j['estadio']
        local = ('na ' if estadio.lower().startswith('arena') else 'no ') + ('' if estadio.lower().startswith(('estádio','estadio','arena')) else 'estádio ') + estadio
        b.append(roteiro.batida('A bola vai rolar '+local+'.', cartao=estadio))
    for nome, jogos in [('Flamengo', feitos), (j['adversario'], rivais)]:
        f = forma(jogos, agora)
        if f['jogos']:
            b.append(roteiro.batida(f"Peguei os últimos {roteiro.por_extenso(f['jogos'])} jogos do {nome} aqui. Deu "
                     f"{quantidade(f['vitorias'], 'vitória', 'vitórias', True)}, {quantidade(f['empates'], 'empate', 'empates')} e "
                     f"{quantidade(f['derrotas'], 'derrota', 'derrotas', True)}.", cartao=f"{nome}: {f['vitorias']}V {f['empates']}E {f['derrotas']}D"))
    if j['liga'] == 'bra.1' and tabela:
        b.append(roteiro.batida(f"Na tabela que eu tenho aqui, o Mengão tá em {roteiro.ordinal(tabela['posicao'])}, com {roteiro.por_extenso(tabela['pontos'])} pontos.",
                               tipo='tabela', posicao=tabela['posicao'], pontos=tabela['pontos']))
    else:
        b.append(roteiro.batida('Eu quero ver o time indo pra cima, mas sem deixar a defesa aberta. Senão complica.'))
    b.extend([roteiro.batida('Você ia pra cima logo ou começava mais na calma?', tipo='pergunta'),
              roteiro.batida('Segue o Mengão da Sala. Depois do apito final, a resenha volta!', tipo='cta')])
    return {'formato':'pre_jogo', 'jogo_id':j['id'], 'humor':'tenso', 'capa':'ANTES DO APITO\n'+j['adversario'].upper(),
            'batidas':b, 'fontes':[j['fonte']], 'coletado_em':agora.isoformat(), 'competicao':j['competicao']}


def ler_tabela(agora):
    d = diario.pegar(diario.STANDINGS)
    if not d:
        raise RuntimeError('Tabela não disponível; boletim será tentado novamente.')
    temporada = d.get('season', {}).get('year')
    if temporada is None:
        raise ValueError('Fonte não informa o ano da tabela; não publicar como classificação atual.')
    if int(temporada) != agora.astimezone(BRT).year:
        raise ValueError('Tabela pertence a outra temporada; não publicar como atual.')
    linhas=[]
    for grupo in d.get('children') or [d]:
        for e in grupo.get('standings',{}).get('entries',[]):
            stats={s['name']:s.get('value') for s in e.get('stats',[])}
            if 'gamesPlayed' not in stats and 'jogos' in stats: stats['gamesPlayed'] = stats['jogos']
            obrigatorios=['rank','points','gamesPlayed','wins','ties','losses','pointDifferential']
            if any(stats.get(k) is None for k in obrigatorios):
                raise ValueError('Classificação incompleta; não preencher estatísticas com zero.')
            linhas.append({'id':str(e['team']['id']), 'time':diario._curto(e['team']['displayName']),
                           **{k:int(stats[k]) for k in obrigatorios}})
    if len(linhas)!=20 or len({x['id'] for x in linhas})!=20 or {x['rank'] for x in linhas}!=set(range(1,21)):
        raise ValueError('Tabela precisa das 20 equipes e posições únicas.')
    return sorted(linhas,key=lambda x:x['rank'])


def tabela_semanal(linhas, semana, agora):
    fla=next(x for x in linhas if x['id']==diario.FLA)
    lider=linhas[0]
    local=agora.astimezone(BRT)
    b=[roteiro.batida('A tabela não aceita palpite, primo! Vamos ver o Brasileirão inteiro.',tipo='abre'),
       roteiro.batida(f"Na coleta de {local:%d/%m}, o Flamengo é {roteiro.ordinal(fla['rank'])}, com {roteiro.por_extenso(fla['points'])} pontos.",
                     tipo='tabela',posicao=fla['rank'],pontos=fla['points'])]
    diff = abs(lider['points']-fla['points'])
    if fla['rank'] == 1:
        vice=linhas[1];diff=fla['points']-vice['points']
        texto=f"O segundo é {vice['time']}. A diferença é de {roteiro.por_extenso(diff)} pontos."
    else:
        texto=f"O líder é {lider['time']}. A diferença do Flamengo é de {roteiro.por_extenso(diff)} pontos."
    b.append(roteiro.batida(texto))
    for ini in range(0,20,5):
        grupo=linhas[ini:ini+5]
        b.append(roteiro.batida(f"Do {roteiro.ordinal(ini+1)} ao {roteiro.ordinal(ini+5)}: confira pontos, jogos e saldo na tela.",
                               tipo='classificacao',linhas=grupo,cartao=f"{ini+1}º ao {ini+5}º",titulo='TABELA DO BRASILEIRÃO'))
    b.extend([roteiro.batida('Jogos a menos mudam a leitura. Pontos e partidas disputadas estão lado a lado.'),
              roteiro.batida('Quem será o principal adversário do Mengão nesta tabela?',tipo='pergunta'),
              roteiro.batida('Salva a tabela e segue o Mengão da Sala para acompanhar toda semana!',tipo='cta')])
    return {'formato':'tabela_semanal','semana':semana,'humor':'debochado','capa':'BRASILEIRÃO\nA TABELA INTEIRA',
            'batidas':b,'classificacao':linhas,'coletado_em':agora.isoformat(),'fontes':['https://www.espn.com/soccer/standings/_/league/bra.1']}


def legenda(p):
    linhas=[p['capa'].replace('\n',' ·'),'']+[b['fala'] for b in p['batidas']]
    if p.get('classificacao'):
        linhas += ['', 'POS | TIME | PTS | J | V | E | D | SG']
        for r in p['classificacao']:
            linhas.append(f"{r['rank']} | {r['time']} | {r['points']} | {r['gamesPlayed']} | {r['wins']} | {r['ties']} | {r['losses']} | {r['pointDifferential']}")
        # The full classification is already on screen; keep caption within API limit.
        linhas = [p['capa'].replace('\n',' ·'),'Classificação na coleta; jogos adiados podem alterar a comparação.','']+linhas[-21:]
    linhas+=['','Coleta: '+p['coletado_em'],'Fontes: '+ ' '.join(p['fontes']),'Opiniões do personagem são análise de torcedor.','#Flamengo #Mengão #Brasileirão']
    return '\n'.join(linhas)


def montar(agora, cfg=None):
    cfg=cfg or configuracao()
    feitos,futuros=diario.agenda(diario.FLA)
    modo,j=selecionar(agora,feitos,futuros,estado.ler()['itens'],cfg)
    if not modo:return None
    if modo=='pre':
        rivais,_=diario.agenda(j['adversario_id']) if j.get('adversario_id') else ([],[])
        p=pre_jogo(j,feitos,rivais,agora,diario.tabela() if j['liga']=='bra.1' else None)
    elif modo=='tabela':
        p=tabela_semanal(ler_tabela(agora),j['semana'],agora)
    else:
        detalhado=pos_jogo.detalhes({**j,'data':j['utc'],'fla_id':diario.FLA})
        analise={'jogo':detalhado}
        p=roteiro.pos_jogo_v2(analise,diario.tabela() if j['liga']=='bra.1' else None)
        if p is None:raise RuntimeError('Pós-jogo sem placar/status confirmado; tentar novamente.')
        p.update(coletado_em=agora.isoformat(),fontes=[j['fonte']],competicao=j['competicao'])
    p=quadros.dirigir(p)
    p['legenda_post']=legenda(p)
    return p


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
    p=montar(datetime.now(timezone.utc))
    if p is None:
        print('Cobertura: nenhuma publicação nova elegível.');return 3
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(p,ensure_ascii=False,indent=2))
    print('Cobertura selecionada:',p['formato'],p.get('jogo_id') or p.get('semana'))
    return 0

if __name__=='__main__':raise SystemExit(main())
