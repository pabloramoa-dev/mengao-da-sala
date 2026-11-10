"""Redução de fundo durante a fala, compartilhada com Caixeiro na Corrida."""
import numpy as np


def ducking(voz: np.ndarray, sr: int, profundidade: float = 0.65,
            ataque: float = 0.04, soltura: float = 0.45) -> np.ndarray:
    """Ganho 0..1 para a trilha: cai `profundidade` enquanto há voz."""
    hop = max(1, sr // 100)                       # envelope a cada 10 ms
    n = len(voz) // hop + 1
    pad = np.zeros(n * hop)
    pad[: len(voz)] = np.abs(voz)
    env = pad.reshape(n, hop).max(axis=1)
    ativo = (env > 0.02).astype(float)
    a_up = 1 - np.exp(-0.01 / ataque)
    a_dn = 1 - np.exp(-0.01 / soltura)
    sm = np.zeros(n)
    v = 0.0
    for i, x in enumerate(ativo):
        v += (a_up if x > v else a_dn) * (x - v)
        sm[i] = v
    ganho = 1 - profundidade * sm
    return np.interp(np.arange(len(voz)), np.arange(n) * hop, ganho)
