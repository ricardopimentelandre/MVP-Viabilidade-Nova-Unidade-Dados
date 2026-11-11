"""O catálogo de dados deve cobrir os 13 atributos e concordar com os domínios do código."""
import unittest
from pathlib import Path

from scripts.pipeline_etl_drive import COLUNAS_ESPERADAS, DOMINIOS, FONTE_METADADOS, SHA256_CSV_V1

CATALOGO = (Path(__file__).resolve().parents[1] / "catalogo" / "catalogo_dados.md").read_text(encoding="utf-8")


class TesteCatalogo(unittest.TestCase):
    def test_todos_os_atributos_estao_no_catalogo(self):
        for coluna in COLUNAS_ESPERADAS:
            self.assertIn(f"`{coluna}`", CATALOGO, coluna)

    def test_categorias_do_codigo_estao_no_catalogo(self):
        for coluna, dom in DOMINIOS.items():
            for categoria in dom.get("categorias", []):
                self.assertIn(categoria, CATALOGO, f"{coluna}: {categoria}")

    def test_fonte_licenca_e_hash_estao_no_catalogo(self):
        self.assertIn(FONTE_METADADOS["licenca"], CATALOGO)
        self.assertIn(SHA256_CSV_V1, CATALOGO)
        self.assertIn("genéricos de infraestrutura", CATALOGO)
        self.assertIn("amostra específica de data centers", CATALOGO)

    def test_stakeholder_documentado_como_fracao(self):
        linha = next(l for l in CATALOGO.splitlines() if l.startswith("| 10 |"))
        self.assertIn("0 a 1", linha)
        self.assertIn("0,50 a 1,00", linha)


if __name__ == "__main__":
    unittest.main()
