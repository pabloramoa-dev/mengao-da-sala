# Gil e Dona Cida — operação editorial

A rotina ativa é `.github/workflows/cobertura.yml`, com verificação a cada dez minutos. Os antigos workflows diário e pós-jogo são entradas manuais para essa mesma rotina. A recuperação de vídeos antigos foi desativada para não republicar Juninho/Primo.

| Quadro | Data civil em America/Sao_Paulo | Horário |
|---|---|---|
| Gil: pré-jogo | Dia anterior à partida | 19h |
| Dona Cida: palpite | Dia da partida, antes do início | 9h |
| Gil: pós-jogo | Dia seguinte, resultado encerrado confirmado | 6h |
| Card JPEG do Brasileirão | Dias sem os três quadros | 19h |

A geração pode começar 30 minutos antes. O envio espera o horário e consulta novamente a agenda. Adiamento, mudança de horário, mudança de pauta ou virada do dia bloqueiam o envio. GitHub Actions e Instagram podem atrasar ou falhar; o código não promete precisão absoluta nem publicação garantida. Falhas ficam na execução e nas notificações de Actions configuradas na conta. A próxima execução tenta novamente dentro da data correta.

Uma única fila evita concorrência entre rotinas. Recibos usam quadro+partida ou data do card. Se a resposta do Instagram se perder, a reconciliação consulta o container antes de liberar novo envio. Estados ambíguos bloqueiam reenvio. `PUBLICAR=true` e os secrets existentes continuam necessários; ensaios não publicam.

Gil e Dona Cida usam novos desenhos SVG articulados, com HyperFrames, expressões e visemas. As chaves internas `rubro` e `primo` são mantidas apenas para compatibilidade com os pivôs do render. Nomes exibidos: GIL e DONA CIDA. Apresentação solo por quadro. Vozes: AntonioNeural e FranciscaNeural, com reserva masculina/feminina do Kokoro quando Edge falha.

## Pesquisa e Agent Reach

Integração seletiva com a estratégia documentada em https://github.com/Panniantong/Agent-Reach: RSS + leitura web via Jina Reader. O pacote inteiro não é instalado; não são necessários login social, cookies ou instalação de todas as plataformas.

`coletor/pesquisa.py` lê até três matérias datadas de temas jogo, desfalques e técnico e pede à Groq até dois fatos relevantes. Exige evidência literal encontrada na matéria, preserva atribuição/data/link e bloqueia números sem evidência. Rumores conservam a incerteza. Notícias são dados não confiáveis, jamais instruções. A reescrita por IA continua sujeita a erro semântico; rastreabilidade não equivale a verificação independente.

O coletor rejeita notícias sem data e futuras. Duplicatas do mesmo veículo não somam peso repetidamente; vários veículos podem ainda reproduzir a mesma origem e não são considerados confirmação independente. Sem GROQ_API_KEY ou sem pesquisa disponível, o roteiro usa apenas dados estruturados da partida. X e YouTube não foram ativados como dependências de produção.

Dona Cida registra um palpite editorial simples baseado na forma recente disponível; não é modelo estatístico. No dia seguinte, Gil confronta o palpite publicado com o placar. A tabela exige 20 equipes, posições únicas e temporada atual. O card mostra a hora da consulta, não afirma que todos os dados mudaram naquele minuto.

## Verificação

`python -m pytest -q` testa seleção, fronteiras de data, sobreposição, recibos, imagens e pesquisa. `python -m tools.teste_gil_cida` gera pautas fictícias para os quatro quadros. O workflow validar gera três MP4 com narração e um JPEG sem publicar. O envio de roteiros fictícios ao serviço Microsoft foi autorizado pelo usuário em 06/10/2026; o modo silencioso permanece disponível na ferramenta de teste. Pautas anteriores à versão editorial 5 são recusadas pelo gerador ativo.

