"""Gera no GitHub Actions o áudio (Edge TTS) de cada fala de uma pauta e
publica numa release — serve para montar o vídeo de teste FORA do Actions
(onde o Edge pode estar bloqueado). Autossuficiente de propósito: roda mesmo
sem o motor da dupla no repositório.

    python tools/vozes_cache.py tools/pauta_teste.json saida_cache/

Os nomes dos arquivos seguem voz_chave() de src/flamengo/render/voz_dupla.py
(mesma fórmula; tests/test_dupla.py confere que as tabelas batem).
"""
import asyncio
import hashlib
import json
import sys
from pathlib import Path

VOZES = {"rubro": dict(voz="pt-BR-AntonioNeural", rate=-2),
         "primo": dict(voz="pt-BR-FranciscaNeural", rate=-2)}
EMOCAO = {"euforico": (8, 6), "indignado": (5, 3), "tenso": (6, 2), "chocado": (3, 8),
          "rindo": (4, 4), "debochado": (-5, -3), "sofrendo": (-8, -5), "neutra": (0, 0)}


def parametros(quem, humor):
    cfg = VOZES.get(quem, VOZES["rubro"])
    dr, dp = EMOCAO.get(humor, (0, 0))
    return cfg["voz"], f"{cfg['rate'] + dr:+d}%", f"{dp:+d}Hz"


def voz_chave(voz, rate, pitch, texto):
    return hashlib.sha1(f"{voz}|{rate}|{pitch}|{texto}".encode("utf-8")).hexdigest()[:16]


async def main(pauta, saida):
    import edge_tts
    saida.mkdir(parents=True, exist_ok=True)
    for b in json.loads(Path(pauta).read_text(encoding="utf-8"))["batidas"]:
        voz, rate, pitch = parametros(b.get("personagem", "rubro"), b.get("humor", "neutra"))
        alvo = saida / f"{voz_chave(voz, rate, pitch, b['fala'])}.mp3"
        await edge_tts.Communicate(b["fala"], voz, rate=rate, pitch=pitch).save(str(alvo))
        print(alvo.name, voz, rate, pitch, b["fala"])


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], Path(sys.argv[2])))
