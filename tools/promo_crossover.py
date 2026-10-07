from pathlib import Path

from src.flamengo.render import hyperframes_v3, voz_dupla

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "promo_crossover_out"
TRAB = OUT / "work"
OUT.mkdir(parents=True, exist_ok=True)
TRAB.mkdir(parents=True, exist_ok=True)

batidas = [
    {
        "personagem": "rubro",
        "fala": "Aqui é o Gil! Futebol, notícia, pré-jogo e pós-jogo com opinião.",
        "humor": "neutra",
        "gesto": "explicar",
        "tipo": "fala",
        "dados": {},
    },
    {
        "personagem": "primo",
        "fala": "E eu sou Dona Cida. Porque torcida também precisa de conversa e bom humor.",
        "humor": "neutra",
        "gesto": "explicar",
        "tipo": "fala",
        "dados": {},
    },
]

audio = voz_dupla.narrar(batidas, TRAB / "audio", RAIZ)
conteudo = {
    "formato": "resenha",
    "capa": "TODOS JUNTOS",
    "batidas": batidas,
    "segs": audio["segs"],
}
meta = hyperframes_v3.renderizar(conteudo, audio, OUT / "gil-dona-cida.mp4", TRAB, RAIZ)
print(meta)
