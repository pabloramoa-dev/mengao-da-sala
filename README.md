# Programação atual: Gil e Dona Cida

Desde 05/10/2026, consulte [operação Gil/Cida](docs/GIL_CIDA.md). Pré na véspera às 19h; palpite às 9h; pós no dia seguinte às 6h; card nos dias livres. Os quadros descritos abaixo são documentação histórica.

# Mengão da Sala — v3 (personagens animados + Plantão da Sala)

## O que mudou na v3

- **Motor padrão `v3`** (`src/flamengo/render/hyperframes_v3.py`): Juninho e Primo
  em rig SVG por camadas (`render/personagens_v3.py`), animados direto no
  HyperFrames/GSAP, sem camada Manim. Oito expressões para cada um (neutra,
  eufórico, indignado, debochado, rindo, chocado, sofrendo, tenso), piscar a
  cada 2–5 s, respiração, quem escuta reage, boca em 5 formatos pelo áudio,
  câmera aproximando nas falas fortes e tremida de tela no gol. Sala à noite
  com a TV em primeiro plano mostrando placar, tabela ou manchete.
- **Recuperação**: `FLAMENGO_MOTOR=dupla` volta ao motor aprovado em 30/09
  (Manim + HyperFrames). `manim-dupla` e `v1` continuam para casos extremos.
- **Plantão da Sala** (`src/flamengo/plantao.py`): lê `data/noticias_hoje.json`
  (`src/flamengo/coletor/noticias.py`), pega as 3 pautas de maior nota das
  últimas 24 h e monta um Reel de 15–25 s. A Groq reescreve com palavras
  próprias a partir do título; fala parecida demais com o título, número ou
  nome fora do título é recusado; rumor é falado como rumor; os veículos vão
  na legenda.
- **Rodízio novo** (`diario.py`): em dia sem jogo o padrão é o Plantão. Humor
  (sofá, primo, você sabia) entra no máximo 2 vezes por semana (quarta e
  sábado). Sem notícias válidas ou sem Groq, cai no rodízio antigo sem falhar.
  Pré-jogo, pós-jogo e tabela seguem na cobertura, como antes.
- **CTA final em todo vídeo**: seguir o @mengaodasala para não perder nenhuma
  notícia do Mengão, ou mandar para um flamenguista amigo.
- `video_diario.yml` coleta as notícias antes da pauta; `validar.yml` renderiza
  sem publicar o Plantão (notícias fictícias), o primo rival e o pós-jogo fictício.

Travas mantidas: deduplicação por recibo, pós-jogo só com partida FINISHED,
nada de fato ou fala inventada de pessoa real, `PUBLICAR` intocado.

---

# Motor anterior — HyperFrames (30/09/2026)

Motor padrão dos Reels do `@mengaodasala`: Juninho e Primo Secador com os rigs
originais do Manim, vozes distintas e composição HyperFrames/GSAP. Integração
aprovada em 30/09/2026.

## Produção

`pauta verificada → vozes + lip-sync → sala/personagens Manim → HyperFrames → MP4`

O visual aprovado é compartilhado pelos vídeos diários, esquetes e pós-jogo:
cartões animados, câmera, legendas com destaque por palavra, campo animado,
placar, tabela, pontuação Cartola, trocas, reações, trilha e efeitos discretos.
Dados esportivos vêm das batidas já verificadas; o compositor não cria fatos.
Medidores de secagem são identificados como humor. As marcações das palavras
são aproximadas por proporção dentro dos segmentos de fala.

Juninho usa `pt-BR-AntonioNeural` e Primo usa
`en-US-AndrewMultilingualNeural`, conforme a escolha registrada em
`render/voz_dupla.py`. A reserva Kokoro continua disponível se o serviço Edge
falhar. A camada Manim do protótipo aprovado é 720×1280; os gráficos, textos e
arquivo final são 1080×1920, a 30 fps.

## Instalar e gerar

```bash
sudo apt-get install libpango1.0-dev libcairo2-dev ffmpeg espeak-ng fonts-dejavu-core
pip install -r requirements.txt
# Node.js 24
npm ci --prefix video
(cd video && npx --no-install hyperframes browser ensure)
python -m src.flamengo.gerar --formato diario --pauta data/pauta_diario.json --out saida/reel.mp4
```

O orquestrador produz o MP4 e os mesmos arquivos `.txt` (legenda) e `.json`
(metadados) esperados pela publicação. O MP4 é gravado primeiro em um caminho
temporário; só passa ao caminho final depois de confirmar duração, áudio,
resolução e frame rate com FFprobe.

## Automação e validação

- `video_diario.yml` e `video_pos_jogo.yml`: instalam Node, compositor e Chrome,
  aproveitam cache de navegador/vozes e geram com o novo padrão.
- `validar.yml`: testes, compilação e três renders sem publicar (dupla, pauta
  solo e pós-jogo com dados fictícios). Artefato `amostra-hyperframes-producao`.
- A publicação segue a configuração existente `PUBLICAR=true`; ensaios não
  publicam. Horários, recibos e prevenção de duplicatas permanecem no fluxo.
- A trava editorial continua bloqueando pós-jogo sem partida `FINISHED`.

Para uma recuperação deliberada, `FLAMENGO_MOTOR=dupla` seleciona o render
anterior para pautas de dupla e `FLAMENGO_MOTOR=v1` seleciona o motor antigo.
Não há troca silenciosa de motor visual se o HyperFrames falhar: o job falha
antes de publicar. `FLAMENGO_HF_WORKERS` ajusta a concorrência (padrão 2);
`FLAMENGO_HF_BASE_RES` ajusta a camada Manim (padrão `720,1280`).

```bash
pip install pytest numpy pillow
python -m pytest -q
python -m compileall -q src
```
