
import unittest

from unittest.mock import patch

import httpx

from ibge_api import (
    URL_ESTADOS,
    URL_MUNICIPIOS,
    consultar_api,
    listar_estados,
    listar_municipios
)


class TestIBGEAPI(unittest.TestCase):

    def setUp(self):

        self.estados = [
            {
                "uf": "PE",
                "nome": "Pernambuco",
                "regiao": "Nordeste"
            }
        ]

        self.url = URL_MUNICIPIOS.format(uf="pe")


    # ========================================================
    # TESTE 1 - CONSULTA JSON VÁLIDA
    # ========================================================

    @patch("ibge_api.httpx.get")
    def test_consulta_json(self, get):

        get.return_value = httpx.Response(
            200,
            json=[{"id": 1}],
            request=httpx.Request("GET", URL_ESTADOS)
        )

        self.assertEqual(
            consultar_api(URL_ESTADOS),
            [{"id": 1}]
        )

        get.assert_called_once_with(
            URL_ESTADOS,
            timeout=15
        )


    # ========================================================
    # TESTE 2 - TIMEOUT
    # ========================================================

    @patch("ibge_api.httpx.get")
    def test_timeout(self, get):

        get.side_effect = httpx.ReadTimeout(
            "Timeout simulado"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Tempo limite"
        ):

            consultar_api(URL_ESTADOS)


    # ========================================================
    # TESTE 3 - ERRO HTTP
    # ========================================================

    @patch("ibge_api.httpx.get")
    def test_erro_http(self, get):

        get.return_value = httpx.Response(
            503,
            request=httpx.Request("GET", URL_ESTADOS)
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "503"
        ):

            consultar_api(URL_ESTADOS)


    # ========================================================
    # TESTE 4 - ERRO DE CONEXÃO
    # ========================================================

    @patch("ibge_api.httpx.get")
    def test_erro_conexao(self, get):

        get.side_effect = httpx.ConnectError(
            "Falha simulada"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "conectar"
        ):

            consultar_api(URL_ESTADOS)


    # ========================================================
    # TESTE 5 - JSON INVÁLIDO
    # ========================================================

    @patch("ibge_api.httpx.get")
    def test_json_invalido(self, get):

        get.return_value = httpx.Response(
            200,
            text="JSON inválido",
            request=httpx.Request("GET", URL_ESTADOS)
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "JSON"
        ):

            consultar_api(URL_ESTADOS)


    # ========================================================
    # TESTE 6 - LISTAGEM DOS ESTADOS
    # ========================================================

    @patch("ibge_api.consultar_api")
    def test_listar_estados(self, consulta):

        consulta.return_value = [
            {
                "sigla": "PE",
                "nome": "Pernambuco",
                "regiao": {"nome": "Nordeste"}
            },
            {
                "sigla": "AC",
                "nome": "Acre",
                "regiao": {"nome": "Norte"}
            },
            {
                "sigla": "PE",
                "nome": "Pernambuco",
                "regiao": {"nome": "Nordeste"}
            },
            {
                "sigla": 123,
                "nome": "Inválido"
            }
        ]

        estados = listar_estados()

        self.assertEqual(
            [e["uf"] for e in estados],
            ["AC", "PE"]
        )

        self.assertEqual(
            estados[1]["regiao"],
            "Nordeste"
        )


    # ========================================================
    # TESTE 7 - FORMATO DE RESPOSTA INESPERADO
    # ========================================================

    @patch(
        "ibge_api.consultar_api",
        return_value={"erro": "Formato incorreto"}
    )
    def test_formato_inesperado(self, consulta):

        with self.assertRaises(RuntimeError):

            listar_estados()

        with self.assertRaises(RuntimeError):

            listar_municipios(
                "PE",
                estados=self.estados
            )


    # ========================================================
    # TESTE 8 - MUNICÍPIOS, DUPLICIDADES E LIMITE
    # ========================================================

    @patch("ibge_api.listar_estados")
    @patch("ibge_api.consultar_api")
    def test_municipios_validos_e_limite(
        self,
        consulta,
        estados
    ):

        consulta.return_value = [
            {"id": 2611606, "nome": "Recife"},
            {"id": 2600401, "nome": "Água Preta"},
            {"id": 2600401, "nome": "Água Preta"},
            {"id": 123, "nome": "Inválido"},
            {"id": 2600203, "nome": "Afrânio"}
        ]

        resultado = listar_municipios(
            "pe",
            2,
            estados=self.estados
        )

        self.assertEqual(
            [m["municipio"] for m in resultado],
            ["Afrânio", "Água Preta"]
        )

        self.assertEqual(
            resultado[0]["codigo_ibge"],
            "2600203"
        )

        self.assertEqual(
            resultado[0]["regiao"],
            "Nordeste"
        )

        consulta.assert_called_once_with(
            self.url
        )

        estados.assert_not_called()

        resultado = listar_municipios(
            "PE",
            99,
            estados=self.estados
        )

        self.assertEqual(
            len(resultado),
            3
        )


    # ========================================================
    # TESTE 9 - LIMITE PADRÃO
    # ========================================================

    @patch("ibge_api.listar_estados")
    @patch("ibge_api.consultar_api")
    def test_limite_padrao(self, consulta, estados):

        estados.return_value = self.estados

        consulta.return_value = [
            {
                "id": 2600000 + i,
                "nome": f"Município {i}"
            }
            for i in range(6)
        ]

        self.assertEqual(
            len(listar_municipios("PE")),
            5
        )

        estados.assert_called_once()


    # ========================================================
    # TESTE 10 - ENTRADAS INVÁLIDAS
    # ========================================================

    @patch("ibge_api.consultar_api")
    def test_entradas_invalidas(self, consulta):

        for limite in (0, -2, True, 1.5, "5"):

            with self.subTest(limite=limite):

                with self.assertRaises(ValueError):

                    listar_municipios(
                        "PE",
                        limite,
                        estados=self.estados
                    )

        for uf in ("XX", "123", None):

            with self.subTest(uf=uf):

                with self.assertRaises(ValueError):

                    listar_municipios(
                        uf,
                        estados=self.estados
                    )

        consulta.assert_not_called()


if __name__ == "__main__":
    unittest.main()
