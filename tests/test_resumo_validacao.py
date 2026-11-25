
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from openpyxl import load_workbook

from main import coletar_municipio
from processamento import exportar_excel


class TestResumoValidacao(unittest.TestCase):

    def test_resumo_com_falha_e_dados_ausentes(self):

        municipios = [
            {
                "codigo_ibge": "2600054",
                "municipio": "Abreu e Lima",
                "uf": "PE",
                "regiao": "Nordeste"
            },
            {
                "codigo_ibge": "2611606",
                "municipio": "Recife",
                "uf": "PE",
                "regiao": "Nordeste"
            }
        ]

        dados_parciais = {
            "prefeito": "",
            "gentilico": "recifense",
            "populacao_estimada": 1500000,
            "ano_populacao": 2026,
            "area_km2": 218.843,
            "ano_area": 2025
        }

        # Simula uma falha de navegação
        with patch("main.logger"), patch(
            "main.capturar_html",
            side_effect=RuntimeError("Falha simulada")
        ):

            registro_falha = coletar_municipio(
                municipios[0]
            )

        # Simula uma coleta parcial
        with patch("main.logger"), patch(
            "main.capturar_html",
            return_value={
                "status": 200,
                "titulo": "Recife (PE) | IBGE",
                "url_final": (
                    "https://www.ibge.gov.br/"
                    "cidades-e-estados/pe/recife.html"
                ),
                "html": "<html></html>"
            }
        ), patch(
            "main.extrair_dados_municipio",
            return_value=dados_parciais
        ):

            registro_parcial = coletar_municipio(
                municipios[1]
            )

        registros = [
            registro_falha,
            registro_parcial
        ]

        # Exporta para uma pasta temporária
        with TemporaryDirectory() as pasta:

            with patch(
                "processamento.PASTA_OUTPUT",
                Path(pasta)
            ):

                caminho = exportar_excel(
                    registros,
                    "PE"
                )

            workbook = load_workbook(caminho)

            try:

                planilha = workbook["Resumo"]

                resumo = dict(
                    planilha.iter_rows(
                        min_row=2,
                        values_only=True
                    )
                )

                self.assertEqual(
                    resumo["UF selecionada"], "PE"
                )

                self.assertEqual(
                    resumo["Municípios processados"], 2
                )

                self.assertEqual(
                    resumo["Registros completos"], 0
                )

                self.assertEqual(
                    resumo["Registros incompletos"], 2
                )

                self.assertEqual(
                    resumo["Falhas de coleta registradas"], 1
                )

                self.assertEqual(
                    resumo["Ausências: Prefeito"], 2
                )

                self.assertEqual(
                    resumo["Ausências: Gentílico"], 1
                )

                self.assertIn(
                    "Falha na coleta",
                    resumo["Pendência: Abreu e Lima (2600054)"]
                )

                self.assertIn(
                    "Campos ausentes: Prefeito",
                    resumo["Pendência: Recife (2611606)"]
                )

                self.assertEqual(
                    workbook["Municípios"].max_column,
                    12
                )

            finally:

                workbook.close()


if __name__ == "__main__":
    unittest.main()
