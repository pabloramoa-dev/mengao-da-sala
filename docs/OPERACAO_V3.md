# Mengão da Sala — operação editorial v3

O canal tem um torcedor rubro-negro e um primo rival de azul, sem representar jogador real. Sofá, almofada e controle são os acessórios recorrentes. A voz do torcedor permanece pm_alex; o primo usa pm_santa. A interpretação alterna expressões, gestos e aproximações por fala, sem acelerar o áudio para cumprir duração.

## Rotina implementada

- Diário às 11h07 de Brasília: um Reel com rodízio entre humor, história, tabela, primo rival e participação.
- Pós-jogo: sondagem a cada 20 minutos; a coleta aprofundada só roda para um jogo encerrado recente, ainda não registrado. GitHub cron pode atrasar; não é transmissão ao vivo.
- Retorno de votação: somente após coleta completa, ao menos três votos válidos e sem repetir a resposta. Conta o último A/B exato por autor. Não guarda nomes, textos livres ou identificadores pessoais. Não lê as respostas como instruções.
- Métricas às 7h17 de Brasília: alcance, compartilhamentos, salvamentos, likes, comentários, tempo médio e follows quando a API disponibilizar. Campos indisponíveis são null e têm diagnóstico.
- Story diário: card vinculado ao Reel, publicado depois dele com o mesmo token. Se a conta não tiver suporte/permissão para Stories, essa etapa falha sem impedir o Reel; o erro fica no Actions. Stickers de votação são nativos do aplicativo: o card encaminha votos A/B aos comentários do Reel, não simula sticker.
- Artefatos incluem MP4, metadados, legendas e cards de Stories/destaques.

## Estado e confiabilidade

`data/publicacoes.json` distingue gerado, processando, publicação pendente, publicado e falhou, com media_id e container_id. Um resultado ambíguo de media_publish bloqueia reenvio automático até reconciliação; não arrisca duplicar.
`data/ultimo_video.json` só avança após publicação de pós-jogo. Ensaios não consomem o rodízio nem marcam jogo como publicado. `PUBLICAR` continua sendo a chave de publicação existente; não é ativada implicitamente.

Pontuação do Cartola está suspensa até o coletor validar a rodada específica do jogo. Quando fornecida por dado verificado, o roteiro distingue pontuação de avaliação esportiva. Mando de campo não determina estádio. A expressão 'logo depois do gol' exige nome completo e intervalo de até cinco minutos.

## Experimento de 30 dias

Faixas editoriais de teste: humor 12–20s, opinião 20–35s, história 35–50s. A duração real fica no JSON do vídeo; são faixas de comparação, sem cortar falas nem acelerar voz artificialmente. Comparar pelo menos cinco episódios por formato, com atenção a jogo, assunto, horário e duração. Relatório gerado no runner como `docs/RESULTADOS_30_DIAS.md` e persistido, junto às métricas, somente no envelope criptografado `data/metricas_privadas.cms`; resultados descritivos, não causalidade.

## Perfil

Nome, bio, ordem de fixados e destaques estão em `config/perfil.json`. Aplicar pela conta @mengaodasala; a sessão inicialmente disponível no navegador era de @opabloguru. Não alterar outra conta.
Fixados: apresentação do personagem; como participar; melhor episódio por compartilhamentos após haver amostra. Não há 'melhor vídeo' validado antes de métricas suficientes.
Capas de destaques são geradas por `python -m src.flamengo.stories`.

## Validação e manutenção

`python -m unittest discover -s tests -v`
`python -m compileall -q src`
O workflow `Validar evolucao editorial` testa, renderiza uma amostra sem publicar e verifica destino/permissões em leitura. O workflow de coleta usa as permissões já concedidas; não pede novas permissões automaticamente.
Fontes técnicas: documentação Meta de publicação, comentários e insights (Instagram Login); se uma métrica não for aceita na versão/configuração da conta, ela permanece indisponível.
Histórias novas: acervo do Museu Flamengo, https://www.museuflamengo.com.br/manto-sagrado-historia, consultado em 25/09/2026. Textos próprios e fontes preservadas na legenda.

## Abrir relatórios privados

A chave `Mengao_Chave_Relatorios.pem` foi entregue separadamente ao proprietário; não colocar no GitHub. O certificado público em `config/metricas_publica.pem` só permite criptografar.

```bash
openssl cms -decrypt -binary -inform DER -in data/metricas_privadas.cms -inkey /caminho/Mengao_Chave_Relatorios.pem -out /tmp/mengao-relatorios.tar.gz
tar -xzf /tmp/mengao-relatorios.tar.gz -C /diretorio/privado
```


## Correção de publicação — 28/09/2026

O publicador distingue o módulo `estado` de `status_container`. Os testes agora
cobrem Reel, Story, processamento, timeout, destino incorreto e duplicatas.

O diário tem tentativas às 11h07, 13h07, 15h07, 17h07 e 19h07 (Brasília).
São tentativas, não cinco publicações: `data/diario.json` encerra o dia após o
Reel confirmado. O agendador do GitHub pode atrasar; não há garantia de minuto exato.
O rodízio é registrado antes do Story, para uma falha de Story não duplicar o Reel.
Falhas de Story ficam visíveis no resultado do job. Os artefatos incluem seus metadados.

`Recuperar publicacoes pendentes` usa os MP4s existentes. Só roda manualmente ou
quando o manifesto `config/recuperacao.json` muda em main. Confere a conta, aplica
a mesma deduplicação e preserva recibos mesmo em falha. A recuperação inicial
publica os Reels de 26 e 27/09 e um Story do mais recente. Não executa em outros perfis.


## Desafios de títulos e auditoria — 01/10/2026

O quadro primo_rival agora usa 34 esquetes dirigidas: 22 sobre Libertadores,
nove sobre Copa do Brasil e três sobre o Carioca. Abrange Vasco, Fluminense,
Botafogo, Palmeiras, Corinthians, São Paulo, Santos, Grêmio, Internacional,
Cruzeiro e Atlético-MG, sem pretender definir um ranking dos maiores clubes.
Juninho pergunta, o rival dá um palpite errado, Juninho corrige e vence a piada.
Os números corretos vêm do banco conferido, sem geração livre da IA.
O rival é identificado nas falas; mantém o personagem original do primo.

Cada comparação declara seu recorte: Libertadores até 2025 ou de 2019 a 2025;
Copa do Brasil até 2024; Carioca até março de 2026. Isso mantém os episódios
corretos mesmo se outra edição terminar. Fontes entram nos metadados e legenda.
O Flamengo não lidera todos os campeonatos. Por isso Cruzeiro e Grêmio não são
comparados com ele no total da Copa do Brasil: um supera, o outro empata.
A vantagem contra eles vem da Libertadores. Nunca antecipar título de 2026.

Auditoria dos recibos: Reel e Story confirmados em 29/09 (19h25 UTC) e
30/09 (19h14–19h15 UTC). Os cinco horários do diário são retentativas para
um único Reel/dia. Depois dele o estado bloqueia as demais tentativas.
Comunidade coleta votos e métricas; não publica vídeos. A resposta à enquete
exige coleta completa e três votos válidos. Os quadros são alternativas no
rodízio, não publicações independentes diárias.

Execução pós-jogo 36824120239: geração/publicação puladas porque não havia
partida elegível. Na agenda consultada, o último jogo encerrado é 401841241,
20/09, e coincide com data/ultimo_video.json. O próximo vem em 08/10.
O marcador antigo sozinho não comprova publicação; os recibos é que confirmam.
A sondagem passa a aceitar partidas não registradas até 24 horas após o início,
para tolerar atraso do cron/coleta. Agenda inteiramente indisponível agora
falha explicitamente e não aparece como ausência confirmada de jogo.

## Cobertura completa e títulos — 01/10/2026

O banco passa a 77 resenhas em 15 categorias de competição/troféu. Acrescenta
Brasileirão (era dos pontos corridos, 2003–2025), Mundial Intercontinental e
FIFA, Supercopa, Recopa, Mercosul, Copa Ouro, Copa dos Campeões, Rio–São Paulo,
Taça Guanabara, Taça Rio, Derby das Américas e Copa Challenger.
O recorte é dito na fala e guardado na legenda. Derby/Challenger são troféus
de fase: não são somados como títulos mundiais completos. Taças estaduais
não são comparadas com campeonatos de outros estados. Torneios que o Flamengo
não ganhou, como Sul-Americana, não geram comparação de vantagem falsa.
O Brasileirão usa um recorte sem a controvérsia de 1987; o Flamengo tem quatro
conquistas de pontos corridos até 2025. Palmeiras e Corinthians empatam nesse
recorte e recebem outras perguntas. Santos tem zero desde 2003.

### Rotina automática independente do humor

- `cobertura.yml`: sondagem aos minutos 11, 31 e 51 de cada hora, com a fila
  compartilhada de publicação para evitar disputa pelo registro no git.
- Pré-jogo: um Reel por jogo, nas 24 horas anteriores ao início confirmado.
  Adversário, competição, data/hora em Brasília, estádio quando informado,
  últimos cinco resultados disponíveis de cada equipe e posição no Brasileiro.
  Termina com uma decisão futebolística para a torcida debater.
- Pós-jogo: um Reel por ID, depois de status encerrado e placar confirmado.
  Competição, resultado, pênaltis quando houver, finalizações/no alvo e posse
  quando disponíveis, substituições verificadas e pergunta de análise.
  Um empate de copa não é narrado como ganho de ponto. Vitória nos pênaltis
  distingue placar do jogo e resultado da disputa. Não declara classificação
  de mata-mata só pelo placar de uma partida, sem agregado confirmado.
- Tabela: toda segunda às 19h BRT; se houver atraso/falha, tenta recuperar ao
  longo da semana. Reel com as 20 equipes, em quatro painéis de cinco: posição,
  pontos, jogos e saldo. A legenda inclui também vitórias, empates e derrotas.
  Mostra líder/vice, distância do Flamengo e alerta sobre jogos a menos.
- Humor diário continua às 11h07 BRT e não consome pré, pós ou tabela.
  O pós-jogo legado fica manual; sua agenda foi substituída pela cobertura.
- A primeira semana pode ser publicada após a ativação para fornecer a tabela
  atual; nas seguintes, segue a janela de segunda-feira às 19h.

### Onde pesquisar e o que sustenta cada conteúdo

1. ESPN, agenda agregada (`all/teams/819/schedule` + `fixture=true`): descobre
   todos os torneios que a fonte registra para o profissional masculino,
   sem depender da antiga lista de três competições. O teste real encontrou
   Brasileirão, Libertadores, Copa do Brasil, Carioca, Supercopa e Recopa em 2026.
   Summary/boxscore dá status, gols, pênaltis, substituições e estatísticas.
2. ESPN standings: classificação completa com ano da temporada. O campo
   `gamesPlayed` já era lido; agora `jogos` também é aceito como alias.
   A melhoria é bloquear estatística obrigatória ausente, em vez de preencher zero.
3. CBF: tabela detalhada, regulamento e súmulas para conferir jogos nacionais:
   https://www.cbf.com.br/futebol-brasileiro
4. FERJ: calendário, súmulas e regulamento do Carioca:
   https://www.fferj.com.br/
5. CONMEBOL: calendário e decisões de Libertadores/Recopa/Sul-Americana:
   https://www.conmebol.com/
6. FIFA: Mundial/Intercontinental e reconhecimento histórico dos campeões:
   https://www.fifa.com/ e https://inside.fifa.com/
7. Flamengo oficial: notícias, convocados, mudanças de estádio/horário e
   anúncio de escalação: https://www.flamengo.com.br/noticias/futebol
   O sistema atual não lê automaticamente escalações/desfalques desse site;
   não inventa essas informações quando não disponíveis na fonte estruturada.

A automação usa ESPN; os sites oficiais são fontes para conferência editorial,
não um fallback automático implementado. Cobrir todos os campeonatos não
significa garantir partidas omitidas pela fonte ou transmissão em tempo real.
A agenda é consultada novamente em cada execução; jogos adiados/cancelados e
horário ainda não confirmado não geram pré. Alteração depois de um pré já
publicado demanda atualização editorial, não um segundo pré automático.

### Controle e recuperação

Recibos separam `pre:<jogo_id>`, `pos:<jogo_id>` e `tabela:<ano-Wsemana>`.
Confirmados e publicação inconclusiva bloqueiam reenvio; texto novo não muda
identidade do conteúdo. Ensaios não registram publicado. Falhas mantêm recibos.
Partidas encerradas desde a ativação podem ser recuperadas por até sete dias;
não dispara publicações antigas de janeiro/setembro ao ativar.
`PUBLICAR` e o token existentes continuam controlando o destino @mengaodasala.

Uma pendência é processada por execução: prioridade para pós, depois pré e
por fim tabela. São no máximo duas publicações por partida, mais o humor do dia
quando houver e uma tabela semanal. Cron do GitHub pode atrasar; não promete
publicação no minuto exato do início ou do apito final.

CI verifica seleção, janelas, deduplicação por jogo/semana, pênaltis, tabela
incompleta, temporada errada, agenda agregada e HTML com os 20 clubes. Renderiza
pré/tabela fictícios sem publicá-los, além dos três formatos anteriores.
