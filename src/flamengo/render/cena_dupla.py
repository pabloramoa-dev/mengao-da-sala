"""Cena da esquete Juninho x Primo Secador (motor "dupla", estilo Vox colagem).

Lê $FLAMENGO_TRAB/conteudo.json (batidas + segs) e $FLAMENGO_TRAB/lip.json.

O que tem aqui e não tinha na v1:
  * dois personagens DIFERENTES (dupla.py), sentados atrás do sofá;
  * quem fala: boca pelo áudio, cabeça acompanhando a sílaba, gesto da fala,
    corpo inclinado pro outro; quem ouve: REAGE (revira o olho, ri, cruza o
    braço, olha o celular, balança a cabeça) e olha pra quem fala;
  * piscada irregular por personagem, squash & stretch na troca de humor;
  * câmera plano/contraplano (dupla, close, impacto) movendo em degraus de
    12 fps, com tremida na virada;
  * sala viva: luz da TV piscando neles, luzes da cidade na janela;
  * colagem: carimbo na virada, legenda karaokê em papel rasgado com a COR
    de quem fala + nome, etiquetas coladas, confete, grão de papel no fim.

Regras herdadas e respeitadas: um único motor dirige tudo pelo RELÓGIO
ABSOLUTO; nada de animar submobjeto (o rig redesenha a pose); capa com
título no quadro 0; legenda no terço central; CTA no fim.
"""
import json
import os
from pathlib import Path

import numpy as np
from manim import (DOWN, LEFT, ORIGIN, RIGHT, UP, WHITE, Dot, MovingCameraScene,
                   Rectangle, VGroup, config)

from src.flamengo.render import dupla as D
from src.flamengo.render import papel as PP

config.frame_width = 8.0
config.frame_height = 14.222
_RES = [int(x) for x in os.environ.get("FLAMENGO_RES", "1080,1920").split(",")]
config.pixel_width, config.pixel_height = _RES

TAIL = 1.4
ESCALA = 1.1
BASE = {"rubro": np.array([-1.95, -1.25, 0.0]), "primo": np.array([2.0, -1.25, 0.0])}
FACE = {"rubro": 1, "primo": -1}
COR_FALA = {"rubro": "rubro", "primo": "#1E4E79"}
NOME = {"rubro": "JUNINHO", "primo": "PRIMO SECADOR"}
ABERTURA = {"X": 0.0, "A": 0.0, "B": 0.3, "F": 0.4, "C": 0.6, "E": 0.75, "D": 1.0,
            "G": 0.35, "H": 0.5}

# reação de quem OUVE: (expressão, gesto, olhar_y, extra)
REACAO = {
    "revirar": ("debochado", "cruzar", 0.9, None),
    "rir": ("rindo", "ombros", 0.0, "rir"),
    "nao": ("indignado", "repouso", 0.0, "nao"),
    "sim": ("neutra", "repouso", 0.0, "sim"),
    "cruzar": ("debochado", "cruzar", 0.0, None),
    "celular": ("debochado", "celular", -0.9, None),
    "choque": ("chocado", "maos_juntas", 0.0, "choque"),
    "sofrer": ("sofrendo", "facepalm", 0.0, None),
    "orgulho": ("euforico", "peito", 0.0, None),
}
PADRAO_OUVINTE = {"rubro": "nao", "primo": "celular"}


def _carregar():
    trab = Path(os.environ["FLAMENGO_TRAB"])
    c = json.loads((trab / "conteudo.json").read_text(encoding="utf-8"))
    lip = json.loads((trab / "lip.json").read_text())["mouthCues"]
    return c, lip


def _cues_para_array(cues, total, fps=60):
    n = int(total * fps) + 2
    arr = np.zeros(n)
    for c in cues:
        a, b = int(c["start"] * fps), int(c["end"] * fps)
        arr[a:b] = ABERTURA.get(c["value"], 0.0)
    return arr, fps


# ---------------------------------------------------------------- legenda
def _quebrar_blocos(txt, max_chars=30):
    palavras, blocos, atual = txt.split(), [], []
    for p in palavras:
        if atual and len(" ".join(atual + [p])) > max_chars:
            blocos.append(atual)
            atual = [p]
        else:
            atual.append(p)
    if atual:
        blocos.append(atual)
    # até 2 linhas por cartela
    return [blocos[i:i + 2] for i in range(0, len(blocos), 2)]


def _cartela_legenda(linhas, quem, semente):
    """Banda de papel rasgado na cor de quem fala + palavras separadas (p/ karaokê)."""
    palavras = []
    rows = VGroup()
    for ln in linhas:
        ws = [PP.texto(w, 40, "tinta") for w in ln]
        palavras += ws
        rows.add(VGroup(*ws).arrange(RIGHT, buff=0.16))
    rows.arrange(DOWN, buff=0.12)
    if rows.width > 6.6:
        rows.scale(6.6 / rows.width)
    banda = PP.recorte(rows.width + 0.6, rows.height + 0.5, c=COR_FALA[quem], semente=semente)
    rows.move_to(banda[-1])
    nome = PP.etiqueta(NOME[quem], c_papel="ouro" if quem == "rubro" else "#8CC8EE", c_txt="ink",
                       tam=20, semente=semente + 3, girar=0.04 * FACE[quem])
    nome.next_to(banda, UP, buff=-0.12).align_to(banda, LEFT if quem == "rubro" else RIGHT)
    nome.shift(RIGHT * 0.25 * FACE[quem])
    g = VGroup(banda, rows, nome)
    return g, palavras


# ---------------------------------------------------------------- cena
class EsqueteDupla(MovingCameraScene):
    def construct(self):
        conteudo, cues = _carregar()
        bats, segs = conteudo["batidas"], conteudo["segs"]
        total = segs[-1]["fim"] + TAIL
        amp, fps_lip = _cues_para_array(cues, total)
        rng = np.random.default_rng(11)

        # ---------- mundo ----------
        fundo, luzes = D.sala()
        self.add(fundo)
        luzes_base = [m.copy() for m in luzes]
        fase_luz = rng.uniform(0, 6.28, len(luzes_base))
        palco = VGroup()
        self.add(palco)
        sofa = D.sofa().shift(DOWN * 0.6)
        self.add(sofa)
        luz_tv = Rectangle(width=12, height=20, fill_color="#7FB2FF", fill_opacity=0.05, stroke_width=0)
        self.add(luz_tv)
        hud = VGroup()
        self.add(hud)

        # ---------- HUD pré-montado (coordenadas de TELA: quadro 8 de largura) ----------
        tag = PP.etiqueta("MENGÃO DA SALA", c_papel="negro", c_txt="tinta", tam=24, semente=2).move_to([0, 6.35, 0])
        capa = PP.manchete(conteudo.get("capa", "O PRIMO\nCHEGOU"), c_papel="ouro", tam=70,
                           semente=9, largura_max=6.4).move_to([0, 5.55, 0])
        fita_capa = PP.fita(capa.get_corner(UP + LEFT) + RIGHT * 0.4, girar=0.5)
        capa = VGroup(capa, fita_capa)

        legendas = []          # (t0, t1, grupo, palavras, tempos_palavra)
        for i, (b, s) in enumerate(zip(bats, segs)):
            quem = b.get("personagem", "rubro")
            partes = _quebrar_blocos(b.get("legenda") or b["fala"])
            n_car = [sum(len(w) + 1 for ln in p for w in ln) for p in partes]
            t_ini, t_fim = s["ini"], s.get("fim_fala", s["fim"])
            acc = 0
            for p, nc in zip(partes, n_car):
                a = t_ini + (t_fim - t_ini) * acc / sum(n_car)
                acc += nc
                z = t_ini + (t_fim - t_ini) * acc / sum(n_car)
                g, ws = _cartela_legenda(p, quem, semente=i * 7 + acc)
                g.move_to([0, 3.15, 0])
                pesos = [max(2, len(w.text)) for w in ws]
                ts = [a + (z - a) * sum(pesos[:k]) / sum(pesos) for k in range(len(ws))]
                legendas.append((a, z if p is not partes[-1] else s["fim"], g, ws, ts))

        extras = []            # (t0, t1, mobject, entrada_colada)
        for i, (b, s) in enumerate(zip(bats, segs)):
            if b.get("carimbo"):
                c = PP.carimbo(b["carimbo"], tam=58, girar=0.14 * (1 if i % 2 else -1)).move_to([0.2, 5.35, 0])
                extras.append((s["ini"] + 0.35, s["fim"], c))
            if b.get("tipo") == "cta":
                cta = PP.manchete("SEGUE O\n@MENGAODASALA", c_papel="rubro", c_txt="tinta", tam=64, semente=21)
                cta.move_to([0, 5.1, 0])
                extras.append((s["ini"] + 0.2, total + 1, VGroup(cta, PP.fita(cta.get_top() + UP * 0.05, 0.1))))
            if b.get("tipo") == "pergunta":
                perg = PP.manchete("COMENTA AÍ,\nNAÇÃO!", c_papel="ouro", tam=58, semente=15).move_to([0, 5.25, 0])
                extras.append((s["ini"] + 0.25, s["fim"], perg))

        # ---------- estado do motor ----------
        st = {q: dict(maoE=None, maoD=None, tilt=0.0, lean=0.0, expr=None, t_expr=-9.0,
                      pisc=list(np.cumsum(rng.uniform(2.2, 4.6, 60)) + (0.6 if q == "primo" else 1.4)))
              for q in ("rubro", "primo")}
        cam = {"c": np.array([0.0, 0.45, 0.0]), "w": 8.0, "passo": -1}
        frame = self.camera.frame
        frame.set_stroke(opacity=0)
        motor = Dot(radius=0.001).set_opacity(0)
        self.add(motor, frame)
        for m in (palco, hud, luz_tv, frame, fundo):
            m.add_updater(lambda m, dt: None)      # nunca congelar na imagem estática

        def seg_em(t):
            for i, s in enumerate(segs):
                if t < s["fim"]:
                    return i
            return len(segs) - 1

        def pose_de(q, t, i, dt):
            b = bats[i]
            s = segs[i]
            falando = b.get("personagem", "rubro") == q and s["ini"] <= t < s.get("fim_fala", s["fim"]) + 0.05
            fecho = i == len(segs) - 1 and b.get("personagem", "rubro") == q and t >= s["ini"]
            f = D.FICHA[q]
            face = FACE[q]
            a = float(amp[min(len(amp) - 1, int(t * fps_lip))]) if falando else 0.0
            if falando or fecho:        # no fecho (CTA) segura a cara da última fala
                expr, gesto = b.get("humor", "neutra"), b.get("gesto", "explicar")
                if expr not in D.EXPRESSOES:
                    expr = "neutra"
                olhar = (face * 0.8, 0.1)
                tilt_alvo = 0.05 * face + 0.06 * np.sin(t * 2.4) * f["energia"]
                lean_alvo = 0.14 * face * f["energia"]
                cab_dy = 0.07 * a * f["energia"]
                extra = None
            else:
                chave = b.get("reacao") if b.get("personagem", "rubro") != q else None
                chave = chave or PADRAO_OUVINTE[q]
                expr, gesto, oy, extra = REACAO.get(chave, REACAO["sim"])
                olhar = (face * 0.9, oy)
                tilt_alvo, lean_alvo, cab_dy = 0.03 * face, 0.0, 0.0
                if extra == "nao":
                    tilt_alvo += 0.12 * np.sin(t * 9)
                elif extra == "sim":
                    cab_dy = 0.05 * abs(np.sin(t * 5))
                elif extra == "rir":
                    cab_dy = 0.06 * abs(np.sin(t * 13))
                    a = 0.5 + 0.3 * np.sin(t * 13)
                elif extra == "choque":
                    lean_alvo = -0.18 * face
            e = st[q]
            if e["expr"] != expr:
                e["expr"], e["t_expr"] = expr, t
            maoE, maoD = D.maos_do_gesto(q, gesto, face, t)
            k = min(1.0, dt * 10) if e["maoE"] is not None else 1.0
            e["maoE"] = maoE if e["maoE"] is None else e["maoE"] + (maoE - e["maoE"]) * k
            e["maoD"] = maoD if e["maoD"] is None else e["maoD"] + (maoD - e["maoD"]) * k
            e["tilt"] += (tilt_alvo - e["tilt"]) * min(1.0, dt * 8)
            e["lean"] += (lean_alvo - e["lean"]) * min(1.0, dt * 6)
            pisc = any(0 <= t - p < 0.12 for p in e["pisc"])
            dtx = t - e["t_expr"]
            pop = 1 + 0.09 * np.exp(-dtx * 14) * np.cos(dtx * 40) if dtx < 0.4 else 1.0
            resp = 0.03 * np.sin(t * 2.2 + (1.3 if q == "primo" else 0))
            return dict(expr=expr, gesto=gesto, face=face, boca=a, palp=1.0 if pisc else 0.0,
                        olhar=olhar, sob=0.6 * a if falando else 0.0, tilt=e["tilt"],
                        lean=e["lean"], bob=resp + (0.06 if gesto == "ombros" else 0.0), cab_dy=cab_dy,
                        maoE=e["maoE"], maoD=e["maoD"], escala_pop=pop, t=t)

        def alvo_camera(i, t):
            b, s = bats[i], segs[i]
            q = b.get("personagem", "rubro")
            plano = b.get("plano", "dupla")
            if t < segs[0]["fim"] or b.get("tipo") == "cta":
                plano = "dupla"
            if plano == "close":
                return np.array([BASE[q][0] * 0.45, 0.1, 0.0]), 6.3, 0.0
            if plano == "impacto":
                treme = 0.09 * np.exp(-(t - s["ini"]) * 5) if t - s["ini"] < 0.6 else 0.0
                return np.array([BASE[q][0] * 0.75, -0.2, 0.0]), 5.0, treme
            return np.array([0.0, 0.45, 0.0]), 8.0, 0.0

        def dirigir(m, dt):
            if dt == 0:
                # O wait() chama update_mobjects(dt=0) e LOGO DEPOIS achata a
                # família dos mobjects móveis numa lista fixa: o que estiver no
                # palco/HUD nessa hora fica colado na tela o vídeo inteiro (foi o
                # bug da legenda/capa fantasma). Nessa chamada, palco e HUD vazios.
                palco.submobjects, hud.submobjects = [], []
                return
            t = self.renderer.time
            i = seg_em(t)
            # --- câmera em degraus de 12 fps (movimento de recorte) ---
            passo = int(t * 12)
            c_alvo, w_alvo, treme = alvo_camera(i, t)
            if passo != cam["passo"]:
                cam["passo"] = passo
                cam["c"] = cam["c"] + (c_alvo - cam["c"]) * 0.45
                cam["w"] = cam["w"] + (w_alvo - cam["w"]) * 0.45
            sacode = np.array([np.sin(t * 71) * treme, np.cos(t * 53) * treme, 0.0])
            frame.set(width=cam["w"])
            frame.move_to(cam["c"] + sacode)
            fw, fc = cam["w"], cam["c"] + sacode

            # --- personagens (o primo entra deslizando nos 0,4 s iniciais) ---
            atores = []
            for q in ("rubro", "primo"):
                pose = pose_de(q, t, i, dt)
                g = D.desenhar(q, pose).scale(ESCALA, about_point=ORIGIN).shift(BASE[q])
                if q == "primo" and t < 0.42:
                    g.shift(RIGHT * 4.5 * (1 - PP.degrau(t, 0.42)))
                atores.append(g)
            palco.submobjects = atores

            # --- sala viva ---
            luz_tv.set_fill(opacity=0.035 + 0.03 * (np.sin(t * 7.3) * np.sin(t * 2.9) + 1) / 2
                            + (0.10 * np.exp(-(t - segs[i]["ini"]) * 6) if bats[i].get("carimbo") and t > segs[i]["ini"] else 0))
            for k, lz in enumerate(luzes):
                lz.set_fill(opacity=0.55 + 0.45 * (np.sin(t * 1.3 + fase_luz[k]) > -0.6))

            # --- HUD (segue a câmera) ---
            itens = [] if t < segs[0]["fim"] or bats[i].get("tipo") == "cta" else [tag]
            if t < segs[0]["fim"]:
                itens.append(PP.colado(capa, t + 0.36))           # já assentada no quadro 0
            for (a, z, g, ws, ts) in legendas:
                if a <= t < z:
                    k = max(j for j in range(len(ws)) if ts[j] <= t) if t >= ts[0] else 0
                    cor_orig = ws[k].get_color()
                    ws[k].set_color(PP.cor("ouro"))
                    itens.append(g.copy())
                    ws[k].set_color(cor_orig)
                    break
            for (a, z, mob) in extras:
                if a <= t < z:
                    itens.append(PP.colado(mob, t - a, dur=0.36, escala=1.5, giro=0.22))
            if any(b.get("efeito") == "confete" and s["ini"] <= t < s["ini"] + 2.2 for b, s in zip(bats, segs)):
                s0 = next(s["ini"] for b, s in zip(bats, segs) if b.get("efeito") == "confete" and s["ini"] <= t < s["ini"] + 2.2)
                itens.append(_confete(t - s0))
            tela = VGroup(*[x.copy() if x is tag else x for x in itens])
            tela.scale(fw / 8.0, about_point=ORIGIN).shift(fc)
            hud.submobjects = [tela]

        # NADA de chamar dirigir() antes do wait: o Manim achata a família dos
        # mobjects móveis no INÍCIO do wait, e o que estivesse no palco/HUD agora
        # ficaria colado na tela o vídeo inteiro (foi o bug da legenda fantasma).
        motor.add_updater(dirigir)
        self.wait(total)


def _confete(dt, n=46):
    rng = np.random.default_rng(5)
    cores = [PP.cor("rubro"), PP.cor("negro"), PP.cor("ouro"), WHITE]
    g = VGroup()
    for k in range(n):
        x0, vx = rng.uniform(-3.8, 3.8), rng.uniform(-0.6, 0.6)
        vy0 = rng.uniform(1.5, 4.0)
        y = 7.3 - (vy0 * dt + 3.2 * dt * dt) * 0.9
        x = x0 + vx * dt + 0.2 * np.sin(dt * 6 + k)
        g.add(Rectangle(width=0.16, height=0.09, fill_color=cores[k % 4], fill_opacity=1, stroke_width=0)
              .rotate(dt * 8 + k).move_to([x, y, 0]))
    return g
