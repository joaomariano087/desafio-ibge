
import unittest

from unittest.mock import patch

from main import coletar_municipio, executar


class TestColetaMunicipio(unittest.TestCase):

    def setUp(self):

        # Dados simulados da API do IBGE
        self.municipio = {
            "codigo_ibge": "2611606",
            "municipio": "Recife",
            "uf": "PE",
            "regiao": "Nordeste"
        }

        self.dados_portal = {
            "prefeito": "Prefeito de teste",
            "gentilico": "recifense",
            "populacao_estimada": 1588983,
            "ano_populacao": 2026,
            "area_km2": 218.843,
            "ano_area": 2025
        }

    # ========================================================
    # TESTE 1 - FALHA DE NAVEGAÇÃO
    # ========================================================

    @patch("main.logger")
    @patch("main.capturar_html")
    def test_falha_na_navegacao(
        self,
        mock_capturar,
        mock_logger
    ):

        # Simula uma falha no acesso ao portal
        mock_capturar.side_effect = RuntimeError(
            "Falha de conexão simulada"
        )

        resultado = coletar_municipio(
            self.municipio
        )

        # Verifica se os dados da API foram preservados
        self.assertEqual(
            resultado["codigo_ibge"],
            "2611606"
        )

        self.assertEqual(
            resultado["municipio"],
            "Recife"
        )

        self.assertEqual(resultado["uf"], "PE")
        self.assertEqual(resultado["regiao"], "Nordeste")

        # Verifica se os dados indisponíveis ficaram vazios
        self.assertEqual(resultado["prefeito"], "")
        self.assertEqual(resultado["gentilico"], "")

        self.assertIsNone(
            resultado["populacao_estimada"]
        )

        self.assertIsNone(resultado["ano_populacao"])
        self.assertIsNone(resultado["area_km2"])
        self.assertIsNone(resultado["ano_area"])

        # Verifica se a URL foi preservada
        self.assertEqual(
            resultado["url_fonte"],
            "https://www.ibge.gov.br/"
            "cidades-e-estados/pe/recife.html"
        )

        # Verifica se o erro foi registrado
        mock_logger.error.assert_called_once()


    # ========================================================
    # TESTE 2 - COLETA PARCIAL
    # ========================================================

    @patch("main.logger")
    @patch("main.extrair_dados_municipio")
    @patch("main.capturar_html")
    def test_coleta_parcial(
        self,
        mock_capturar,
        mock_extrair,
        mock_logger
    ):

        mock_capturar.return_value = {
            "html": "<html></html>",
            "status": 200,
            "url_final": (
                "https://www.ibge.gov.br/"
                "cidades-e-estados/pe/recife.html"
            )
        }

        # Simula informações indisponíveis
        dados_parciais = self.dados_portal.copy()

        dados_parciais["prefeito"] = ""
        dados_parciais["area_km2"] = None
        dados_parciais["ano_area"] = None

        mock_extrair.return_value = dados_parciais

        resultado = coletar_municipio(
            self.municipio
        )

        # Confirma os dados disponíveis
        self.assertEqual(
            resultado["gentilico"],
            "recifense"
        )

        self.assertEqual(
            resultado["populacao_estimada"],
            1588983
        )

        # Confirma os dados ausentes
        self.assertEqual(resultado["prefeito"], "")
        self.assertIsNone(resultado["area_km2"])
        self.assertIsNone(resultado["ano_area"])

        # Verifica se o aviso foi registrado
        mock_logger.warning.assert_called_once()


    # ========================================================
    # TESTE 3 - CONTINUIDADE APÓS UMA FALHA
    # ========================================================

    @patch("main.logger")
    @patch("main.exportar_excel")
    @patch("main.extrair_dados_municipio")
    @patch("main.capturar_html")
    @patch("main.listar_municipios")
    @patch("main.listar_estados")
    @patch("builtins.input", side_effect=["PE", "2"])
    def test_continuidade_apos_falha(
        self,
        mock_input,
        mock_estados,
        mock_municipios,
        mock_capturar,
        mock_extrair,
        mock_exportar,
        mock_logger
    ):

        mock_estados.return_value = [
            {
                "uf": "PE",
                "nome": "Pernambuco",
                "regiao": "Nordeste"
            }
        ]

        mock_municipios.return_value = [
            {
                "codigo_ibge": "2600054",
                "municipio": "Abreu e Lima",
                "uf": "PE",
                "regiao": "Nordeste"
            },
            self.municipio
        ]

        # A primeira coleta falha.
        # A segunda coleta funciona normalmente.
        mock_capturar.side_effect = [
            RuntimeError("Falha simulada"),
            {
                "html": "<html></html>",
                "status": 200,
                "url_final": (
                    "https://www.ibge.gov.br/"
                    "cidades-e-estados/pe/recife.html"
                )
            }
        ]

        mock_extrair.return_value = self.dados_portal

        mock_exportar.return_value = (
            "output/municipios_pe.xlsx"
        )

        registros = executar()

        # Verifica se os dois municípios foram processados
        self.assertEqual(len(registros), 2)

        self.assertEqual(
            mock_capturar.call_count,
            2
        )

        # Primeiro município: coleta indisponível
        self.assertIsNone(
            registros[0]["populacao_estimada"]
        )

        # Segundo município: coleta bem-sucedida
        self.assertEqual(
            registros[1]["populacao_estimada"],
            1588983
        )

        # Verifica se a exportação foi solicitada
        # mesmo após a primeira falha
        mock_exportar.assert_called_once_with(
            registros,
            "PE"
        )

        # Verifica se a falha foi registrada
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
