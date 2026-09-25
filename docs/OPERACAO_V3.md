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

Faixas editoriais de teste: humor 12–20s, opinião 20–35s, história 35–50s. A duração real fica no JSON do vídeo; são faixas de comparação, sem cortar falas nem acelerar voz artificialmente. Comparar pelo menos cinco episódios por formato, com atenção a jogo, assunto, horário e duração. Relatório atualizado em `docs/RESULTADOS_30_DIAS.md`; resultados descritivos, não causalidade.

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
