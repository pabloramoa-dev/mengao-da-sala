# Stories automáticos por resposta

Ativação no workflow cobertura.yml, mesma fila e recibos dos vídeos.
Dia do jogo: dois JPEG verticais a partir das 9h de Brasília, antes do início:
quem vence (incluindo empate) e palpite do placar. Ambos exibem horário,
adversário e competição da agenda. Sem horário confirmado não sai palpite.

Demais dias: um Story a partir de 12h. Prioridade à véspera, depois resenha do
jogo de ontem e, nos dias livres, rodízio semanal de memória, camisa, ídolo,
superstição, companhia, estádio e gol inesquecível.

Chamada: Responda a este Story. Não são enquetes com botões: a interação usa a
resposta nativa do Instagram. As respostas precisam estar habilitadas no perfil;
a API usada não verifica nem altera essa configuração. Nenhuma resposta privada
é coletada, respondida ou transformada automaticamente em conteúdo.

Recibos por data e pergunta impedem duplicação. Reconsulta da agenda antes do
envio bloqueia mudança de horário, início ou adiamento. Ensaio só gera arquivos;
PUBLICAR=true controla envio. A geração diária não depende de haver Reel no dia.
Falha de Story gera aviso e não impede o Reel. Recibos pendentes são reconciliados
antes de tentar novamente. Cron e Instagram podem atrasar a publicação.
