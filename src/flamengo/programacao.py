"""Calendário editorial Gil/Cida. Datas civis de São Paulo, recibos por partida."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import argparse
import json
from pathlib import Path
from src.flamengo import cobertura as base, diario, estado, roteiro, quadros
from src.flamengo.coletor import pos_jogo
from src.flamengo.palpite import calcular

BRT = ZoneInfo('America/Sao_Paulo')
FORMATOS = {'pre': 'pre_jogo', 'palpite': 'palpite_cida', 'pos': 'pos_jogo_v2', 'tabela': 'tabela_card'}


def agenda_segura():
    """As duas respostas são obrigatórias: falha parcial não significa dia livre."""
    feitos, futuros = {}, {}
    for extra in ('', '?fixture=true'):
        dados=diario.pegar(f'{diario.ESPN}/all/teams/{diario.FLA}/schedule{extra}')
        if not dados or 'events' not in dados:
            raise RuntimeError('Agenda parcial indisponível; suspender seleção.')
        for evento in dados['events']:
            j=diario._jogo(evento,'all',diario.FLA)
            st=j['status']
            if st.get('completed'):feitos[j['id']]=j
            elif st.get('state') in {'pre','in'} and st.get('name') not in {'STATUS_POSTPONED','STATUS_CANCELED','STATUS_CANCELLED'}:
                futuros[j['id']]=j
    for ident in feitos:futuros.pop(ident,None)
    return sorted(feitos.values(),key=lambda j:j['utc']),sorted(futuros.values(),key=lambda j:j['utc'])


def selecionar(agora, feitos, futuros, itens, cfg):
    if not feitos and not futuros:
        raise RuntimeError('Agenda indisponível; não assumir dia sem jogo.')
    local = agora.astimezone(BRT)
    hoje = local.date()
    reservada = False
    # Pré e palpite são urgentes; pós vem depois se houver coincidência.
    candidatos = []
    for j in futuros:
        data = diario._utc(j['utc']).astimezone(BRT).date()
        if data in {hoje, hoje + timedelta(days=1)}:
            reservada = True
        if not j.get('horario_confirmado') or j.get('status',{}).get('state') == 'in':
            continue
        if data == hoje + timedelta(days=1):
            candidatos.append(('pre', j, cfg['pre_hora_brt']))
        elif data == hoje and diario._utc(j['utc']) > agora:
            candidatos.append(('palpite', j, cfg['palpite_hora_brt']))
    for j in feitos:
        data = diario._utc(j['utc']).astimezone(BRT).date()
        if data in {hoje, hoje - timedelta(days=1)}:
            reservada = True
        if data == hoje - timedelta(days=1) and j.get('status', {}).get('completed'):
            candidatos.append(('pos', j, cfg['pos_hora_brt']))
    for modo, j, hora in candidatos:
        if local.hour >= hora and not base.publicado(FORMATOS[modo], j['id'], itens=itens):
            return modo, j
    if not reservada and local.hour >= cfg['tabela_hora_brt']:
        if not any(i.get('formato') == 'tabela_card' and i.get('dia') == hoje.isoformat()
                   and i.get('status') in {'publicado', 'publicacao_pendente'} for i in itens):
            return 'tabela', {'dia': hoje.isoformat()}
    return None, None


def palpite(j, feitos, rivais, agora):
    f = base.forma(feitos, agora)
    r = base.forma(rivais, agora)
    analise = calcular(j, feitos, rivais, agora)
    placar = analise['placar'] or [1, 1]
    local = diario._utc(j['utc']).astimezone(BRT)
    horario = roteiro.por_extenso(local.hour) + (' hora' if local.hour == 1 else ' horas')
    if local.minute:
        horario += ' e ' + roteiro.por_extenso(local.minute)
    falas = ['Hoje tem Mengão, e eu já tenho meu palpite!',
             f"Hoje o Flamengo pega o {j['adversario']}, às {horario}. É jogo de {j['competicao']}."]
    if f['jogos']:
        falas.append(f"Olha os últimos {f['jogos']} jogos que eu tenho aqui: o Flamengo ganhou {f['vitorias']}.")
    if r['jogos']:
        falas.append(f"Já o {j['adversario']} ganhou {r['vitorias']} dos últimos {r['jogos']} que eu vi na lista.")
    if analise['status'] == 'ok':
        falas.append('Eu olhei quem anda fazendo gol, quem anda levando e quem joga em casa.')
        ultimo_f = analise['flamengo']['ultimo']
        ultimo_r = analise['adversario']['ultimo']
        descanso_f = (diario._utc(j['utc'])-diario._utc(ultimo_f)).days
        descanso_r = (diario._utc(j['utc'])-diario._utc(ultimo_r)).days
        if 0 <= descanso_f <= 14 and 0 <= descanso_r <= 14 and descanso_f != descanso_r:
            falas.append(f'Pela lista aqui, o Flamengo vem de {descanso_f} dias sem jogar. O outro lado, de {descanso_r}.')
    else:
        falas.append('Tenho poucos jogos aqui pra comparar. Hoje eu vou no meu palpite mesmo!')
    falas += [f"Meu palpite é {placar[0]} a {placar[1]}. É meu palpite, viu? Não é certeza!",
              'Amanhã o Gil confere se eu acertei. E você, qual placar arrisca?']
    return dict(formato='palpite_cida', jogo_id=j['id'], humor='debochado',
                capa='O PALPITE DA CIDA', palpite=placar, analise_palpite=analise, batidas=[roteiro.batida(f) for f in falas],
                fontes=[j['fonte']], coletado_em=agora.isoformat(), competicao=j['competicao'])


def montar(agora, cfg=None):
    cfg = cfg or json.loads(Path('config/programacao.json').read_text())
    feitos, futuros = agenda_segura()
    itens = estado.ler()['itens']
    modo, j = selecionar(agora + timedelta(minutes=30), feitos, futuros, itens, cfg)
    if not modo:
        return None
    hora = cfg[{'pre':'pre_hora_brt','palpite':'palpite_hora_brt','pos':'pos_hora_brt','tabela':'tabela_hora_brt'}[modo]]
    publicar_em = agora.astimezone(BRT).replace(hour=hora,minute=0,second=0,microsecond=0).isoformat()
    if modo == 'tabela':
        linhas = base.ler_tabela(agora)
        fla = next(x for x in linhas if x['id'] == diario.FLA)
        p = dict(formato='tabela_card', dia=j['dia'], classificacao=linhas, capa='FLAMENGO NO BRASILEIRÃO',
                 fontes=['https://www.espn.com/soccer/standings/_/league/bra.1'], coletado_em=agora.isoformat(),
                 batidas=[], humor='neutra', versao_editorial=5)
        p['legenda_post'] = (f"Flamengo: {fla['rank']}º, {fla['points']} pontos em {fla['gamesPlayed']} jogos.\n"
                              f"Tabela consultada em {agora.astimezone(BRT):%d/%m/%Y às %H:%M}.\n"
                              'Jogos a menos podem mudar a comparação. Salve para acompanhar!\nFonte: '+p['fontes'][0])
        p['publicar_em'] = publicar_em
        return p
    if modo in {'pre', 'palpite'}:
        rivais, _ = diario.agenda(j['adversario_id']) if j.get('adversario_id') else ([], [])
        p = palpite(j, feitos, rivais, agora) if modo == 'palpite' else base.pre_jogo(j, feitos, rivais, agora, diario.tabela() if j['liga']=='bra.1' else None)
        if modo == 'pre':
            p['capa'] = 'AMANHÃ TEM MENGÃO\n' + j['adversario'].upper()
            p['batidas'][0] = roteiro.batida('Amanhã tem Mengão! E aí, tá confiante?', tipo='abre')
    else:
        detalhado = pos_jogo.detalhes({**j, 'data':j['utc'], 'fla_id':diario.FLA})
        p = roteiro.pos_jogo_v2({'jogo':detalhado}, diario.tabela() if j['liga']=='bra.1' else None)
        if not p:
            raise RuntimeError('Pós-jogo sem resultado encerrado confirmado.')
        p.update(fontes=[j['fonte']], coletado_em=agora.isoformat(), competicao=j['competicao'])
        anterior = next((i for i in itens if str(i.get('jogo_id'))==str(j['id']) and i.get('formato')=='palpite_cida' and i.get('status')=='publicado' and i.get('palpite')), None)
        if anterior:
            n, e = anterior['palpite']
            certo = [n,e] == [j['gols_nossos'],j['gols_deles']]
            p['batidas'].insert(2, roteiro.batida(f"A Dona Cida palpitou {n} a {e}. " + ('Acertou o placar!' if certo else 'Errou dessa vez! Amanhã ela vai dizer que foi por pouco.')))
        p['capa'] = 'A RESENHA DO GIL'
    # Notícias opcionais: falhas da pesquisa não bloqueiam os dados confirmados do jogo.
    from src.flamengo.coletor.pesquisa import enriquecer
    p = enriquecer(p, j, agora)
    from src.flamengo.engajamento import aplicar
    p = aplicar(p, j)
    p = quadros.dirigir(p)
    ator = 'primo' if modo == 'palpite' else 'rubro'  # IDs técnicos do rig, nomes públicos Gil/Cida.
    p.update(apresentador='Dona Cida' if modo=='palpite' else 'Gil', solo=ator, versao_editorial=5,
             dia=agora.astimezone(BRT).date().isoformat(), jogo_utc=j['utc'])
    for b in p['batidas']:
        b.update(personagem=ator)
        b.setdefault('plano', 'aberto')
        b['fala'] = b['fala'].replace('primo', 'Nação').replace('Primo', 'Nação')
        b['legenda'] = b['fala']
    p['publicar_em'] = publicar_em
    p['legenda_post'] = base.legenda(p)
    return p


def validar_envio(p, agora=None):
    import time
    agora = agora or datetime.now(timezone.utc)
    alvo = datetime.fromisoformat(p['publicar_em'])
    while agora < alvo:
        time.sleep(min(30, (alvo-agora).total_seconds()))
        agora = datetime.now(timezone.utc)
    if agora.astimezone(BRT).date().isoformat() != p['dia']:
        raise RuntimeError('Janela encerrada: não publicar pré-jogo em outro dia.')
    feitos, futuros = agenda_segura()
    cfg=json.loads(Path('config/programacao.json').read_text())
    modo,j=selecionar(agora,feitos,futuros,estado.ler()['itens'],cfg)
    if not modo or FORMATOS[modo]!=p['formato'] or str(j.get('id'))!=str(p.get('jogo_id')):
        raise RuntimeError('Pauta mudou, foi publicada ou partida foi adiada; gerar novamente.')
    if p.get('jogo_utc') and j['utc']!=p['jogo_utc']:
        raise RuntimeError('Horário da partida mudou; atualizar pauta antes de publicar.')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out');ap.add_argument('--validar-envio');a=ap.parse_args()
    if a.validar_envio:
        validar_envio(json.loads(Path(a.validar_envio).read_text()));return 0
    if not a.out:ap.error('--out obrigatório')
    p=montar(datetime.now(timezone.utc))
    if p is None: return 3
    out=Path(a.out);out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(p,ensure_ascii=False,indent=2))
    print(p['formato'], p.get('apresentador', 'Card'))
    return 0

if __name__=='__main__': raise SystemExit(main())
