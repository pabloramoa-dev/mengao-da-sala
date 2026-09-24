"""Orquestrador do Reel do canal do Flamengo.

    python -m src.flamengo.gerar --snapshot data/snapshot.json \
        --formato pos_jogo --out saida/reel.mp4

Formatos: situacao | pos_jogo. (noticia exige aprovação humana: não passa por aqui
sem o texto já reescrito e aprovado.)

Trava editorial: se o formato for pos_jogo e não houver partida FINISHED,
o script sai com código 3 e NÃO gera vídeo — o workflow entende como "hoje não".
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from src.flamengo import roteiro
from src.flamengo.render import voz
from src.flamengo.render.cena import PRE_ROLL

RAIZ = Path(__file__).resolve().parents[2]


def gerar(snapshot: dict, formato: str, destino: Path) -> Path | None:
    if formato == "situacao":
        pauta = roteiro.situacao(snapshot)
    elif formato == "pos_jogo":
        pauta = roteiro.pos_jogo(snapshot)
    elif formato == "pos_jogo_v2":
        pauta = roteiro.pos_jogo_v2(snapshot["analise"], (snapshot.get("snapshot") or {}).get("tabela"))
    else:
        raise SystemExit(f"formato desconhecido: {formato}")
    if pauta is None:
        print("[trava] sem partida encerrada e confirmada — nenhum vídeo hoje")
        return None

    destino = destino.resolve()
    trab = destino.parent / f"trab_{destino.stem}"
    audio = voz.narrar(pauta["batidas"], trab, RAIZ)

    conteudo = dict(pauta, segs=audio["segs"])
    (trab / "conteudo.json").write_text(json.dumps(conteudo, ensure_ascii=False),
                                        encoding="utf-8")

    env = dict(os.environ, FLAMENGO_TRAB=str(trab), PYTHONPATH=str(RAIZ))
    subprocess.run([sys.executable, "-m", "manim", "-r", "1080,1920", "--fps", "30",
                    "--disable_caching", "--media_dir", str(trab / "media"),
                    str(Path(__file__).parent / "render" / "cena.py"), "ReelFlamengo"],
                   check=True, cwd=RAIZ, env=env)
    mudo = next((trab / "media" / "videos").rglob("ReelFlamengo.mp4"))

    atraso = int(PRE_ROLL * 1000)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mudo), "-i", str(audio["master"]),
                    "-filter_complex", f"[1:a]adelay={atraso}:all=1,apad[a]",
                    "-map", "0:v", "-map", "[a]",
                    "-c:v", "libx264", "-profile:v", "main", "-level", "4.0",
                    "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", str(destino)], check=True)

    (destino.with_suffix(".json")).write_text(json.dumps({
        "formato": pauta["formato"], "humor": pauta["humor"], "capa": pauta["capa"],
        "voz": voz.PRESET_BIRA, "filtro": voz.FILTRO_BIRA,
        "falas": [b["fala"] for b in pauta["batidas"]], "publicado": False,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--formato", choices=["situacao", "pos_jogo", "pos_jogo_v2"], default="situacao")
    ap.add_argument("--analise", help="data/analise.json do coletor (formato pos_jogo_v2)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    snap = json.loads(Path(a.snapshot).read_text(encoding="utf-8"))
    if a.formato == "pos_jogo_v2":
        if not a.analise:
            raise SystemExit("pos_jogo_v2 precisa de --analise")
        snap = {"snapshot": snap, "analise": json.loads(Path(a.analise).read_text(encoding="utf-8"))}
    saida = gerar(snap, a.formato, Path(a.out))
    if saida is None:
        sys.exit(3)
    print(f"ok: {saida}")


if __name__ == "__main__":
    main()
