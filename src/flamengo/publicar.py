"""Publicador de Reels do @mengaodasala — mesmo padrão do @previsaorj.

Rota: "API do Instagram com login do Instagram" (graph.instagram.com).
Travas, na ordem:
  1. DESTINO: o token tem de apontar para @mengaodasala; qualquer outra conta
     (inclusive seus outros canais) bloqueia a publicação.
  2. REPETIDO: se já existe post recente com a mesma legenda, não publica de novo
     (protege contra reexecução do workflow).
  3. CONTAINER: só publica quando o Instagram terminar de processar o vídeo.

Uso (no workflow, com IG_USER_ID e IG_ACCESS_TOKEN nos secrets):
    python -m src.flamengo.publicar --video-url URL --legenda saida/x.txt
    python -m src.flamengo.publicar --so-verificar
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from src.flamengo import estado
import urllib.error
import urllib.parse
import urllib.request

ESPERADO = "mengaodasala"


def _cfg():
    user = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_ACCESS_TOKEN")
    versao = os.environ.get("META_GRAPH_VERSION") or "v26.0"
    esperado = (os.environ.get("EXPECTED_IG_USERNAME") or ESPERADO).lstrip("@").casefold()
    if not user or not token:
        raise RuntimeError("IG_USER_ID/IG_ACCESS_TOKEN ausentes")
    return user, token, f"https://graph.instagram.com/{versao}", esperado


def _req(metodo: str, url: str, params: dict) -> dict:
    corpo = urllib.parse.urlencode(params).encode()
    if metodo == "GET":
        req = urllib.request.Request(f"{url}?{corpo.decode()}")
    else:
        req = urllib.request.Request(url, data=corpo, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        erro = exc.read().decode("utf-8", "ignore")[:400]
        raise RuntimeError(f"Instagram {exc.code}: {erro}") from None


def verificar_destino() -> dict:
    user, token, base, esperado = _cfg()
    dados = _req("GET", f"{base}/{user}", {"fields": "id,username", "access_token": token})
    obtido = (dados.get("username") or "").casefold()
    if obtido != esperado:
        raise RuntimeError(f"DESTINO BLOQUEADO: token aponta para @{obtido}, esperado @{esperado}")
    return dados


def encontrar_publicado(legenda: str, limite: int = 100) -> str | None:
    user, token, base, _ = _cfg()
    dados = _req("GET", f"{base}/{user}/media",
                 {"fields": "id,caption,timestamp", "limit": str(limite), "access_token": token})
    alvo = " ".join(legenda.split()).casefold()
    return next((m["id"] for m in dados.get("data", [])
                 if " ".join((m.get("caption") or "").split()).casefold() == alvo), None)


def publicar_reel(video_url: str, legenda: str, espera_max: int = 420, meta=None, story=False) -> str:
    user, token, base, _ = _cfg()
    meta = meta or {}
    params = {"media_type":"STORIES", "image_url":video_url, "access_token":token} if story else {
        "media_type":"REELS", "video_url":video_url, "caption":legenda,
        "share_to_feed":"true", "access_token":token}
    cont = _req("POST", f"{base}/{user}/media", params)["id"]
    estado.registrar(legenda, meta, "processando", container_id=cont)
    print(f"[ig] container {cont} criado, aguardando processamento")
    fim = time.time() + espera_max
    while time.time() < fim:
        estado = _req("GET", f"{base}/{cont}", {"fields": "status_code",
                                                "access_token": token}).get("status_code")
        if estado == "FINISHED":
            break
        if estado in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"container {estado}")
        time.sleep(10)
    else:
        raise TimeoutError("Instagram não terminou de processar o vídeo")
    estado.registrar(legenda, meta, "publicacao_pendente", container_id=cont)
    media = _req("POST", f"{base}/{user}/media_publish",
                 {"creation_id": cont, "access_token": token})["id"]
    return media


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video-url")
    ap.add_argument("--story", action="store_true", help="video-url aponta para PNG de Story")
    ap.add_argument("--legenda", help="arquivo .txt com a legenda")
    ap.add_argument("--so-verificar", action="store_true")
    a = ap.parse_args()

    destino = verificar_destino()
    print(f"[ig] destino confirmado: @{destino['username']}")
    if a.so_verificar:
        return 0

    legenda = open(a.legenda, encoding="utf-8").read().strip()
    print(f"[ig] legenda {hashlib.sha256(legenda.encode()).hexdigest()[:12]} ({len(legenda)} caracteres)")
    meta_path = Path(a.legenda).with_suffix(".json")
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    anterior = next((x for x in estado.ler()['itens'] if x['chave'] == estado.chave(legenda, meta)), {})
    media = anterior.get("media_id") if anterior.get("status") == "publicado" else (None if a.story else encontrar_publicado(legenda))
    if not media:
        if anterior.get("status") == "publicacao_pendente":
            raise RuntimeError("Publicação anterior inconclusiva: reconciliar container antes de reenviar")
        estado.registrar(legenda, meta, "gerado")
        try:
            media = publicar_reel(a.video_url, legenda, meta=meta, story=a.story)
        except Exception:
            atual = next(x for x in estado.ler()['itens'] if x['chave'] == estado.chave(legenda,meta))
            if atual.get('status') != 'publicacao_pendente':
                estado.registrar(legenda, meta, "falhou")
            raise
    estado.registrar(legenda, meta, "publicado", media_id=media)
    print(f"[ig] PUBLICADO: media_id {media}")
    with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a") as f:
        f.write(f"- Conteúdo publicado no @mengaodasala: media_id `{media}`\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
