
import logging
import re
import unicodedata

import httpx


# ============================================================
# 1. CONFIGURAÇÕES DA API
# ============================================================

URL_ESTADOS = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
)

URL_MUNICIPIOS = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/"
    "estados/{uf}/municipios"
)

TIMEOUT = 15

logger = logging.getLogger("coletor_ibge.api")


# ============================================================
# 2. FUNÇÕES AUXILIARES
# ============================================================

def chave_alfabetica(texto):
    """
    Ordena textos desconsiderando acentos e maiúsculas.
    """

    texto = unicodedata.normalize("NFD", texto.casefold())

    return "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )


def texto_valido(valor):
    """
    Verifica se o valor é um texto não vazio.
    """

    return isinstance(valor, str) and bool(valor.strip())


# ============================================================
# 3. CONSULTA À API COM HTTPX
# ============================================================

def consultar_api(url):
    """
    Consulta a API e trata erros de comunicação e JSON.
    """

    try:

        resposta = httpx.get(
            url,
            timeout=TIMEOUT
        )

        resposta.raise_for_status()

        return resposta.json()

    except httpx.TimeoutException as erro:

        raise RuntimeError(
            "Tempo limite da API excedido."
        ) from erro

    except httpx.HTTPStatusError as erro:

        raise RuntimeError(
            f"Erro HTTP: {erro.response.status_code}"
        ) from erro

    except httpx.RequestError as erro:

        raise RuntimeError(
            f"Erro ao conectar com a API: {erro}"
        ) from erro

    except ValueError as erro:

        raise RuntimeError(
            "A API retornou uma resposta JSON inválida."
        ) from erro


# ============================================================
# 4. CONSULTA DOS ESTADOS
# ============================================================

def listar_estados():
    """
    Consulta e organiza as UFs e suas regiões.
    """

    dados = consultar_api(URL_ESTADOS)

    if not isinstance(dados, list):

        raise RuntimeError(
            "Formato de resposta dos estados inesperado."
        )

    estados = []
    siglas = set()

    for item in dados:

        if not isinstance(item, dict):

            logger.warning(
                "Registro de estado inválido ignorado."
            )

            continue

        uf = item.get("sigla")
        nome = item.get("nome")
        regiao = item.get("regiao")

        nome_regiao = (
            regiao.get("nome")
            if isinstance(regiao, dict)
            else None
        )

        # Validação dos campos obrigatórios
        if (
            not texto_valido(uf)
            or not re.fullmatch(r"[A-Za-z]{2}", uf.strip())
            or not texto_valido(nome)
            or not texto_valido(nome_regiao)
        ):

            logger.warning(
                "Estado com dados inválidos ignorado."
            )

            continue

        uf = uf.strip().upper()

        # Impede estados duplicados
        if uf in siglas:

            logger.warning(
                "UF duplicada ignorada: %s",
                uf
            )

            continue

        siglas.add(uf)

        estados.append({
            "uf": uf,
            "nome": nome.strip(),
            "regiao": nome_regiao.strip()
        })

    if not estados:

        raise RuntimeError(
            "Nenhum estado válido foi encontrado."
        )

    return sorted(
        estados,
        key=lambda item: chave_alfabetica(item["nome"])
    )


# ============================================================
# 5. CONSULTA DOS MUNICÍPIOS
# ============================================================

def listar_municipios(uf, limite=5, *, estados=None):
    """
    Retorna até o limite de municípios válidos,
    ordenados alfabeticamente e sem duplicidades.
    """

    # Valida a sigla
    if (
        not isinstance(uf, str)
        or not re.fullmatch(r"[A-Za-z]{2}", uf.strip())
    ):

        raise ValueError(
            "Informe uma sigla de UF válida."
        )

    # Valida a quantidade solicitada
    if (
        isinstance(limite, bool)
        or not isinstance(limite, int)
        or limite <= 0
    ):

        raise ValueError(
            "A quantidade deve ser um inteiro positivo."
        )

    uf = uf.strip().upper()

    # Reutiliza a lista de estados quando fornecida.
    # Evita uma nova requisição desnecessária.
    if estados is None:

        estados = listar_estados()

    estado = next(
        (
            item for item in estados
            if item["uf"] == uf
        ),
        None
    )

    if estado is None:

        raise ValueError(
            "Estado não encontrado."
        )

    # Consulta os municípios da UF selecionada
    url = URL_MUNICIPIOS.format(
        uf=uf.lower()
    )

    dados = consultar_api(url)

    if not isinstance(dados, list):

        raise RuntimeError(
            "Formato de municípios inválido."
        )

    municipios = []
    codigos = set()

    for item in dados:

        if not isinstance(item, dict):

            logger.warning(
                "Registro de município inválido ignorado: %s",
                url
            )

            continue

        codigo = item.get("id")
        nome = item.get("nome")

        # Aceita apenas códigos originalmente válidos
        # com exatamente sete dígitos.
        if (
            type(codigo) not in (int, str)
            or not re.fullmatch(r"[0-9]{7}", str(codigo))
            or not texto_valido(nome)
        ):

            logger.warning(
                "Município inválido ignorado: %r | URL: %s",
                item.get("id"),
                url
            )

            continue

        codigo = str(codigo)

        # Impede municípios duplicados
        if codigo in codigos:

            logger.warning(
                "Código IBGE duplicado ignorado: %s",
                codigo
            )

            continue

        codigos.add(codigo)

        municipios.append({
            "codigo_ibge": codigo,
            "municipio": nome.strip(),
            "uf": uf,
            "regiao": estado["regiao"]
        })

    if dados and not municipios:

        raise RuntimeError(
            "Nenhum município válido foi encontrado."
        )

    # Ordena os municípios alfabeticamente
    municipios.sort(
        key=lambda item: chave_alfabetica(
            item["municipio"]
        )
    )

    # Respeita o limite disponível
    return municipios[:limite]


# ============================================================
# 6. TESTE INDIVIDUAL DA API
# ============================================================

if __name__ == "__main__":

    try:

        print("\n===== CONSULTA DE MUNICÍPIOS =====")

        uf = input(
            "Digite a sigla do estado (ex: PE): "
        )

        municipios = listar_municipios(uf)

        for numero, item in enumerate(
            municipios,
            start=1
        ):

            print(
                f"{numero}. {item['municipio']} "
                f"| Código: {item['codigo_ibge']} "
                f"| UF: {item['uf']} "
                f"| Região: {item['regiao']}"
            )

        print(
            f"\nTotal processado: {len(municipios)}"
        )

    except (RuntimeError, ValueError) as erro:

        print(f"\nErro: {erro}")
