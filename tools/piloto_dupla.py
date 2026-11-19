"""Piloto Gil e Dona Cida. Não consulta partidas e não publica nas redes."""
import json
from pathlib import Path
from src.flamengo.render import voz_dupla, hyperframes_v3

RAIZ = Path(__file__).resolve().parents[1]

def pauta():
    falas = [
        ("rubro", "Dona Cida, por que a senhora escondeu o controle?", "neutra", "perguntar", "revirar", "CADÊ O CONTROLE?"),
        ("primo", "Porque você troca de lugar no sofá e acha que muda o placar!", "debochado", "explicar", "choque", "TÁTICA DE SOFÁ"),
        ("rubro", "É estratégia! Quando eu levanto, o Mengão ataca!", "euforico", "peito", "revirar", "SUPERSTIÇÃO RUBRO-NEGRA"),
        ("primo", "Então vai lavar a louça. Vai que sai uma goleada?", "debochado", "explicar", "choque", "ESCALADO PRA PIA"),
        ("rubro", "A senhora quer título ou cozinha limpa?", "chocado", "perguntar", "rir", "TÍTULO OU LOUÇA?"),
        ("primo", "Os dois, meu filho! Aqui o Flamengo joga e você lava!", "rindo", "ombros", "sofrer", "DONA CIDA ESCALOU!"),
        ("rubro", "Nação, essa superstição funciona ou eu caí na conversa dela?", "neutra", "perguntar", "rir", "CAÍ NA CONVERSA?"),
        ("primo", "Comenta aí! E deixa o controle comigo!", "debochado", "peito", "rir", "QUEM MANDA NO CONTROLE?"),
    ]
    bats = [dict(personagem=q, fala=t, humor=h, gesto=g, reacao=r,
                 tipo="cta" if i == 7 else "abre" if i == 0 else "resenha",
                 dados={"cartao":c}, plano="close" if i in (3,5,7) else "dupla")
            for i,(q,t,h,g,r,c) in enumerate(falas)]
    return dict(formato="o_sofa_nao_aguenta", versao_editorial=5,
                capa="QUEM MANDA NO CONTROLE?", batidas=bats,
                legenda_post="Gil e Dona Cida juntos: a superstição do sofá virou escalação para lavar a louça! Uma cena de humor fictícia.",
                piloto=True, publicado=False)

def main():
    out=RAIZ / "saida" / "mengao_gil_cida_conversa.mp4"
    trab=out.parent / "trab_dupla"; trab.mkdir(parents=True, exist_ok=True)
    p=pauta()
    audio=voz_dupla.narrar(p["batidas"], trab, RAIZ, equalizar=True, pausa_troca=.34)
    conteudo=dict(p,segs=audio["segs"])
    meta=hyperframes_v3.renderizar(conteudo,audio,out,trab,RAIZ)
    out.with_suffix(".json").write_text(json.dumps(dict(conteudo,**meta,motor_voz=audio["motor_voz"],equalizacao=True),ensure_ascii=False,indent=2))
    out.with_suffix(".txt").write_text(p["legenda_post"])
    print(out)

if __name__ == "__main__":
    main()
