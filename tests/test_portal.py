
import unittest

from portal import (
    normalizar_texto,
    gerar_slug,
    gerar_url,
    converter_inteiro_br,
    converter_decimal_br,
    extrair_dados_municipio
)


# ============================================================
# 1. TESTES DE NORMALIZAÇÃO E GERAÇÃO DE URL
# ============================================================

class TestGeracaoURL(unittest.TestCase):

    def test_normalizar_texto(self):
        self.assertEqual(
            normalizar_texto("População Estimada"),
            "populacao estimada"
        )

    def test_slug_simples(self):
        self.assertEqual(
            gerar_slug("Recife"),
            "recife"
        )

    def test_slug_com_acentos(self):
        self.assertEqual(
            gerar_slug("Afrânio"),
            "afranio"
        )

    def test_slug_nome_composto(self):
        self.assertEqual(
            gerar_slug("Água Preta"),
            "agua-preta"
        )

    def test_slug_nome_composto_com_acentos(self):
        self.assertEqual(
            gerar_slug("São José do Belmonte"),
            "sao-jose-do-belmonte"
        )

    def test_gerar_url(self):
        self.assertEqual(
            gerar_url("PE", "Recife"),
            "https://www.ibge.gov.br/"
            "cidades-e-estados/pe/recife.html"
        )

    def test_gerar_url_uf_invalida(self):
        with self.assertRaises(ValueError):
            gerar_url("PERNAMBUCO", "Recife")

    def test_gerar_url_municipio_vazio(self):
        with self.assertRaises(ValueError):
            gerar_url("PE", "")


# ============================================================
# 2. TESTES DE CONVERSÃO NUMÉRICA
# ============================================================

class TestConversaoNumerica(unittest.TestCase):

    def test_converter_inteiro(self):
        self.assertEqual(
            converter_inteiro_br("1.588.983"),
            1588983
        )

    def test_converter_inteiro_invalido(self):
        self.assertIsNone(
            converter_inteiro_br("Indisponível")
        )

    def test_converter_decimal(self):
        self.assertAlmostEqual(
            converter_decimal_br("218,843"),
            218.843
        )

    def test_converter_decimal_com_milhar(self):
        self.assertAlmostEqual(
            converter_decimal_br("1.491,572"),
            1491.572
        )

    def test_converter_decimal_invalido(self):
        self.assertIsNone(
            converter_decimal_br("Indisponível")
        )


# ============================================================
# 3. TESTES DE EXTRAÇÃO COM BEAUTIFULSOUP
# ============================================================

class TestExtracaoHTML(unittest.TestCase):

    def setUp(self):

        # HTML de teste baseado na estrutura
        # encontrada na página de Recife.

        self.html = """
        <html>
            <body>

                <div class="indicador">
                    <div class="ind-label">
                        <p>Prefeito</p>
                    </div>

                    <p class="ind-value">
                        JOÃO HENRIQUE DE ANDRADE LIMA CAMPOS
                        <small>[2025]</small>
                    </p>
                </div>

                <div class="indicador">
                    <div class="ind-label">
                        <p>Gentílico</p>
                    </div>

                    <p class="ind-value">
                        recifense
                    </p>
                </div>

                <div class="indicador">
                    <div class="ind-label">
                        <p>População estimada</p>
                    </div>

                    <p class="ind-value">
                        1.588.983

                        <span class="indicador-unidade">
                            pessoas
                        </span>

                        <small>[2026]</small>
                    </p>
                </div>

                <div class="indicador">
                    <div class="ind-label">
                        <p>Área Territorial</p>
                    </div>

                    <p class="ind-value">
                        218,843

                        <span class="indicador-unidade">
                            km²
                        </span>

                        <small>[2025]</small>
                    </p>
                </div>

            </body>
        </html>
        """

        self.dados = extrair_dados_municipio(
            self.html
        )

    def test_extrair_prefeito(self):
        self.assertEqual(
            self.dados["prefeito"],
            "JOÃO HENRIQUE DE ANDRADE LIMA CAMPOS"
        )

    def test_extrair_gentilico(self):
        self.assertEqual(
            self.dados["gentilico"],
            "recifense"
        )

    def test_extrair_populacao(self):
        self.assertEqual(
            self.dados["populacao_estimada"],
            1588983
        )

    def test_extrair_ano_populacao(self):
        self.assertEqual(
            self.dados["ano_populacao"],
            2026
        )

    def test_extrair_area(self):
        self.assertAlmostEqual(
            self.dados["area_km2"],
            218.843
        )

    def test_extrair_ano_area(self):
        self.assertEqual(
            self.dados["ano_area"],
            2025
        )

    def test_html_sem_indicadores(self):

        html = "<html><body></body></html>"

        dados = extrair_dados_municipio(html)

        self.assertEqual(dados["prefeito"], "")
        self.assertEqual(dados["gentilico"], "")

        self.assertIsNone(dados["populacao_estimada"])
        self.assertIsNone(dados["ano_populacao"])
        self.assertIsNone(dados["area_km2"])
        self.assertIsNone(dados["ano_area"])


# ============================================================
# 4. EXECUÇÃO DOS TESTES
# ============================================================

if __name__ == "__main__":
    unittest.main()
