"""Camada dos personagens originais, sem HUD: composição fica no HyperFrames.

O relógio absoluto dirige a pose. Transições entre gestos são calculadas a
partir das duas batidas, sem acumular transformações ou congelar updaters.
"""
import json
import os
from pathlib import Path

import numpy as np
from manim import Dot, ORIGIN, Rectangle, Scene, VGroup, DOWN, config
from src.flamengo.render import dupla as D
from src.flamengo.render.hyperframes import validar_conteudo

config.frame_width, config.frame_height = 8.0, 14.222222
config.pixel_width, config.pixel_height = [int(n) for n in os.environ.get("FLAMENGO_HF_BASE_RES", "720,1280").split(",")]
config.frame_rate = 30

ABERTURA = {"X": 0, "A": 0, "B": .3, "C": .6, "D": 1, "E": .75, "F": .4, "G": .35, "H": .5}
REACAO = {
    "celular": ("debochado", "celular"), "nao": ("indignado", "cruzar"),
    "revirar": ("debochado", "ombros"), "rir": ("rindo", "ombros"),
    "sofrer": ("sofrendo", "facepalm"), "orgulho": ("euforico", "peito"),
    "choque": ("chocado", "maos_juntas"), "cruzar": ("debochado", "cruzar"),
    "sim": ("neutra", "repouso"),
}


def direcao(b, q):
    if b.get("personagem", "rubro") == q:
        expr, gesto = b.get("humor", "neutra"), b.get("gesto", "explicar")
        if gesto == "perguntar":
            gesto = "ombros"
        return (expr if expr in D.EXPRESSOES else "neutra",
                gesto if gesto in D.GESTOS else "explicar")
    return REACAO.get(b.get("reacao") or ("celular" if q == "primo" else "nao"), ("neutra", "repouso"))


class HyperframesBase(Scene):
    def construct(self):
        trab = Path(os.environ["FLAMENGO_TRAB"])
        c = json.loads((trab / "conteudo.json").read_text())
        total = validar_conteudo(c)
        bats, segs = c["batidas"], c["segs"]
        cues = json.loads((trab / "lip.json").read_text())["mouthCues"]
        amp = np.zeros(int(total * 60) + 3)
        for cue in cues:
            amp[int(cue["start"] * 60):int(cue["end"] * 60)] = ABERTURA.get(cue["value"], 0)
        bg, lights = D.sala()
        actors = VGroup()
        sofa = D.sofa().shift(DOWN * .6)
        tv = Rectangle(width=12, height=20, fill_color="#7FB2FF", fill_opacity=.03, stroke_width=0)
        motor = Dot(radius=.001).set_opacity(0)
        self.add(bg, actors, sofa, tv, motor)
        for m in (actors, tv, bg):
            m.add_updater(lambda m, dt: None)

        def update(m, dt):
            if dt == 0:
                actors.submobjects = []
                return
            t = self.renderer.time
            i = next((k for k, s in enumerate(segs) if t < s["fim"]), len(segs)-1)
            b, s = bats[i], segs[i]
            out = []
            for q, x, face in [("rubro", -1.9, 1), ("primo", 1.95, -1)]:
                talk = b.get("personagem", "rubro") == q and s["ini"] <= t < s["fim_fala"]
                a = float(amp[min(len(amp)-1, int(t*60))]) if talk else 0
                expr, gesto = direcao(b, q)
                e, d = D.maos_do_gesto(q, gesto, face, t)
                elapsed = max(0, t-s["ini"])
                if i and elapsed < .22:
                    _, antes = direcao(bats[i-1], q)
                    ae, ad = D.maos_do_gesto(q, antes, face, t)
                    k = elapsed/.22
                    k = k*k*(3-2*k)
                    e, d = ae+(e-ae)*k, ad+(d-ad)*k
                blink = (t+(1.2 if q == "primo" else 0)) % 3.7 < .12
                pop = 1 + .05*np.exp(-elapsed*14)*np.sin(elapsed*35) if elapsed < .4 else 1
                pose = dict(expr=expr, gesto=gesto, face=face, boca=a, palp=1 if blink else 0,
                            olhar=(face*.85, -.8 if gesto == "celular" else .08), sob=.4*a,
                            tilt=.035*face+.035*np.sin(t*2.6), lean=.1*face if talk else 0,
                            bob=.025*np.sin(t*2.2), cab_dy=.06*a, maoE=e, maoD=d, escala_pop=pop, t=t)
                out.append(D.desenhar(q, pose).scale(1.1, about_point=ORIGIN).shift(np.array([x, -1.25, 0])))
            actors.submobjects = out
            tv.set_fill(opacity=.028+.025*(np.sin(t*5.3)+1)/2)
            for k, luz in enumerate(lights):
                luz.set_fill(opacity=.6+.35*(np.sin(t*1.5+k) > 0))
        motor.add_updater(update)
        self.wait(total)
