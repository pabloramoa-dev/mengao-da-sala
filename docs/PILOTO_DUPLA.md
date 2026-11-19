# Gil e Dona Cida: conversa no sofá

Executar `python -m tools.piloto_dupla` ou o workflow **Piloto Gil e Dona Cida conversando**. Saída: `saida/mengao_gil_cida_conversa.mp4`. O piloto não publica nem muda a programação diária.

Referência inspecionada: `pabloramoa-dev/previsao-modelo`, `hyperframes/comunicado_dupla.py`, workflow e assets dupla. O modelo combina HyperFrames/GSAP, alternância de falas Kokoro, sincronização de boca por personagem, reações do ouvinte, gestos, piscadas, legendas e mixagem. Seus extras incluem SFX Kit/Komiku/Open Peeps (CC0) e Geopattern (MIT). Esses assets externos não são copiados: o piloto usa a sala, os rigs originais Gil/Cida e os efeitos já existentes no Mengão.

A adaptação usa o compositor real `hyperframes_v3`, reações explícitas por turno, aproximações e pausa de 0,34 s na troca. As falas são sintetizadas inteiras com as vozes atuais do canal. Equalização independente retira graves excessivos, reduz médios abafados e realça presença; compressão leve e ajuste de volume por fala precedem a masterização final. A opção é exclusiva do piloto até avaliação, sem alterar velocidade ou tom. O diálogo é ficcional, sem inventar placares ou notícias.
