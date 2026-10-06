"""Extração local de artigos; Jina é alternativa, nunca fonte de confirmação."""
import json
import re
import urllib.request
from urllib.parse import urlparse
from src.flamengo.coletor import noticias


def url_publica(url):
    import ipaddress
    import socket
    p = urlparse(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.port not in (None, 443):
        raise ValueError('URL de notícia inválida')
    ips = socket.getaddrinfo(p.hostname, 443, type=socket.SOCK_STREAM)
    if not ips or any(not ipaddress.ip_address(i[4][0]).is_global for i in ips):
        raise ValueError('Endereço não público')
    return url


class Redirecionamento(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url_publica(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def baixar(url):
    url_publica(url)
    req = urllib.request.Request(url, headers={'User-Agent': noticias.UA})
    with urllib.request.build_opener(Redirecionamento()).open(req, timeout=12) as r:
        return r.read(1500000).decode('utf-8', 'replace'), r.url


def extrair(html, url):
    from trafilatura import extract
    raw = extract(html, url=url, output_format='json', with_metadata=True,
                  include_comments=False, include_tables=False,
                  date_extraction_params={'original_date': True, 'extensive_search': False})
    d = json.loads(raw or '{}')
    if len(d.get('text') or '') < 300:
        raise ValueError('Artigo sem texto suficiente')
    return dict(texto=d['text'][:14000], titulo=d.get('title'),
                data_pagina=d.get('date'), link=url, leitor='trafilatura')


def ler(url):
    url_publica(url)
    try:
        html, destino = baixar(url)
        return extrair(html, destino)
    except Exception:
        # O proxy não deve mascarar páginas antigas nem inventar uma data.
        texto, _ = baixar('https://r.jina.ai/' + url)
        if len(texto) < 300 or 'Markdown Content:' not in texto:
            raise ValueError('Leitor alternativo sem artigo')
        data = re.search(r'^Published Time:\s*(.+)$', texto, re.M)
        return dict(texto=texto.split('Markdown Content:', 1)[1][:14000],
                    titulo=None, data_pagina=data.group(1).strip() if data else None,
                    link=url, leitor='jina')
