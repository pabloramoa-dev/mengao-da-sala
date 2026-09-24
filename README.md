# Canal do Flamengo — motor v0.1

Reel vertical 1080x1920 com o torcedor de camisa listrada na horizontal, voz do
Bira do Tempo (@previsaorj) e dados do football-data.org. Mesma engenharia dos
canais de previsão e do Pablo Guru.

## O que já funciona (testado em 24/09/2026)
- `coletor/futebol.py` — tabela, último jogo, próximo jogo e sequência do
  Brasileirão. Testado offline com fixture; falta a chave real.
- `roteiro.py` — formatos `situacao` (manhã) e `pos_jogo`, números por extenso e
  ordinal na fala, dígito na legenda.
- `render/voz.py` — preset do Bira sem alteração: pm_alex, speed 1.04, gap 0.22,
  filtro highpass+compressor, masterização por ganho fixo a -16,5 LUFS.
- `render/elenco.py` — torcedor em 5 humores (neutra, euforico, indignado,
  tenso, debochado). Sem escudo, sem patrocínio, sem jogador real.
- `render/cena.py` — capa no quadro 0, cartão de placar/posição, legenda no
  terço central, lip sync por amplitude, piscada e respiração no motor.
- `gerar.py` — orquestrador. Trava: pós-jogo sem partida FINISHED sai com código 3
  e não gera vídeo.

## Rodar
    pip install -r requirements.txt          # + apt: libpango1.0-dev libcairo2-dev ffmpeg espeak-ng
    export FOOTBALL_DATA_TOKEN=...           # chave grátis do football-data.org
    python -m src.flamengo.coletor.futebol --out data/snapshot.json
    python -m src.flamengo.gerar --snapshot data/snapshot.json --formato pos_jogo --out saida/reel.mp4

Teste sem chave:
    python -m src.flamengo.coletor.futebol --offline tests/fixture_bsa.json --out data/snapshot.json

## Armadilha nova deste canal
Mobjeto que só é mexido por updater de OUTRO mobjeto é congelado pelo Manim na
imagem estática do wait — foi o que deixou a capa e a legenda antiga fantasmas
no primeiro render. Solução: trocar camadas só ENTRE waits e dar ao personagem
um updater vazio.

## Pendente
Chave do football-data.org, nome/@ do canal, estilo Vox colagem, karaokê palavra
por palavra, formato `noticia` com aprovação, workflows e publicação
(Instagram graph.instagram.com e TikTok separado).
