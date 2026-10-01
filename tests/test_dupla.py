"""Esquete Juninho x Primo Secador: roteiro dirigido, CTA e validação da Groq."""
import pytest

from src.flamengo import dialogos, quadros


def test_banco_inteiro_passa_na_validacao():
    for esq in dialogos.BANCO:
        falas = dialogos.validar(esq["falas"])
        assert falas[0]["quem"] == "rubro" and "?" in falas[0]["fala"]
        assert falas[-1]["quem"] == "rubro" and "?" in falas[-1]["fala"]
        assert any(f.get("carimbo") for f in falas)


def test_pauta_do_primo_tem_dupla_direcao_e_cta():
    p = quadros.dirigir(quadros.primo("2026-09-28"))
    assert p["motor"] == "dupla"
    quem = {b["personagem"] for b in p["batidas"]}
    assert quem == {"rubro", "primo"}
    assert p["batidas"][-1]["tipo"] == "cta"
    assert all(b.get("gesto") and b.get("humor") for b in p["batidas"])


def test_sem_chave_nao_chama_groq(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert dialogos.esquete_groq({"tabela": {}}) is None


@pytest.mark.parametrize("ruim", [
    [{"quem": "rubro", "fala": "oi?"}] * 6,                                   # só um personagem
    [{"quem": "primo", "fala": "x" * 130}] + [{"quem": "rubro", "fala": "a?"}] * 5,   # fala longa
    [{"quem": "primo", "fala": "seu idiota"}] + [{"quem": "rubro", "fala": "a?"}] * 5,  # ofensa
])
def test_validacao_recusa_esquete_ruim(ruim):
    with pytest.raises(ValueError):
        dialogos.validar(ruim)


def test_ferramenta_de_cache_usa_as_mesmas_vozes_do_motor():
    import importlib.util
    from src.flamengo.render import voz_dupla
    spec = importlib.util.spec_from_file_location("vc", "tools/vozes_cache.py")
    vc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vc)
    assert vc.EMOCAO == voz_dupla.EMOCAO
    for q in ("rubro", "primo"):
        for h in voz_dupla.EMOCAO:
            assert vc.parametros(q, h) == voz_dupla.parametros(q, h)
    assert vc.voz_chave("a", "+1%", "+0Hz", "oi") == voz_dupla.voz_chave("a", "+1%", "+0Hz", "oi")


CTX = {"tabela": {"posicao": 1, "pontos": 64, "rival_nome": "Palmeiras", "diferenca": 5},
       "proximo_jogo": {"adversario": "Flamengo x Santos"}}


def test_checagem_recusa_clube_nome_e_numero_fora_dos_dados():
    for fala in ["Vai perder pro Corinthians, primo.",
                 "O Pedro vai perder pênalti de novo.",
                 "Três pontos de vantagem não segura ninguém."]:
        with pytest.raises(ValueError):
            dialogos.checar_fatos([{"quem": "primo", "fala": fala}], CTX)


def test_checagem_aceita_o_que_esta_nos_dados_e_o_banco():
    ok = [{"quem": "primo", "fala": "O Palmeiras tá cinco pontos atrás. Por enquanto."},
          {"quem": "rubro", "fala": "E o Santos vem aí. Eu já separei o sofá."}]
    dialogos.checar_fatos(ok, CTX)
    for esq in dialogos.BANCO:
        assert esq["fato"]["flamengo"] > esq["fato"]["rival"]


def test_desafios_cobrem_rivais_e_periodos_sem_inventar_titulos():
    assert len({e["rival"] for e in dialogos.BANCO}) == 11
    assert len(dialogos.BANCO) == 77
    for e in dialogos.BANCO:
        fato = e["fato"]
        assert fato["flamengo"] > fato["rival"]
        assert e["falas"][0]["fala"].endswith("?")
        assert e["falas"][2]["quem"] == "rubro"
        assert str(fato["flamengo"]) in e["falas"][2]["carimbo"]
        assert e["fontes"]


def test_memoria_nao_repete_desafio_antes_de_esgotar():
    usados = []
    for _ in dialogos.BANCO:
        e = dialogos.escolher_banco("mesmo-dia", usados)
        chave = "primo:" + e["chave"]
        assert chave not in usados
        usados.append(chave)
