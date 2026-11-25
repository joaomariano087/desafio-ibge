
import unittest

from portal import (
    converter_inteiro_br,
    converter_decimal_br,
    extrair_dados_municipio,
    gerar_url,
    validar_pagina_municipio
)


class TestValidacaoPortal(unittest.TestCase):

    # ========================================================
    # TESTE 1 - NÚMEROS INTEIROS INVÁLIDOS
    # ========================================================

    def test_inteiros_malformados(self):

        valores = (
            "12,5",
            "abc123",
            "-12",
            "1.2.3",
            "1.00",
            ""
        )

        for valor in valores:

            with self.subTest(valor=valor):

                self.assertIsNone(
                    converter_inteiro_br(valor)
                )

    # ========================================================
    # TESTE 2 - NÚMEROS DECIMAIS INVÁLIDOS
    # ========================================================

    def test_decimais_malformados(self):

        valores = (
            "abc123",
            "-12,5",
            "1.2.3",
            "1,2,3",
            "12.34",
            ""
        )

        for valor in valores:

            with self.subTest(valor=valor):

                self.assertIsNone(
                    converter_decimal_br(valor)
                )

    # ========================================================
    # TESTE 3 - NÚMEROS VÁLIDOS
    # ========================================================

    def test_numeros_validos(self):

        self.assertEqual(
            converter_inteiro_br("0"),
            0
        )

        self.assertEqual(
            converter_inteiro_br("1.588.983"),
            1588983
        )

        self.assertEqual(
            converter_decimal_br("218,843"),
            218.843
        )

        self.assertEqual(
            converter_decimal_br("1.234,567"),
            1234.567
        )

        self.assertEqual(
            converter_decimal_br("100"),
            100.0
        )

    # ========================================================
    # TESTE 4 - INDICADORES INDISPONÍVEIS
    # ========================================================

    def test_indicadores_indisponiveis(self):

        html = """
        <div class="indicador">
            <div class="ind-label">
                Prefeito
            </div>

            <p class="ind-value">
                Não disponível
                <small>[2025]</small>
            </p>
        </div>

        <div class="indicador">
            <div class="ind-label">
                Gentílico
            </div>

            <p class="ind-value">
                —
            </p>
        </div>

        <div class="indicador">
            <div class="ind-label">
                População estimada
            </div>

            <p class="ind-value">
                12,5
                <small>[2026]</small>
            </p>
        </div>

        <div class="indicador">
            <div class="ind-label">
                Área Territorial
            </div>

            <p class="ind-value">
                Não informado
                <small>[2025]</small>
            </p>
        </div>
        """

        dados = extrair_dados_municipio(html)

        self.assertEqual(
            dados["prefeito"],
            ""
        )

        self.assertEqual(
            dados["gentilico"],
            ""
        )

        campos = (
            "populacao_estimada",
            "ano_populacao",
            "area_km2",
            "ano_area"
        )

        for campo in campos:

            self.assertIsNone(
                dados[campo]
            )

    # ========================================================
    # TESTE 5 - PÁGINA CORRETA
    # ========================================================

    def test_pagina_correta(self):

        url = gerar_url(
            "PE",
            "Água Preta"
        )

        validar_pagina_municipio(
            url,
            url,
            "Água Preta (PE) | Cidades e Estados | IBGE"
        )

    # ========================================================
    # TESTE 6 - REDIRECIONAMENTO PARA OUTRO MUNICÍPIO
    # ========================================================

    def test_url_redirecionada(self):

        url = gerar_url(
            "PE",
            "Recife"
        )

        with self.assertRaises(RuntimeError):

            validar_pagina_municipio(
                url,
                gerar_url("PE", "Olinda"),
                "Olinda (PE) | Cidades e Estados | IBGE"
            )

    # ========================================================
    # TESTE 7 - TÍTULO INCOMPATÍVEL
    # ========================================================

    def test_titulo_incompativel(self):

        url = gerar_url(
            "PE",
            "Recife"
        )

        titulos = (
            "Olinda (PE)",
            "Recife (BA)",
            "Portal IBGE"
        )

        for titulo in titulos:

            with self.subTest(titulo=titulo):

                with self.assertRaises(RuntimeError):

                    validar_pagina_municipio(
                        url,
                        url,
                        titulo
                    )


if __name__ == "__main__":

    unittest.main()
