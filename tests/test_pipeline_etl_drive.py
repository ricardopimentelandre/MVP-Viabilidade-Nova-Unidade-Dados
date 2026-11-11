"""Testes locais sem rede/Colab, com linhas reais da base do Kaggle (v1) e variações inválidas.

Executar na raiz do repositório: python -m unittest discover -s tests -v

Estes testes NÃO comprovam persistência no Google Drive: isso depende da execução no Colab.
Para conferir o CSV real localmente (opcional), defina PSP8_CSV_REAL com o caminho do arquivo.
"""
import csv
import json
import os
import tempfile
import unittest
import warnings
from pathlib import Path

import pandas as pd

from scripts.pipeline_etl_drive import (
    COLUNAS_ESPERADAS,
    DOMINIOS,
    SHA256_CSV_V1,
    _versao_do_caminho,
    auditar_prata,
    ler_csv,
    preparar_prata,
    processar_csv,
    sha256_arquivo,
    verificar_persistencia,
)

# Linhas reais da versão 1 do dataset (P0001, P0003, P0004).
LINHAS_REAIS = [
    ["P0001", "Urban Flyover", "Road", "Medium", 2692743, 57, 68, 69, 0.0, 0.5, 268, "Feasible", 2],
    ["P0003", "Industrial Complex", "Road", "High", 5926484, 90, 50, 62, 0.3, 0.62, 219, "Not Feasible", 3],
    ["P0004", "Smart Solar Grid", "Road", "Medium", 3234489, 95, 58, 76, 3.28, 0.53, 174, "Borderline", 2],
]


def linha(posicao=0, **alteracoes):
    registro = dict(zip(COLUNAS_ESPERADAS, LINHAS_REAIS[posicao]))
    registro.update(alteracoes)
    return registro


def linhas_validas():
    return [linha(0), linha(1), linha(2)]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "entrada.csv"

    def escrever(self, linhas):
        with self.source.open("w", encoding="utf-8", newline="") as arq:
            gravador = csv.DictWriter(arq, fieldnames=COLUNAS_ESPERADAS)
            gravador.writeheader()
            gravador.writerows(linhas)

    def auditar(self, linhas):
        self.escrever(linhas)
        return auditar_prata(preparar_prata(ler_csv(self.source)))


class TestePipeline(Base):
    def test_camada_bronze_identica_e_prata_reaberta(self):
        self.escrever(linhas_validas())
        resultado = processar_csv(
            self.source, self.root / "drive_simulado",
            coletado_em_utc="2026-11-11T00:44:00+00:00", versao_fonte=1,
        )
        m = resultado["manifesto"]
        self.assertEqual((m["registros_bronze"], m["registros_prata"]), (3, 3))
        self.assertEqual(len(m["colunas_prata"]), 13)
        self.assertEqual(m["sha256_fonte"], m["sha256_bronze"])
        self.assertEqual(sha256_arquivo(self.source), sha256_arquivo(Path(resultado["caminho_bronze"])))
        self.assertEqual(m["releitura_bronze_e_prata"], "APROVADA")
        self.assertEqual(resultado["auditoria"]["project_id_duplicados"], 0)
        pasta = Path(resultado["pasta_execucao"])
        gravado = json.loads((pasta / "evidencias" / "manifesto_execucao.json").read_text(encoding="utf-8"))
        self.assertEqual(gravado["registros_prata"], 3)
        self.assertTrue((pasta / "evidencias" / "auditoria_qualidade.json").is_file())

    def test_manifesto_registra_fonte_licenca_versao_tamanho_e_datas(self):
        self.escrever(linhas_validas())
        m = processar_csv(
            self.source, self.root / "d", coletado_em_utc="2026-11-11T00:44:00+00:00", versao_fonte=1,
        )["manifesto"]
        self.assertEqual(m["licenca_dos_dados"], "CC0: Public Domain")
        self.assertEqual(m["versao_kaggle_documentada"], 1)
        self.assertEqual(m["versao_kaggle_baixada"], 1)
        self.assertTrue(m["versao_confere"])
        self.assertEqual(m["coletado_em_utc"], "2026-11-11T00:44:00+00:00")
        self.assertIn("T", m["execucao_utc"])
        self.assertEqual(m["tamanho_bytes_fonte"], self.source.stat().st_size)
        self.assertEqual(m["tamanho_bytes_bronze"], m["tamanho_bytes_fonte"])
        self.assertEqual(m["ambiente"]["pandas"], pd.__version__)
        self.assertFalse(m["ambiente"]["colab"])
        self.assertFalse(m["sha256_fonte_confere_com_v1_documentada"])  # dados sintéticos de teste
        self.assertEqual(len(m["sha256_fonte"]), 64)

    def test_manifesto_sem_coleta_nem_versao_nao_inventa_valores(self):
        self.escrever(linhas_validas())
        m = processar_csv(self.source, self.root / "d")["manifesto"]
        self.assertIsNone(m["coletado_em_utc"])
        self.assertIsNone(m["versao_kaggle_baixada"])
        self.assertIsNone(m["versao_confere"])

    def test_prata_documentada_sem_alterar_conteudo(self):
        self.escrever(linhas_validas())
        r = processar_csv(self.source, self.root / "d")
        m = r["manifesto"]
        self.assertTrue(all(not t["altera_conteudo"] for t in m["transformacoes_prata"]))
        self.assertEqual(m["prata_identica_a_bronze_byte_a_byte"], m["sha256_prata"] == m["sha256_bronze"])
        self.assertEqual(m["esquema_prata"]["Stakeholder_Priority_Score"], "float64")
        origem = pd.read_csv(self.source)
        prata = pd.read_csv(r["caminho_prata"])
        pd.testing.assert_frame_equal(origem, prata, check_dtype=False)

    def test_registros_com_problemas_sao_preservados(self):
        self.escrever([linha(0), linha(1, Stakeholder_Priority_Score=65), linha(1, Feasibility_Label="Medium")])
        r = processar_csv(self.source, self.root / "d")
        prata = pd.read_csv(r["caminho_prata"])
        self.assertEqual(len(prata), 3)
        self.assertEqual(prata["Stakeholder_Priority_Score"].tolist(), [0.5, 65.0, 0.62])
        self.assertEqual(r["auditoria"]["project_id_duplicados"], 1)
        self.assertGreater(r["auditoria"]["resumo"]["total_violacoes_dominio_esperado"], 0)

    def test_esquema_incompleto_rejeitado(self):
        self.escrever(linhas_validas())
        texto = self.source.read_text(encoding="utf-8").replace("Scope_Complexity_Numeric", "Outro_Campo")
        self.source.write_text(texto, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Esquema diferente"):
            processar_csv(self.source, self.root / "drive_simulado")
        self.assertFalse((self.root / "drive_simulado").exists())

    def test_texto_invalido_em_numerico_rejeitado(self):
        self.escrever([linha(0, Estimated_Cost_USD="VALOR INVALIDO")])
        with self.assertRaisesRegex(ValueError, "Coluna numérica inválida"):
            preparar_prata(ler_csv(self.source))

    def test_leitura_sem_aviso_de_depreciacao(self):
        self.escrever(linhas_validas())
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter("always")
            ler_csv(self.source)
        self.assertEqual([str(a.message) for a in avisos], [])


class TesteDominios(Base):
    def test_linhas_reais_nao_violam_dominios(self):
        a = self.auditar(linhas_validas())
        self.assertEqual(a["resumo"]["total_violacoes_dominio_esperado"], 0)
        self.assertEqual(a["resumo"]["atributos_com_violacao_do_dominio_esperado"], [])
        self.assertEqual(a["complexidade_fora_do_mapeamento_low_medium_high"], 0)
        self.assertEqual(a["atributos"]["Feasibility_Label"]["fora_do_dominio_esperado"], 0)
        self.assertEqual(set(a["atributos"]["Feasibility_Label"]["categorias_mais_frequentes"]),
                         {"Feasible", "Not Feasible", "Borderline"})

    def test_stakeholder_em_escala_0_100_e_sinalizado(self):
        # O erro antigo: 65 era aceito como "0–100". Agora é violação da escala 0–1.
        a = self.auditar([linha(0), linha(1, Stakeholder_Priority_Score=65)])
        self.assertEqual(a["atributos"]["Stakeholder_Priority_Score"]["fora_do_dominio_esperado"], 1)

    def test_stakeholder_limites_esperado_e_observado_sao_distintos(self):
        a = self.auditar([linha(0), linha(1, Stakeholder_Priority_Score=0.3),
                          linha(2, Stakeholder_Priority_Score=1.0)])
        s = a["atributos"]["Stakeholder_Priority_Score"]
        self.assertEqual(s["fora_do_dominio_esperado"], 0)   # 0,3 está em [0, 1]
        self.assertEqual(s["fora_do_observado_v1"], 1)       # mas abaixo do 0,5 observado
        self.assertEqual(DOMINIOS["Stakeholder_Priority_Score"]["observado_v1"], {"min": 0.5, "max": 1.0})
        a = self.auditar([linha(0), linha(1, Stakeholder_Priority_Score=-0.1),
                          linha(2, Stakeholder_Priority_Score=1.01)])
        self.assertEqual(a["atributos"]["Stakeholder_Priority_Score"]["fora_do_dominio_esperado"], 2)

    def test_rotulo_invalido_e_sinalizado(self):
        a = self.auditar([linha(0), linha(1, Feasibility_Label="Medium")])
        f = a["atributos"]["Feasibility_Label"]
        self.assertEqual(f["fora_do_dominio_esperado"], 1)
        self.assertEqual(f["valores_fora_do_dominio"], ["Medium"])

    def test_padrao_do_id_e_sinalizado(self):
        a = self.auditar([linha(0), linha(1, Project_ID="X12"), linha(2, Project_ID="P12345")])
        self.assertEqual(a["atributos"]["Project_ID"]["fora_do_dominio_esperado"], 2)

    def test_id_duplicado_e_sinalizado(self):
        a = self.auditar([linha(0), linha(0)])
        self.assertEqual(a["project_id_duplicados"], 1)
        self.assertEqual(a["linhas_duplicadas_exatas"], 1)

    def test_complexidade_textual_e_numerica_inconsistentes(self):
        # "Low" com código 3: par único, mas fora do mapeamento Low=1/Medium=2/High=3.
        a = self.auditar([linha(0), linha(1, Scope_Complexity="Low")])
        self.assertEqual(a["complexidade_fora_do_mapeamento_low_medium_high"], 1)
        self.assertEqual(a["inconsistencias_categoria_para_codigo_complexidade"], 0)
        # "Medium" com dois códigos diferentes: inconsistência categoria -> código.
        a = self.auditar([linha(0), linha(2, Scope_Complexity_Numeric=3)])
        self.assertEqual(a["inconsistencias_categoria_para_codigo_complexidade"], 1)
        a = self.auditar([linha(0), linha(2), linha(2, Project_ID="P0005", Scope_Complexity_Numeric=1)])
        self.assertEqual(a["inconsistencias_categoria_para_codigo_complexidade"], 1)
        self.assertEqual(a["atributos"]["Scope_Complexity_Numeric"]["fora_do_dominio_esperado"], 0)
        a = self.auditar([linha(0, Scope_Complexity_Numeric=4)])
        self.assertEqual(a["atributos"]["Scope_Complexity_Numeric"]["fora_do_dominio_esperado"], 1)

    def test_custo_e_prazo_devem_ser_positivos(self):
        a = self.auditar([linha(0, Estimated_Cost_USD=0, Time_Estimate_Days=-5), linha(1)])
        self.assertEqual(a["atributos"]["Estimated_Cost_USD"]["fora_do_dominio_esperado"], 1)
        self.assertEqual(a["atributos"]["Time_Estimate_Days"]["fora_do_dominio_esperado"], 1)

    def test_escores_fora_de_0_100_e_nao_inteiros(self):
        a = self.auditar([linha(0, Risk_Assessment_Score=125), linha(1, Resource_Allocation_Score=-1),
                          linha(2, Environmental_Impact_Score=50.5)])
        at = a["atributos"]
        self.assertEqual(at["Risk_Assessment_Score"]["fora_do_dominio_esperado"], 1)
        self.assertEqual(at["Resource_Allocation_Score"]["fora_do_dominio_esperado"], 1)
        self.assertEqual(at["Environmental_Impact_Score"]["nao_inteiros"], 1)

    def test_desvio_historico_negativo_e_sinalizado(self):
        a = self.auditar([linha(0, **{"Historical_Cost_Deviation_%": -2.0}), linha(1)])
        self.assertEqual(a["atributos"]["Historical_Cost_Deviation_%"]["fora_do_dominio_esperado"], 1)

    def test_outlier_iqr_e_informativo_e_nao_remove_registro(self):
        linhas = [linha(0, Project_ID=f"P{i:04d}", Estimated_Cost_USD=3_000_000 + i * 10_000) for i in range(1, 21)]
        linhas.append(linha(0, Project_ID="P0099", Estimated_Cost_USD=90_000_000))
        a = self.auditar(linhas)
        custo = a["atributos"]["Estimated_Cost_USD"]
        self.assertEqual(custo["outliers_iqr"]["quantidade"], 1)
        self.assertEqual(custo["fora_do_dominio_esperado"], 0)     # outlier não é violação de domínio
        self.assertEqual(a["linhas"], 21)

    def test_categoria_nova_e_sinalizada_como_fora_do_dominio_observado(self):
        a = self.auditar([linha(0, Project_Type="Airport")])
        self.assertEqual(a["atributos"]["Project_Type"]["valores_fora_do_dominio"], ["Airport"])

    def test_auditoria_nao_tem_campos_sem_valor_analitico(self):
        a = self.auditar(linhas_validas())
        for dados in a["atributos"].values():
            self.assertNotIn("duplicados_na_coluna", dados)
        self.assertNotIn("categorias_mais_frequentes", a["atributos"]["Project_ID"])
        json.dumps(a, allow_nan=False)  # serializável sem NaN/inf


class TesteVerificacaoPersistencia(Base):
    def processar(self):
        self.escrever(linhas_validas())
        return processar_csv(self.source, self.root / "drive_simulado")

    def test_verificacao_aprovada_grava_evidencia(self):
        r = self.processar()
        v = verificar_persistencia(Path(r["pasta_execucao"]), remontado=True)
        self.assertEqual(v["resultado"], "APROVADA")
        self.assertTrue(v["remontagem_do_drive_declarada_pelo_chamador"])
        self.assertEqual(v["arquivos"]["prata"]["linhas"], 3)
        evidencia = Path(r["pasta_execucao"]) / "evidencias" / "verificacao_persistencia.json"
        self.assertTrue(evidencia.is_file())
        self.assertFalse(verificar_persistencia(Path(r["pasta_execucao"]))["remontagem_do_drive_declarada_pelo_chamador"])

    def test_prata_adulterada_e_detectada(self):
        r = self.processar()
        prata = Path(r["caminho_prata"])
        prata.write_text(prata.read_text(encoding="utf-8").replace("Urban Flyover", "Urban Flyover2"), encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "SHA-256"):
            verificar_persistencia(Path(r["pasta_execucao"]))
        self.assertFalse((Path(r["pasta_execucao"]) / "evidencias" / "verificacao_persistencia.json").exists())

    def test_arquivo_ausente_e_detectado(self):
        r = self.processar()
        Path(r["caminho_bronze"]).unlink()
        with self.assertRaisesRegex(AssertionError, "ausente"):
            verificar_persistencia(Path(r["pasta_execucao"]))

    def test_auditoria_gravada_adulterada_e_detectada(self):
        r = self.processar()
        caminho = Path(r["pasta_execucao"]) / "evidencias" / "auditoria_qualidade.json"
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        dados["linhas"] = 999
        caminho.write_text(json.dumps(dados), encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "auditoria"):
            verificar_persistencia(Path(r["pasta_execucao"]))


class TesteVersaoDaFonte(unittest.TestCase):
    def test_versao_extraida_do_caminho_do_kagglehub(self):
        self.assertEqual(_versao_do_caminho("/root/.cache/kagglehub/datasets/ziya07/x/versions/1"), 1)
        self.assertEqual(_versao_do_caminho("/a/versions/12/arquivo.csv"), 12)
        self.assertIsNone(_versao_do_caminho("/kaggle/input/engineering-project-cost-feasibility-dataset"))


@unittest.skipUnless(
    os.environ.get("PSP8_CSV_REAL") and Path(os.environ.get("PSP8_CSV_REAL", "")).is_file(),
    "defina PSP8_CSV_REAL com o CSV real da versão 1 para executar",
)
class TesteCsvReal(Base):
    def test_csv_real_v1(self):
        real = Path(os.environ["PSP8_CSV_REAL"])
        self.assertEqual(sha256_arquivo(real), SHA256_CSV_V1)
        r = processar_csv(real, self.root / "d", versao_fonte=1)
        m, a = r["manifesto"], r["auditoria"]
        self.assertEqual((m["registros_prata"], len(m["colunas_prata"])), (3245, 13))
        self.assertTrue(m["prata_identica_a_bronze_byte_a_byte"])
        self.assertTrue(m["sha256_fonte_confere_com_v1_documentada"])
        self.assertEqual(a["resumo"]["total_violacoes_dominio_esperado"], 0)
        self.assertEqual(a["complexidade_fora_do_mapeamento_low_medium_high"], 0)
        for coluna, dom in DOMINIOS.items():
            if "observado_v1" in dom and "min" in dom["observado_v1"]:
                dados = a["atributos"][coluna]
                self.assertEqual(dados["minimo_observado"], dom["observado_v1"]["min"], coluna)
                self.assertEqual(dados["maximo_observado"], dom["observado_v1"]["max"], coluna)
                self.assertEqual(dados["fora_do_observado_v1"], 0, coluna)
        self.assertEqual(a["atributos"]["Feasibility_Label"]["categorias_mais_frequentes"],
                         {"Feasible": 1931, "Not Feasible": 823, "Borderline": 491})
        verificar_persistencia(Path(r["pasta_execucao"]))


if __name__ == "__main__":
    unittest.main()
