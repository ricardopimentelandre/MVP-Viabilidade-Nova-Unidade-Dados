"""Testes locais sem rede/Colab usando dados mínimos artificiais.

Executar na raiz do repositório: python -m unittest discover -s tests -v
Os testes aqui não substituem a execução com 3.245 registros no Drive.
"""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.pipeline_etl_drive import (
    COLUNAS_ESPERADAS,
    preparar_prata,
    ler_csv,
    processar_csv,
    sha256_arquivo,
)


def linha_base(identificador="P0001"):
    return {
        "Project_ID": identificador,
        "Project_Name": "Projeto A",
        "Project_Type": "Building",
        "Scope_Complexity": "Medium",
        "Estimated_Cost_USD": 5500000,
        "Resource_Allocation_Score": 57,
        "Risk_Assessment_Score": 80,
        "Environmental_Impact_Score": 60,
        "Historical_Cost_Deviation_%": 2.5,
        "Stakeholder_Priority_Score": 65,
        "Time_Estimate_Days": 480,
        "Feasibility_Label": "Medium",
        "Scope_Complexity_Numeric": 2,
    }


class TestePipeline(unittest.TestCase):
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

    def test_camada_bronze_identica_e_prata_reaberta(self):
        self.escrever([linha_base("P0001"), linha_base("P0002")])
        resultado = processar_csv(self.source, self.root / "drive_simulado")
        manifesto = resultado["manifesto"]
        self.assertEqual(manifesto["registros_bronze"], 2)
        self.assertEqual(manifesto["registros_prata"], 2)
        self.assertEqual(len(manifesto["colunas_prata"]), 13)
        self.assertEqual(manifesto["sha256_fonte"], manifesto["sha256_bronze"])
        self.assertEqual(sha256_arquivo(self.source), sha256_arquivo(Path(resultado["caminho_bronze"])))
        self.assertEqual(manifesto["releitura_bronze_e_prata"], "APROVADA")
        self.assertEqual(resultado["auditoria"]["project_id_duplicados"], 0)
        pasta = Path(resultado["pasta_execucao"])
        self.assertTrue((pasta / "evidencias" / "manifesto_execucao.json").is_file())
        self.assertTrue((pasta / "evidencias" / "auditoria_qualidade.json").is_file())
        self.assertEqual(
            json.loads((pasta / "evidencias" / "manifesto_execucao.json").read_text(encoding="utf-8"))["registros_prata"],
            2,
        )

    def test_auditoria_sinaliza_id_duplicado_e_faixa_anomala(self):
        segunda = linha_base("P0001")
        segunda["Risk_Assessment_Score"] = 125
        self.escrever([linha_base("P0001"), segunda])
        resultado = processar_csv(self.source, self.root / "drive_simulado")
        auditoria = resultado["auditoria"]
        self.assertEqual(auditoria["project_id_duplicados"], 1)
        self.assertEqual(auditoria["atributos"]["Risk_Assessment_Score"]["fora_0_a_100"], 1)

    def test_esquema_incompleto_rejeitado(self):
        self.escrever([linha_base()])
        linhas = self.source.read_text(encoding="utf-8").splitlines()
        self.source.write_text("\n".join(s.replace("Scope_Complexity_Numeric", "Outro_Campo") for s in linhas) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Esquema diferente"):
            processar_csv(self.source, self.root / "drive_simulado")
        self.assertFalse((self.root / "drive_simulado").exists())

    def test_texto_invalido_em_numerico_rejeitado(self):
        linha = linha_base()
        linha["Estimated_Cost_USD"] = "VALOR INVALIDO"
        self.escrever([linha])
        with self.assertRaisesRegex(ValueError, "Coluna numérica inválida"):
            preparar_prata(ler_csv(self.source))


if __name__ == "__main__":
    unittest.main()
