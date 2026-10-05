"""Resolve envios inconclusivos antes de selecionar novas pautas; sem reenvio cego."""
from src.flamengo import estado, publicar


def main():
    itens=estado.ler()['itens']
    pendentes=[i for i in itens if i.get('status')=='publicacao_pendente']
    if not pendentes:return
    publicar.verificar_destino()
    user,token,base,_=publicar._cfg()
    for item in pendentes:
        cid=item.get('container_id')
        if not cid:raise RuntimeError('Recibo inconclusivo sem container')
        status=publicar._req('GET',f'{base}/{cid}',{'fields':'status_code','access_token':token}).get('status_code')
        if status=='PUBLISHED':
            # O container confirma a publicação, mesmo se a resposta media_publish se perdeu.
            item.update(status='publicado', confirmacao='container:PUBLISHED')
            estado.salvar(item)
        elif status in {'ERROR','EXPIRED'}:
            item.update(status='falhou');estado.salvar(item)
        else:
            raise RuntimeError('Publicação inconclusiva; aguardando confirmação do Instagram, sem duplicar')

if __name__=='__main__':main()
