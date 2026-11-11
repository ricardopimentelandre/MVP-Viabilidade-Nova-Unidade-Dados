"""Testes das análises P1–P4 (scripts/analise_ssd.py), sem rede nem Colab.

Executar na raiz do repositório: python -m unittest discover -s tests -v
Teste opcional com o CSV real: defina PSP8_CSV_REAL com o caminho do arquivo da versão 1.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.analise_ssd import (
    FAIXA_ATENCAO, FAIXA_CRITICA, FAIXA_FAVORAVEL,
    avaliar_cenario, carregar_prata, classificar, comparar_cenarios, correlacoes, curva_indice,
    estatisticas_descritivas, indice_historico, percentil_empirico, ponto_de_virada, recomendacoes,
    sensibilidade_em_desvios, sensibilidade_uma_dimensao,
)
from scripts.pipeline_etl_drive import COLUNAS_ESPERADAS, processar_csv

RAIZ = Path(__file__).resolve().parents[1]


def base_uniforme(n=100):
    """Base sintética em que o percentil de v é exatamente v (1..100) nas três dimensões."""
    return pd.DataFrame({
        "Estimated_Cost_USD": range(1, n + 1),
        "Risk_Assessment_Score": range(1, n + 1),
        "Time_Estimate_Days": range(1, n + 1),
        "Feasibility_Label": ["Feasible"] * n,
    })


def csv_sintetico(caminho, n=20):
    linhas = []
    for i in range(1, n + 1):
        linhas.append([f"P{i:04d}", "Urban Flyover", "Road", "Medium", 1_000_000 + i * 1000, 60, 30 + i, 50,
                       1.0, 0.5 + i / 100, 100 + i, "Feasible", 2])
    pd.DataFrame(linhas, columns=COLUNAS_ESPERADAS).to_csv(caminho, index=False)


class TestePercentilEFaixas(unittest.TestCase):
    def test_percentil_empirico_inclui_o_proprio_valor(self):
        s = pd.Series(range(1, 11))
        self.assertEqual(percentil_empirico(5, s), 50.0)
        self.assertEqual(percentil_empirico(0, s), 0.0)
        self.assertEqual(percentil_empirico(10, s), 100.0)
        self.assertEqual(percentil_empirico(5.5, s), 50.0)

    def test_cortes_das_faixas_sao_os_do_mvp_original(self):
        self.assertEqual(classificar(32.99), FAIXA_FAVORAVEL)
        self.assertEqual(classificar(33), FAIXA_ATENCAO)
        self.assertEqual(classificar(66.99), FAIXA_ATENCAO)
        self.assertEqual(classificar(67), FAIXA_CRITICA)
        # a classificação usa o índice sem arredondar: 66,996 aparece como 67,00, mas é Atenção
        self.assertEqual(f"{66.996:.2f}", "67.00")
        self.assertEqual(classificar(66.996), FAIXA_ATENCAO)

    def test_metodologia_igual_a_do_notebook_original(self):
        nb = json.loads((RAIZ / "MVP_Viabilidade_Nova_Unidade_Dados.ipynb").read_text(encoding="utf-8"))
        codigo = {i: "".join(c["source"]) for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"}
        original = {}
        exec(codigo[8], original)  # define calcular_percentil
        df = base_uniforme(37)
        for v in (0, 1, 7.5, 20, 37, 99):
            self.assertEqual(percentil_empirico(v, df["Estimated_Cost_USD"]),
                             original["calcular_percentil"](v, df["Estimated_Cost_USD"]))
        avaliar = codigo[10]
        for literal in ("indice_geral < 33", "indice_geral < 67", "score_custo >= 67",
                        "score_risco >= 67", "score_tempo >= 67", ") / 3"):
            self.assertIn(literal, avaliar)


class TesteCenarios(unittest.TestCase):
    def test_indice_e_media_simples_dos_percentis(self):
        a = avaliar_cenario(base_uniforme(), 90, 60, 30)
        self.assertEqual(a["percentis"], {"custo": 90.0, "risco": 60.0, "prazo": 30.0})
        self.assertAlmostEqual(a["indice"], 60.0)
        self.assertEqual(a["faixa"], FAIXA_ATENCAO)

    def test_faixas_e_recomendacoes(self):
        df = base_uniforme()
        self.assertEqual(avaliar_cenario(df, 10, 10, 10)["faixa"], FAIXA_FAVORAVEL)
        critica = avaliar_cenario(df, 90, 90, 90)
        self.assertEqual(critica["faixa"], FAIXA_CRITICA)
        self.assertIn("Recomenda-se não iniciar a implantação sem revisão do planejamento.", critica["recomendacoes"])
        self.assertIn("Revisar orçamento, fornecedores e criar reserva de contingência.", critica["recomendacoes"])
        r = recomendacoes({"custo": 66.9, "risco": 67.0, "prazo": 10.0}, FAIXA_ATENCAO)
        self.assertEqual(r[0], "Custo dentro de uma faixa administrável frente aos projetos históricos.")
        self.assertEqual(r[1], "Elaborar plano formal de mitigação de riscos antes da implantação.")
        self.assertEqual(r[2], "Prazo está em faixa administrável frente aos projetos históricos.")

    def test_contribuicoes_somam_100(self):
        a = avaliar_cenario(base_uniforme(), 90, 60, 30)
        self.assertAlmostEqual(sum(a["contribuicao_%"].values()), 100.0)

    def test_comparar_cenarios(self):
        t = comparar_cenarios(base_uniforme(), {"A": (10, 10, 10), "B": (90, 90, 90)})
        self.assertEqual(list(t.index), ["A", "B"])
        self.assertEqual(t.loc["A", "faixa"], FAIXA_FAVORAVEL)
        self.assertEqual(t.loc["B", "n_alertas"], 3)


class TesteSensibilidade(unittest.TestCase):
    base = {"custo": 50, "risco": 50, "prazo": 50}

    def test_variacao_zero_reproduz_o_cenario_base(self):
        df = base_uniforme()
        s = sensibilidade_uma_dimensao(df, self.base, [-20, 0, 20])
        base = avaliar_cenario(df, 50, 50, 50)["indice"]
        self.assertTrue((s[s["variacao_%"] == 0]["indice"] == base).all())

    def test_indice_nao_diminui_quando_a_dimensao_aumenta(self):
        s = sensibilidade_uma_dimensao(base_uniforme(), self.base, [-30, -10, 0, 10, 30])
        for _, g in s.groupby("dimensao"):
            self.assertTrue(g.sort_values("variacao_%")["indice"].is_monotonic_increasing)

    def test_risco_e_limitado_a_100(self):
        s = sensibilidade_uma_dimensao(base_uniforme(), {"custo": 50, "risco": 90, "prazo": 50}, [30])
        self.assertEqual(s[s["dimensao"] == "risco"]["valor"].iloc[0], 100)

    def test_variacao_em_desvios_e_simetrica_na_base_uniforme(self):
        s = sensibilidade_em_desvios(base_uniforme(), self.base, [0])
        self.assertEqual(s["indice"].nunique(), 1)

    def test_curva_cobre_a_faixa_observada(self):
        c = curva_indice(base_uniforme(), self.base, "custo", pontos=10)
        self.assertEqual((c["valor"].min(), c["valor"].max()), (1, 100))
        self.assertTrue(c["indice"].is_monotonic_increasing)

    def test_ponto_de_virada(self):
        df = base_uniforme()
        pv = ponto_de_virada(df, {"custo": 90, "risco": 90, "prazo": 90}, "custo", 67)
        # (c + 90 + 90) / 3 < 67  =>  c < 21  =>  maior valor observado que serve: 20
        self.assertEqual(pv["valor"], 20.0)
        self.assertTrue(pv["alcancavel"])
        inalcancavel = ponto_de_virada(df, {"custo": 100, "risco": 100, "prazo": 100}, "custo", 33)
        self.assertFalse(inalcancavel["alcancavel"])
        self.assertIsNone(inalcancavel["valor"])


class TesteEstatisticas(unittest.TestCase):
    def test_p1_estatisticas_e_correlacao(self):
        df = base_uniforme()
        e = estatisticas_descritivas(df)
        self.assertEqual(e.loc["custo", "minimo"], 1)
        self.assertEqual(e.loc["custo", "maximo"], 100)
        self.assertEqual(e.loc["custo", "mediana"], 50.5)
        self.assertEqual(e.loc["custo", "outliers_iqr"], 0)
        self.assertAlmostEqual(correlacoes(df).loc["custo", "prazo"], 1.0)


class TesteIndiceHistorico(unittest.TestCase):
    def test_indice_historico_igual_ao_indice_de_cada_projeto(self):
        df = base_uniforme(50)
        h = indice_historico(df)
        for i in (0, 10, 49):
            r = df.iloc[i]
            a = avaliar_cenario(df, r["Estimated_Cost_USD"], r["Risk_Assessment_Score"], r["Time_Estimate_Days"])
            self.assertAlmostEqual(h["indice"].iloc[i], a["indice"])
            self.assertEqual(h["faixa"].iloc[i], a["faixa"])
        self.assertEqual(len(h), 50)


class TesteCarregarPrata(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        csv_sintetico(self.root / "e.csv")
        self.r = processar_csv(self.root / "e.csv", self.root / "d")

    def test_le_prata_e_confere_manifesto(self):
        df, m = carregar_prata(self.r["pasta_execucao"])
        self.assertEqual(len(df), 20)
        self.assertEqual(m["registros_prata"], 20)

    def test_nao_grava_nada_na_pasta_de_execucao(self):
        antes = sorted(p.name for p in Path(self.r["pasta_execucao"]).rglob("*"))
        carregar_prata(self.r["pasta_execucao"])
        self.assertEqual(antes, sorted(p.name for p in Path(self.r["pasta_execucao"]).rglob("*")))

    def test_prata_alterada_e_rejeitada(self):
        p = Path(self.r["caminho_prata"])
        p.write_text(p.read_text(encoding="utf-8").replace("Road", "Rode", 1), encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "SHA-256"):
            carregar_prata(self.r["pasta_execucao"])


@unittest.skipUnless(
    os.environ.get("PSP8_CSV_REAL") and Path(os.environ.get("PSP8_CSV_REAL", "")).is_file(),
    "defina PSP8_CSV_REAL com o CSV real da versão 1 para executar",
)
class TesteResultadosReais(unittest.TestCase):
    def test_resultados_reais_do_cenario_demonstrado(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = processar_csv(Path(os.environ["PSP8_CSV_REAL"]), Path(tmp))
            df, _ = carregar_prata(r["pasta_execucao"])
            a = avaliar_cenario(df, 5_500_000, 80, 480)
            self.assertEqual({k: round(v, 1) for k, v in a["percentis"].items()},
                             {"custo": 75.7, "risco": 72.3, "prazo": 75.1})
            self.assertEqual(round(a["indice"], 1), 74.4)
            self.assertEqual(a["faixa"], FAIXA_CRITICA)
            e = estatisticas_descritivas(df)
            self.assertEqual((e.loc["custo", "minimo"], e.loc["custo", "maximo"]), (1000404, 6998223))
            self.assertEqual((e.loc["risco", "minimo"], e.loc["risco", "maximo"]), (30, 99))
            self.assertEqual((e.loc["prazo", "minimo"], e.loc["prazo", "maximo"]), (120, 599))


if __name__ == "__main__":
    unittest.main()
