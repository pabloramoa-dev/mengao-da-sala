# Mengão da Sala — HyperFrames

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
