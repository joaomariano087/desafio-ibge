
import re
import unicodedata
import math

from urllib.parse import urlsplit
from bs4 import BeautifulSoup

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError
)


# ============================================================
# 1. NORMALIZAÇÃO DE TEXTOS
# ============================================================

def normalizar_texto(texto):
    """
    Remove acentos, espaços desnecessários e padroniza
    textos para facilitar comparações.
    """

    texto = unicodedata.normalize("NFD", str(texto))

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    return re.sub(
        r"\s+",
        " ",
        texto
    ).strip().rstrip(":").casefold()


# ============================================================
# 2. GERAÇÃO E VALIDAÇÃO DA URL DO MUNICÍPIO
# ============================================================

def gerar_slug(nome_municipio):
    """
    Transforma o nome do município em um formato
    adequado para compor a URL do portal do IBGE.
    """

    nome = unicodedata.normalize("NFD", nome_municipio)

    nome = "".join(
        caractere
        for caractere in nome
        if not unicodedata.combining(caractere)
    )

    nome = nome.lower().strip()

    # Remove apóstrofos
    nome = nome.replace("'", "").replace("’", "")

    # Substitui espaços e caracteres especiais por hífens
    nome = re.sub(r"[^a-z0-9]+", "-", nome)

    return nome.strip("-")


def gerar_url(uf, nome_municipio):
    """
    Gera automaticamente a URL da página do município.
    """

    if not isinstance(uf, str) or not re.fullmatch(
        r"[a-zA-Z]{2}", uf.strip()
    ):
        raise ValueError("Informe uma sigla de UF válida.")

    if (
        not isinstance(nome_municipio, str)
        or not nome_municipio.strip()
    ):
        raise ValueError("Informe o nome do município.")

    uf = uf.strip().lower()

    slug = gerar_slug(nome_municipio)

    if not slug:

        raise ValueError(
            "Nome de município inválido para gerar a URL."
        )

    return (
        f"https://www.ibge.gov.br/"
        f"cidades-e-estados/{uf}/{slug}.html"
    )


def validar_pagina_municipio(
    url_esperada,
    url_final,
    titulo
):
    """
    Confere se a URL final e o título correspondem
    ao município solicitado.
    """

    esperada = urlsplit(url_esperada)

    final = urlsplit(url_final)

    # Verifica o endereço acessado
    if (
        final.scheme != "https"
        or final.hostname != esperada.hostname
        or final.path != esperada.path
    ):

        raise RuntimeError(
            f"Página diferente da solicitada: {url_final}"
        )

    # Identifica a UF e o município na URL
    partes = esperada.path.strip("/").split("/")

    if (
        len(partes) != 3
        or partes[0] != "cidades-e-estados"
    ):

        raise RuntimeError(
            "URL do município não reconhecida."
        )

    uf, arquivo = partes[1:]

    # Formato esperado:
    # Recife (PE) | Cidades e Estados | IBGE

    correspondencia = re.match(
        r"^(.+?)\s*\(([A-Za-z]{2})\)\s*(?:\||$)",
        titulo.strip()
    )

    # Valida o nome do município e a UF
    if (
        not correspondencia
        or correspondencia.group(2).lower() != uf.lower()
        or gerar_slug(correspondencia.group(1)) + ".html"
        != arquivo
    ):

        raise RuntimeError(
            f"Título incompatível com o município "
            f"solicitado: {titulo}"
        )


# ============================================================
# 3. NAVEGAÇÃO COM PLAYWRIGHT
# ============================================================

def capturar_html(url):
    """
    Abre a página do município utilizando Playwright,
    aguarda o conteúdo relevante, recupera o HTML
    e encerra o navegador corretamente.
    """

    with sync_playwright() as playwright:

        navegador = None

        try:

            navegador = playwright.chromium.launch(
                headless=False
            )

            pagina = navegador.new_page()

            respostas_documento = []

            def registrar_resposta(resposta):

                if resposta.request.resource_type == "document":

                    respostas_documento.append(resposta)

            pagina.on("response", registrar_resposta)

            # Acessa a página do município
            resposta_inicial = pagina.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            # Aguarda o corpo da página
            pagina.locator("body").wait_for(
                state="visible",
                timeout=10000
            )

            status_inicial = (
                resposta_inicial.status
                if resposta_inicial
                else None
            )

            titulo = pagina.title()

            # Verifica eventual proteção de segurança
            if (
                status_inicial == 403
                or "just a moment" in titulo.lower()
            ):

                print(
                    "\nO portal apresentou uma "
                    "verificação de segurança."
                )

                print("Verifique a janela do navegador.")

                input(
                    "\nApós a interação normal com o portal, "
                    "pressione ENTER neste terminal..."
                )

                pagina.wait_for_timeout(1500)

            # Aguarda os indicadores da página
            try:

                pagina.locator(
                    "div.indicador"
                ).first.wait_for(
                    state="visible",
                    timeout=10000
                )

            except PlaywrightTimeoutError:
                pass

            titulo = pagina.title()

            # Identifica a resposta mais recente do documento
            resposta_final = next(
                (
                    resposta
                    for resposta in reversed(respostas_documento)
                    if resposta.url == pagina.url
                ),
                None
            )

            status = (
                resposta_final.status
                if resposta_final
                else status_inicial
            )

            # Captura o HTML renderizado
            html = pagina.content()

            # Verifica se a proteção continua ativa
            if "just a moment" in titulo.lower():

                raise RuntimeError(
                    "A verificação de segurança continua ativa."
                )

            # Verifica erros HTTP
            if status is not None and status >= 400:

                raise RuntimeError(
                    f"O portal retornou o status HTTP {status}."
                )

            # Verifica se o HTML está vazio
            if not html.strip():

                raise RuntimeError(
                    "O portal retornou um HTML vazio."
                )

            # Evita atribuir informações de outra página
            # ao código IBGE do município solicitado
            validar_pagina_municipio(
                url,
                pagina.url,
                titulo
            )

            return {
                "url": url,
                "url_final": pagina.url,
                "status": status,
                "titulo": titulo,
                "html": html
            }

        except PlaywrightTimeoutError as erro:

            raise RuntimeError(
                f"Tempo limite excedido ao acessar: {url}"
            ) from erro

        except PlaywrightError as erro:

            raise RuntimeError(
                f"Erro durante a navegação: {erro}"
            ) from erro

        finally:

            # Fecha o navegador independentemente do resultado
            if navegador is not None:

                navegador.close()


# ============================================================
# 4. CONVERSÃO DE NÚMEROS NO FORMATO BRASILEIRO
# ============================================================

def converter_inteiro_br(valor):
    """
    Aceita apenas números inteiros não negativos
    no formato brasileiro.

    Exemplo:
    1.588.983 -> 1588983
    """

    if not isinstance(valor, str):
        return None

    numero = valor.strip()

    # Valida a estrutura do número
    if not re.fullmatch(
        r"(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+)",
        numero
    ):

        return None

    try:

        return int(
            numero.replace(".", "")
        )

    except ValueError:

        return None


def converter_decimal_br(valor):
    """
    Aceita números não negativos com vírgula decimal
    e separadores de milhar válidos.

    Exemplos:
    218,843 -> 218.843
    1.234,567 -> 1234.567
    """

    if not isinstance(valor, str):

        return None

    numero = valor.strip()

    # Valida o formato brasileiro
    if not re.fullmatch(
        r"(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+)(?:,[0-9]+)?",
        numero
    ):

        return None

    try:

        resultado = float(
            numero.replace(".", "").replace(",", ".")
        )

        # Impede valores numéricos infinitos
        return (
            resultado
            if math.isfinite(resultado)
            else None
        )

    except (ValueError, OverflowError):

        return None


def limpar_valor_textual(valor):
    """
    Transforma marcadores conhecidos de indisponibilidade
    em textos vazios.
    """

    marcadores = {
        "",
        "-",
        "--",
        "–",
        "—",
        "...",
        "…",
        "n/a",
        "na",
        "null",
        "indisponivel",
        "nao disponivel",
        "nao informado",
        "nao informada",
        "sem informacao",
        "sem dados",
        "nao encontrado",
        "nao se aplica",
        "nao ha dados",
        "nao ha informacao",
        "nao consta"
    }

    texto = re.sub(
        r"\s+",
        " ",
        valor
    ).strip()

    if normalizar_texto(texto) in marcadores:

        return ""

    return texto


# ============================================================
# 5. EXTRAÇÃO DOS DADOS COM BEAUTIFULSOUP
# ============================================================

def extrair_dados_municipio(html):
    """
    Extrai as informações solicitadas no desafio
    a partir do HTML capturado pelo Playwright.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # Estrutura inicial dos dados
    dados = {
        "prefeito": "",
        "gentilico": "",
        "populacao_estimada": None,
        "ano_populacao": None,
        "area_km2": None,
        "ano_area": None
    }

    # Relaciona os rótulos do portal com os campos
    # que serão armazenados no DataFrame
    mapa_campos = {
        "prefeito": "prefeito",
        "gentilico": "gentilico",
        "populacao estimada": "populacao_estimada",
        "area territorial": "area_km2"
    }

    # Percorre todos os indicadores da página
    for indicador in soup.select("div.indicador"):

        rotulo_elemento = indicador.select_one(
            ".ind-label"
        )

        valor_elemento = indicador.select_one(
            ".ind-value"
        )

        if not rotulo_elemento or not valor_elemento:

            continue

        # Identifica o nome do indicador
        rotulo = normalizar_texto(
            rotulo_elemento.get_text(" ", strip=True)
        )

        campo = mapa_campos.get(rotulo)

        if campo is None:

            continue

        # Captura o ano de referência
        elemento_ano = valor_elemento.find("small")

        ano = None

        if elemento_ano:

            correspondencia = re.search(
                r"\b\d{4}\b",
                elemento_ano.get_text()
            )

            if correspondencia:

                ano = int(
                    correspondencia.group()
                )

        # Cria uma cópia do elemento para limpar o valor
        valor_limpo = BeautifulSoup(
            str(valor_elemento),
            "html.parser"
        )

        # Remove unidades e anos da cópia
        for elemento in valor_limpo.select(
            "small, .indicador-unidade"
        ):

            elemento.decompose()

        texto_valor = valor_limpo.get_text(
            " ",
            strip=True
        )

        # Tratamento individual de cada campo
        if campo == "prefeito":

            dados["prefeito"] = limpar_valor_textual(
                texto_valor
            )

        elif campo == "gentilico":

            dados["gentilico"] = limpar_valor_textual(
                texto_valor
            )

        elif campo == "populacao_estimada":

            dados["populacao_estimada"] = (
                converter_inteiro_br(texto_valor)
            )

            dados["ano_populacao"] = (
                ano
                if dados["populacao_estimada"] is not None
                else None
            )

        elif campo == "area_km2":

            dados["area_km2"] = (
                converter_decimal_br(texto_valor)
            )

            dados["ano_area"] = (
                ano
                if dados["area_km2"] is not None
                else None
            )

    return dados


# ============================================================
# 6. APRESENTAÇÃO DOS DADOS EXTRAÍDOS
# ============================================================

def exibir_dados(dados):
    """
    Apresenta os dados extraídos de maneira organizada.
    """

    print("\n===== DADOS EXTRAÍDOS =====")

    campos = {
        "prefeito": "Prefeito",
        "gentilico": "Gentílico",
        "populacao_estimada": "População estimada",
        "ano_populacao": "Ano da população",
        "area_km2": "Área territorial (km²)",
        "ano_area": "Ano da área"
    }

    for campo, descricao in campos.items():

        valor = dados.get(campo)

        if valor is None or valor == "":

            valor = "Não encontrado"

        print(f"{descricao}: {valor}")

    # Identifica os campos não encontrados
    ausentes = [
        descricao
        for campo, descricao in campos.items()
        if dados.get(campo) is None
        or dados.get(campo) == ""
    ]

    if ausentes:

        print("\nATENÇÃO: Campos não encontrados:")

        for campo in ausentes:

            print(f"- {campo}")


# ============================================================
# 7. EXECUÇÃO PRINCIPAL
# ============================================================

if __name__ == "__main__":

    print("\n===== TESTE DO PORTAL IBGE =====")

    try:

        # Recebe os dados do usuário
        uf = input(
            "Digite a UF: "
        ).strip().upper()

        municipio = input(
            "Digite o município: "
        ).strip()

        # Gera a URL automaticamente
        url = gerar_url(
            uf,
            municipio
        )

        print(f"\nURL gerada: {url}")

        print("\nAcessando o portal...")

        # Realiza a navegação com Playwright
        resultado = capturar_html(url)

        print("\n===== RESULTADO DA NAVEGAÇÃO =====")

        print(f"Status HTTP: {resultado['status']}")

        print(f"Título: {resultado['titulo']}")

        print(f"URL final: {resultado['url_final']}")

        print(
            f"Tamanho do HTML: "
            f"{len(resultado['html'])} caracteres"
        )

        print("\nPágina acessada com sucesso!")

        # Extrai os dados utilizando BeautifulSoup
        dados = extrair_dados_municipio(
            resultado["html"]
        )

        # Exibe os resultados
        exibir_dados(dados)

    except (RuntimeError, ValueError) as erro:

        print(f"\nErro: {erro}")
