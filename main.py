
from datetime import date

from ibge_api import listar_estados, listar_municipios

from portal import (
    gerar_url,
    capturar_html,
    extrair_dados_municipio
)

from processamento import exportar_excel

from config_logger import logger


# ============================================================
# 1. SELEÇÃO DO ESTADO
# ============================================================

def selecionar_estado(estados):
    """
    Permite selecionar um estado por número ou sigla.
    """

    if not estados:
        raise ValueError("Nenhum estado disponível.")

    print("\n===== ESTADOS BRASILEIROS =====\n")

    for numero, estado in enumerate(estados, start=1):

        print(
            f"{numero}. {estado['nome']} "
            f"({estado['uf']}) - {estado['regiao']}"
        )

    while True:

        escolha = input(
            "\nEscolha um estado (número ou UF): "
        ).strip()

        if escolha.isdecimal():

            numero = int(escolha)

            if 1 <= numero <= len(estados):
                return estados[numero - 1]

        else:

            estado = next(
                (
                    item for item in estados
                    if item["uf"] == escolha.upper()
                ),
                None
            )

            if estado:
                return estado

        print("Seleção inválida. Tente novamente.")

        logger.warning(
            "Tentativa de seleção inválida: %s",
            escolha
        )


# ============================================================
# 2. QUANTIDADE DE MUNICÍPIOS
# ============================================================

def solicitar_quantidade():
    """
    Solicita a quantidade de municípios.
    O limite padrão é cinco.
    """

    while True:

        quantidade = input(
            "\nQuantidade de municípios [5]: "
        ).strip()

        if not quantidade:
            return 5

        try:

            valor = int(quantidade)

            if valor > 0:
                return valor

            print("Informe uma quantidade maior que zero.")

            logger.warning(
                "Quantidade inválida: %s",
                quantidade
            )

        except ValueError:

            print("Digite uma quantidade inteira válida.")

            logger.warning(
                "Quantidade não numérica: %s",
                quantidade
            )


# ============================================================
# 3. COLETA DOS MUNICÍPIOS
# ============================================================

def coletar_municipio(municipio):
    """
    Combina os dados da API com os dados do portal.
    """

    uf = municipio["uf"]
    nome = municipio["municipio"]

    registro = {
        "codigo_ibge": municipio["codigo_ibge"],
        "municipio": nome,
        "uf": uf,
        "regiao": municipio["regiao"],
        "prefeito": "",
        "gentilico": "",
        "populacao_estimada": None,
        "ano_populacao": None,
        "area_km2": None,
        "ano_area": None,
        "url_fonte": "",
        "data_coleta": date.today().isoformat()
    }

    url = ""

    try:

        url = gerar_url(uf, nome)

        registro["url_fonte"] = url

        print(f"\nColetando: {nome} ({uf})")

        logger.info(
            "Iniciando coleta: %s (%s) | Código: %s | URL: %s",
            nome,
            uf,
            municipio["codigo_ibge"],
            url
        )

        # Navegação com Playwright
        resultado = capturar_html(url)

        logger.info(
            "Navegação concluída: %s | HTTP: %s",
            nome,
            resultado["status"]
        )

        # Extração com BeautifulSoup4
        dados_portal = extrair_dados_municipio(
            resultado["html"]
        )

        registro.update(dados_portal)

        registro["url_fonte"] = resultado["url_final"]

        # Identifica informações ausentes
        campos_ausentes = [
            campo
            for campo, valor in dados_portal.items()
            if valor is None or valor == ""
        ]

        if campos_ausentes:

            print("Coleta realizada parcialmente.")

            print(
                "Campos ausentes: "
                + ", ".join(campos_ausentes)
            )

            logger.warning(
                "Coleta parcial: %s (%s) | Campos ausentes: %s | URL: %s",
                nome,
                uf,
                ", ".join(campos_ausentes),
                url
            )

        else:

            print("Coleta realizada com sucesso!")

            logger.info(
                "Coleta completa: %s (%s)",
                nome,
                uf
            )

    except (RuntimeError, ValueError) as erro:

        registro["_erro_coleta"] = True

        print(f"Falha na coleta de {nome}: {erro}")

        print(f"URL: {url}")

        logger.error(
            "Falha na coleta: %s (%s) | URL: %s | Erro: %s",
            nome,
            uf,
            url,
            erro,
            exc_info=True
        )

    return registro


# ============================================================
# 4. EXECUÇÃO PRINCIPAL
# ============================================================

def executar():
    """
    Coordena todas as etapas da aplicação.
    """

    logger.info("=" * 60)
    logger.info("Iniciando nova execução do coletor IBGE")

    print("\n====================================")
    print("       COLETOR DE DADOS DO IBGE")
    print("====================================")

    try:

        # 1. Consulta os estados
        estados = listar_estados()

        logger.info(
            "UFs consultadas na API: %s",
            len(estados)
        )

        # 2. Seleciona o estado
        estado = selecionar_estado(estados)

        print(
            f"\nEstado selecionado: "
            f"{estado['nome']} ({estado['uf']})"
        )

        logger.info(
            "Estado selecionado: %s (%s)",
            estado["nome"],
            estado["uf"]
        )

        # 3. Solicita a quantidade
        limite = solicitar_quantidade()

        logger.info(
            "Quantidade solicitada: %s",
            limite
        )

        # 4. Consulta os municípios
        municipios = listar_municipios(
            estado["uf"],
            limite,
            estados=estados
        )

        print(f"\nQuantidade solicitada: {limite}")

        print(
            f"Municípios selecionados: {len(municipios)}"
        )

        logger.info(
            "UF: %s | Municípios selecionados: %s",
            estado["uf"],
            len(municipios)
        )

        if not municipios:

            print("Nenhum município disponível.")

            logger.warning(
                "Nenhum município disponível para coleta."
            )

            return []

        if len(municipios) < limite:

            print(
                "A quantidade disponível é inferior "
                "ao limite solicitado."
            )

            logger.warning(
                "Limite solicitado: %s | Disponíveis: %s",
                limite,
                len(municipios)
            )

        # 5. Realiza a coleta
        registros = []

        total = len(municipios)

        for indice, municipio in enumerate(
            municipios,
            start=1
        ):

            print(f"\nProgresso: {indice}/{total}")

            registro = coletar_municipio(municipio)

            registros.append(registro)

        # 6. Calcula os resultados
        coletas_completas = sum(
            1 for registro in registros
            if (
                registro["prefeito"]
                and registro["gentilico"]
                and registro["populacao_estimada"] is not None
                and registro["ano_populacao"] is not None
                and registro["area_km2"] is not None
                and registro["ano_area"] is not None
            )
        )

        coletas_incompletas = (
            len(registros) - coletas_completas
        )

        percentual_sucesso = (
            coletas_completas / len(registros)
        ) * 100

        # 7. Apresenta o resumo
        print("\n====================================")
        print("          RESUMO DA COLETA")
        print("====================================")

        print(f"UF selecionada: {estado['uf']}")

        print(
            f"Municípios processados: {len(registros)}"
        )

        print(
            f"Coletas completas: {coletas_completas}"
        )

        print(
            f"Coletas com dados ausentes ou falhas: "
            f"{coletas_incompletas}"
        )

        print(
            f"Percentual de coletas completas: "
            f"{percentual_sucesso:.2f}%"
        )

        logger.info(
            "Resumo | UF: %s | Processados: %s | "
            "Completos: %s | Incompletos: %s | Sucesso: %.2f%%",
            estado["uf"],
            len(registros),
            coletas_completas,
            coletas_incompletas,
            percentual_sucesso
        )

        # 8. Exporta para Excel
        print("\nPreparando os dados para exportação...")

        caminho_arquivo = exportar_excel(
            registros,
            estado["uf"]
        )

        logger.info(
            "Planilha exportada: %s",
            caminho_arquivo
        )

        print("\nProcesso concluído com sucesso!")

        logger.info(
            "Processo concluído. Coletas incompletas: %s",
            coletas_incompletas
        )

        return registros

    except PermissionError as erro:

        print(
            "\nErro de permissão ao gravar o arquivo."
        )

        print(
            "Verifique se o Excel está aberto."
        )

        logger.exception(
            "Erro de permissão: %s",
            erro
        )

        return []

    except (RuntimeError, ValueError, OSError) as erro:

        print(f"\nErro na execução: {erro}")

        logger.exception(
            "Erro durante a execução: %s",
            erro
        )

        return []

    except KeyboardInterrupt:

        print("\nExecução interrompida pelo usuário.")

        logger.warning(
            "Execução interrompida pelo usuário."
        )

        return []

    finally:

        logger.info("Execução encerrada.")
        logger.info("=" * 60)


# ============================================================
# 5. INICIALIZAÇÃO DO PROGRAMA
# ============================================================

if __name__ == "__main__":
    executar()
