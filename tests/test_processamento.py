
import unittest
import pandas as pd

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from openpyxl import load_workbook

from processamento import (
    COLUNAS,
    preparar_dataframe,
    gerar_resumo,
    exportar_excel
)


class TestProcessamento(unittest.TestCase):

    # ========================================================
    # CONFIGURAÇÃO DOS DADOS DE TESTE
    # ========================================================

    def setUp(self):

        # Dados fictícios utilizados exclusivamente nos testes.
        self.registros = [
            {
                "codigo_ibge": "2611606",
                "municipio": "Recife",
                "uf": "PE",
                "regiao": "Nordeste",
                "prefeito": "Prefeito de teste",
                "gentilico": "recifense",
                "populacao_estimada": 3000,
                "ano_populacao": 2026,
                "area_km2": 20.0,
                "ano_area": 2025,
                "url_fonte": (
                    "https://www.ibge.gov.br/"
                    "cidades-e-estados/pe/recife.html"
                ),
                "data_coleta": "2026-11-25"
            },
            {
                "codigo_ibge": "2600401",
                "municipio": "Água Preta",
                "uf": "PE",
                "regiao": "Nordeste",
                "prefeito": "Prefeito de teste",
                "gentilico": "agua-pretense",
                "populacao_estimada": 1000,
                "ano_populacao": 2026,
                "area_km2": 10.0,
                "ano_area": 2025,
                "url_fonte": (
                    "https://www.ibge.gov.br/"
                    "cidades-e-estados/pe/agua-preta.html"
                ),
                "data_coleta": "2026-11-25"
            }
        ]

    # ========================================================
    # TESTE 1 - ESTRUTURA E TIPOS DE DADOS
    # ========================================================

    def test_estrutura_dataframe(self):

        df = preparar_dataframe(self.registros)

        self.assertEqual(
            list(df.columns),
            COLUNAS
        )

        self.assertEqual(len(df.columns), 12)
        self.assertEqual(len(df), 2)

        self.assertEqual(
            str(df["codigo_ibge"].dtype),
            "string"
        )

        self.assertEqual(
            str(df["populacao_estimada"].dtype),
            "Int64"
        )

        self.assertEqual(
            str(df["area_km2"].dtype),
            "Float64"
        )

        self.assertEqual(
            str(df["ano_populacao"].dtype),
            "Int64"
        )

        self.assertEqual(
            str(df["ano_area"].dtype),
            "Int64"
        )

    # ========================================================
    # TESTE 2 - ORDENAÇÃO E DUPLICIDADES
    # ========================================================

    def test_ordenacao_e_duplicidades(self):

        registros = self.registros.copy()

        # Adiciona um registro duplicado
        registros.append(self.registros[0].copy())

        df = preparar_dataframe(registros)

        self.assertEqual(len(df), 2)

        self.assertFalse(
            df["codigo_ibge"].duplicated().any()
        )

        self.assertEqual(
            df["municipio"].tolist(),
            ["Água Preta", "Recife"]
        )

    # ========================================================
    # TESTE 3 - CÓDIGO IBGE INVÁLIDO
    # ========================================================

    def test_codigo_ibge_invalido(self):

        registro = self.registros[0].copy()

        registro["codigo_ibge"] = "123"

        with self.assertRaises(ValueError):

            preparar_dataframe([registro])

    # ========================================================
    # TESTE 4 - TRATAMENTO DE DADOS AUSENTES
    # ========================================================

    def test_dados_ausentes(self):

        registro = self.registros[0].copy()

        registro["prefeito"] = ""
        registro["gentilico"] = ""
        registro["populacao_estimada"] = None
        registro["ano_populacao"] = None
        registro["area_km2"] = None
        registro["ano_area"] = None

        df = preparar_dataframe([registro])

        campos_ausentes = [
            "prefeito",
            "gentilico",
            "populacao_estimada",
            "ano_populacao",
            "area_km2",
            "ano_area"
        ]

        for campo in campos_ausentes:

            self.assertTrue(
                pd.isna(df.loc[0, campo])
            )

        # Confirma que os dados da API foram preservados
        self.assertEqual(
            df.loc[0, "municipio"],
            "Recife"
        )

        self.assertEqual(
            df.loc[0, "codigo_ibge"],
            "2611606"
        )

    # ========================================================
    # TESTE 5 - RESUMO ESTATÍSTICO
    # ========================================================

    def test_resumo_estatistico(self):

        df = preparar_dataframe(self.registros)

        df_resumo = gerar_resumo(df)

        resumo = dict(
            zip(
                df_resumo["Indicador"],
                df_resumo["Valor"]
            )
        )

        self.assertEqual(
            resumo["Municípios processados"],
            2
        )

        self.assertEqual(
            resumo["Registros completos"],
            2
        )

        self.assertEqual(
            resumo["Registros incompletos"],
            0
        )

        self.assertEqual(
            resumo["Percentual de registros completos"],
            1.0
        )

        self.assertEqual(
            resumo["População total (habitantes)"],
            4000
        )

        self.assertAlmostEqual(
            resumo["População média (habitantes)"],
            2000
        )

        self.assertAlmostEqual(
            resumo["Área territorial total (km²)"],
            30.0
        )

        self.assertAlmostEqual(
            resumo["Área territorial média (km²)"],
            15.0
        )

        self.assertEqual(
            resumo["Município mais populoso"],
            "Recife"
        )

        self.assertEqual(
            resumo["Município com maior área"],
            "Recife"
        )

        self.assertAlmostEqual(
            resumo["Densidade demográfica (hab/km²)"],
            4000 / 30
        )

    # ========================================================
    # TESTE 6 - DENSIDADE COM DADOS INCOMPLETOS
    # ========================================================

    def test_densidade_com_dados_ausentes(self):

        registros = [
            registro.copy()
            for registro in self.registros
        ]

        # Recife fica sem área territorial
        registros[0]["area_km2"] = None
        registros[0]["ano_area"] = None

        # Apenas Água Preta possui população e área.
        df = preparar_dataframe(registros)

        df_resumo = gerar_resumo(df)

        resumo = dict(
            zip(
                df_resumo["Indicador"],
                df_resumo["Valor"]
            )
        )

        self.assertEqual(
            resumo["Municípios utilizados na densidade"],
            1
        )

        self.assertAlmostEqual(
            resumo["Densidade demográfica (hab/km²)"],
            100.0
        )

        self.assertEqual(
            resumo["Registros incompletos"],
            1
        )

    # ========================================================
    # TESTE 7 - RESUMO SEM DADOS NUMÉRICOS
    # ========================================================

    def test_resumo_sem_dados_numericos(self):

        registro = self.registros[0].copy()

        registro["populacao_estimada"] = None
        registro["ano_populacao"] = None
        registro["area_km2"] = None
        registro["ano_area"] = None

        df = preparar_dataframe([registro])

        df_resumo = gerar_resumo(df)

        resumo = dict(
            zip(
                df_resumo["Indicador"],
                df_resumo["Valor"]
            )
        )

        indicadores = [
            "População total (habitantes)",
            "População média (habitantes)",
            "Área territorial total (km²)",
            "Área territorial média (km²)",
            "Densidade demográfica (hab/km²)"
        ]

        for indicador in indicadores:

            self.assertTrue(
                pd.isna(resumo[indicador])
            )

        self.assertEqual(
            resumo["Municípios utilizados na densidade"],
            0
        )

    # ========================================================
    # TESTE 8 - EXPORTAÇÃO PARA EXCEL
    # ========================================================

    def test_exportar_excel(self):

        # Cria uma pasta temporária para evitar alterações
        # na planilha oficial do projeto.
        with TemporaryDirectory() as pasta:

            with patch(
                "processamento.PASTA_OUTPUT",
                Path(pasta)
            ):

                caminho = exportar_excel(
                    self.registros,
                    "PE"
                )

                self.assertTrue(caminho.exists())

                self.assertEqual(
                    caminho.name,
                    "municipios_pe.xlsx"
                )

                arquivo = load_workbook(caminho)

                try:

                    # Confirma a existência das duas abas
                    self.assertEqual(
                        arquivo.sheetnames,
                        ["Municípios", "Resumo"]
                    )

                    municipios = arquivo["Municípios"]
                    resumo = arquivo["Resumo"]

                    # Valida linhas e colunas
                    self.assertEqual(
                        municipios.max_column,
                        12
                    )

                    self.assertEqual(
                        municipios.max_row,
                        3
                    )

                    # Confirma os cabeçalhos
                    self.assertEqual(
                        [
                            celula.value
                            for celula in municipios[1]
                        ],
                        COLUNAS
                    )

                    # Código IBGE armazenado como texto
                    self.assertEqual(
                        municipios["A2"].data_type,
                        "s"
                    )

                    # Confirma a ordenação
                    self.assertEqual(
                        municipios["B2"].value,
                        "Água Preta"
                    )

                    # Confirma o tipo numérico da população
                    self.assertEqual(
                        municipios["G2"].data_type,
                        "n"
                    )

                    # Confirma a existência do hyperlink
                    self.assertIsNotNone(
                        municipios["K2"].hyperlink
                    )

                    # Confirma o formato de data
                    self.assertTrue(
                        municipios["L2"].is_date
                    )

                    # Verifica os cálculos no arquivo Excel
                    indicadores = dict(
                        resumo.iter_rows(
                            min_row=2,
                            values_only=True
                        )
                    )

                    self.assertEqual(
                        indicadores[
                            "População total (habitantes)"
                        ],
                        4000
                    )

                    self.assertAlmostEqual(
                        indicadores[
                            "Área territorial total (km²)"
                        ],
                        30.0
                    )

                    self.assertAlmostEqual(
                        indicadores[
                            "Densidade demográfica (hab/km²)"
                        ],
                        4000 / 30
                    )

                finally:

                    arquivo.close()

    # ========================================================
    # TESTE 9 - UF INCOMPATÍVEL
    # ========================================================

    def test_uf_incompativel(self):

        with self.assertRaises(ValueError):

            exportar_excel(
                self.registros,
                "SP"
            )

    # ========================================================
    # TESTE 10 - REGISTROS VAZIOS
    # ========================================================

    def test_registros_vazios(self):

        with self.assertRaises(ValueError):

            preparar_dataframe([])


if __name__ == "__main__":
    unittest.main()

