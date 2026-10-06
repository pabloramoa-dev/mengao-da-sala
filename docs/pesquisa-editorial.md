# Pesquisa e memória editorial — Gil e Dona Cida

A pesquisa combina os feeds configurados com uma busca por Flamengo e adversário.
Links diretos de veículos têm prioridade sobre agregadores. Trafilatura 2.3.0 lê
texto e data original; Jina é alternativa. Exigem-se RSS recente (36 horas) e data
recente na página. Página sem data verificável é descartada. Datas sem hora são
comparadas por dia; não se presume precisão horária inexistente.

Até quatro documentos, oito tentativas de leitura e dois fatos por episódio.
Textos quase idênticos são removidos. Cada fala precisa de trecho de apoio,
atribuição ao veículo e preservação de incerteza. Não existe confirmação
independente automática: múltiplos veículos podem reproduzir a mesma origem.

O recibo de publicação guarda os fatos usados e a análise do palpite. Apenas
publicações confirmadas alimentam a memória de sete dias; ensaios e falhas não
consomem assuntos. Fatos iguais ou falas quase iguais são filtrados. Mudanças
concretas podem ser abordadas novamente. O pós-jogo já compara o palpite publicado
com o resultado e utiliza estatísticas e substituições disponíveis na ESPN.

O palpite usa até oito jogos encerrados por equipe, nos últimos 180 dias. Cada
partida anterior recebe fator 0,85; mesmo mando recebe peso 1,5 (sem esse peso em
campo neutro). A estimativa de gols combina média de gols marcados de uma equipe
com sofridos da outra; arredondamento dá o placar editorial. Não é modelo
calibrado nem promessa de acerto. Descanso é citado quando disponível, sem
coeficiente inventado. Desfalques entram na fala, não em ajuste numérico.

Com menos de três partidas válidas de qualquer equipe, Cida declara falta de
base e dá um feeling de 1 a 1. Pesquisa indisponível não impede roteiro baseado
nos dados estruturados. O diagnóstico do workflow registra o resultado real da
coleta, incluindo ausência de evidência; execução verde não significa notícias
necessariamente incorporadas.

SoccerData, Penaltyblog e Agent Reach completo não são dependências: falta validar
cobertura, estabilidade e um histórico adequado antes de adotar novos modelos.
