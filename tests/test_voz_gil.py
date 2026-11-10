"""Garante as vozes principais e as reservas do Gil e da Dona Cida.

Os testes nao baixam modelo, nao acionam Edge e nao publicam videos.
"""
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.flamengo.render import voz_dupla as voz


FALA = "Hoje tem Mengao!"
AMOSTRA = np.zeros(128, dtype=np.float32)


def sintetizar(quem):
    edge, rate, pitch = voz.parametros(quem, "neutra")
    return voz.sintetizar_fala(quem, FALA, edge, rate, pitch)


def test_gil_tem_pm_alex_como_voz_principal():
    assert voz.VOZES["rubro"]["motor"] == "kokoro"
    assert voz.VOZES["rubro"]["voz_principal"] == "pm_alex:0.70+im_nicola:0.30"
    with patch.object(voz, "_kokoro", return_value=AMOSTRA) as kokoro, \
         patch.object(voz, "edge_mp3") as edge:
        audio, motor = sintetizar("rubro")
    assert motor == "kokoro"
    assert audio is AMOSTRA
    kokoro.assert_called_once_with(FALA, "pm_alex:0.70+im_nicola:0.30")
    edge.assert_not_called()


def test_gil_recorre_ao_antonio_se_kokoro_falhar():
    with patch.object(voz, "_kokoro", side_effect=RuntimeError("offline")), \
         patch.object(voz, "edge_mp3", return_value=Path("antonio.mp3")) as edge, \
         patch.object(voz, "_ler", return_value=AMOSTRA) as ler:
        audio, motor = sintetizar("rubro")
    assert motor == "edge"
    assert audio is AMOSTRA
    edge.assert_called_once_with(FALA, "pt-BR-AntonioNeural", "-2%", "+0Hz")
    ler.assert_called_once_with(Path("antonio.mp3"))


def test_cida_usa_mistura_propria():
    with patch.object(voz, "_kokoro", return_value=AMOSTRA) as kokoro:
        audio, motor = sintetizar("primo")
    assert audio is AMOSTRA and motor == "kokoro"
    kokoro.assert_called_once_with(FALA, "pf_dora:0.80+bf_emma:0.20")


def test_cida_recorre_a_francisca():
    with patch.object(voz, "_kokoro", side_effect=RuntimeError("offline")), \
         patch.object(voz, "edge_mp3", return_value=Path("voz.mp3")) as edge, \
         patch.object(voz, "_ler", return_value=AMOSTRA):
        audio, motor = sintetizar("primo")
    assert audio is AMOSTRA and motor == "edge"
    edge.assert_called_once_with(FALA, "pt-BR-FranciscaNeural", "-2%", "+0Hz")
