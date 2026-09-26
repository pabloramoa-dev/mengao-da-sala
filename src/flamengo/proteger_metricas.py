"""Criptografa relatórios privados antes de persistir em repositório público."""
import io
import subprocess
import tarfile
from pathlib import Path


def main():
    arquivos = [Path('data/metricas.json'),Path('docs/RESULTADOS_30_DIAS.md')]
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w:gz') as tar:
        for p in arquivos:
            if p.exists(): tar.add(p,arcname=str(p))
    resultado=subprocess.run(['openssl','cms','-encrypt','-binary','-aes-256-cbc',
        '-outform','DER','config/metricas_publica.pem'],input=buf.getvalue(),capture_output=True,check=True)
    Path('data/metricas_privadas.cms').write_bytes(resultado.stdout)
    # Os arquivos abertos continuam só no runner; nunca são incluídos no commit/artefato.

if __name__=='__main__': main()
