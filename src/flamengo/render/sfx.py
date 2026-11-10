"""Síntese de estádio com o impacto original do Caixeiro na Corrida."""
import numpy as np

SR = 48000


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _rng(seed):
    return np.random.default_rng(seed)


def _norm(x):
    p = np.max(np.abs(x)) or 1.0
    return x / p


def _lowpass(x, corte):
    """Passa-baixa de 1 polo com corte (Hz) fixo ou variável no tempo."""
    corte = np.broadcast_to(np.asarray(corte, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * corte / SR)
    y = np.empty_like(x)
    v = 0.0
    for i in range(len(x)):
        v += a[i] * (x[i] - v)
        y[i] = v
    return y


def impacto(seed=6):
    """Choque: batida grave + ar."""
    t = _t(0.6)
    f = 110 * np.exp(-t * 9) + 38
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    ar = _lowpass(_rng(seed).normal(size=len(t)), 900) * np.exp(-t * 10) * 2
    return _norm(boom + ar)


def estadio(dur):
    t = _t(dur)
    ruido = _rng(819).normal(size=len(t))
    coro = np.convolve(ruido, np.ones(25) / 25, mode='same')
    return coro * (.65 + .35 * np.sin(2*np.pi*t*.7))


def apito():
    t = _t(.26)
    return np.sin(2*np.pi*2200*t + .9*np.sin(2*np.pi*32*t))*np.sin(np.pi*t/.26)**2
