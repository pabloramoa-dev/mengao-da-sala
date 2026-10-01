"""Amostras fictícias de cobertura para CI; jamais entram na fila de publicação."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
from src.flamengo import cobertura as c, quadros


def main():
    agora=datetime(2026,10,5,23,tzinfo=timezone.utc)
    linhas=[{'id':'819' if n==1 else str(n),'time':'Flamengo' if n==1 else 'Equipe Exemplo '+str(n),
             'rank':n,'points':61-n,'gamesPlayed':28,'wins':18,'ties':6,'losses':4,'pointDifferential':30-n}
            for n in range(1,21)]
    j={'id':'fixture-pre','utc':(agora+timedelta(hours=12)).isoformat(),'liga':'conmebol.recopa',
       'competicao':'Recopa (AMOSTRA FICTÍCIA)','adversario':'Rival Exemplo','fonte':'https://www.espn.com/',
       'horario_confirmado':True,'estadio':'Estádio Exemplo'}
    for nome,p in [('pre',c.pre_jogo(j,[],[],agora)),('tabela',c.tabela_semanal(linhas,'fixture-W41',agora))]:
        p=quadros.dirigir(p);p['legenda_post']=c.legenda(p);p['_nota']='AMOSTRA FICTÍCIA. NÃO PUBLICAR.'
        Path('saida').mkdir(exist_ok=True)
        Path(f'saida/{nome}_pauta_teste.json').write_text(json.dumps(p,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
