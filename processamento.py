
import pandas as pd

from pathlib import Path
from openpyxl.styles import Font, PatternFill, Alignment
from ibge_api import chave_alfabetica


# ============================================================
# 1. CONFIGURAÇÕES
# ============================================================

COLUNAS = [
    "codigo_ibge",
    "municipio",
    "uf",
    "regiao",
    "prefeito",
    "gentilico",
    "populacao_estimada",
    "ano_populacao",
    "area_km2",
    "ano_area",
    "url_fonte",
    "data_coleta"
]

CAMPOS_PORTAL = [
    "prefeito",
    "gentilico",
    "populacao_estimada",
    "ano_populacao",
    "area_km2",
    "ano_area"
]

PASTA_OUTPUT = Path(__file__).resolve().parent / "output"


# ============================================================
# 2. TRATAMENTO E VALIDAÇÃO DOS DADOS
# ============================================================

def preparar_dataframe(registros):
    """
    Transforma os registros em um DataFrame,
    organiza as colunas e valida os tipos.
    """

    if not registros:
        raise ValueError(
            "Nenhum registro disponível para exportação."
        )

    df = pd.DataFrame(
        registros,
        columns=COLUNAS
    )

    # Mantém o código IBGE como texto
    df["codigo_ibge"] = df["codigo_ibge"].astype("string")

    codigos_validos = df["codigo_ibge"].str.fullmatch(
        r"[0-9]{7}",
        na=False
    )

    if not codigos_validos.all():
        raise ValueError(
            "Foram encontrados códigos IBGE inválidos."
        )

    # Padroniza as colunas de texto
    colunas_texto = [
        "municipio",
        "uf",
        "regiao",
        "prefeito",
        "gentilico",
        "url_fonte"
    ]

    for coluna in colunas_texto:

        df[coluna] = (
            df[coluna]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    df["uf"] = df["uf"].str.upper()

    # Converte as colunas inteiras
    colunas_inteiras = [
        "populacao_estimada",
        "ano_populacao",
        "ano_area"
    ]

    for coluna in colunas_inteiras:

        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce"
        ).astype("Int64")

    # Converte a área territorial
    df["area_km2"] = pd.to_numeric(
        df["area_km2"],
        errors="coerce"
    ).astype("Float64")

    # Converte a data de coleta
    df["data_coleta"] = pd.to_datetime(
        df["data_coleta"],
        errors="coerce"
    ).dt.date

    # Remove duplicidades pelo código IBGE
    df = df.drop_duplicates(
        subset="codigo_ibge",
        keep="first"
    )

    # Ordena alfabeticamente
    df = df.sort_values(
        by="municipio",
        key=lambda coluna: coluna.map(chave_alfabetica)
    )

    return df.reset_index(drop=True)


# ============================================================
# 3. GERAÇÃO DO RESUMO ESTATÍSTICO
# ============================================================

def gerar_resumo(df, erros_por_codigo=None):
    """
    Calcula indicadores estatísticos e apresenta
    informações sobre a qualidade da coleta.
    """

    erros_por_codigo = erros_por_codigo or {}

    total_municipios = len(df)

    uf = df["uf"].iloc[0] if not df.empty else None

    # Identifica os registros completos
    registros_completos = int(
        df[CAMPOS_PORTAL].notna().all(axis=1).sum()
    )

    registros_incompletos = (
        total_municipios - registros_completos
    )

    percentual_completos = (
        registros_completos / total_municipios
        if total_municipios > 0
        else 0
    )

    # Identifica as falhas de coleta registradas
    total_falhas = sum(
        1 for codigo in df["codigo_ibge"]
        if erros_por_codigo.get(codigo, False)
    )

    # Quantidade de valores disponíveis
    municipios_com_populacao = int(
        df["populacao_estimada"].count()
    )

    municipios_com_area = int(
        df["area_km2"].count()
    )

    # Indicadores populacionais
    populacao_total = df["populacao_estimada"].sum(
        min_count=1
    )

    populacao_media = df["populacao_estimada"].mean()

    # Indicadores territoriais
    area_total = df["area_km2"].sum(
        min_count=1
    )

    area_media = df["area_km2"].mean()

    # Município mais populoso
    municipio_mais_populoso = None
    maior_populacao = None

    if municipios_com_populacao > 0:

        indice = df["populacao_estimada"].idxmax()

        municipio_mais_populoso = df.loc[
            indice, "municipio"
        ]

        maior_populacao = df.loc[
            indice, "populacao_estimada"
        ]

    # Município com maior área
    municipio_maior_area = None
    maior_area = None

    if municipios_com_area > 0:

        indice = df["area_km2"].idxmax()

        municipio_maior_area = df.loc[
            indice, "municipio"
        ]

        maior_area = df.loc[
            indice, "area_km2"
        ]

    # Seleciona municípios com população e área disponíveis
    dados_densidade = df.dropna(
        subset=["populacao_estimada", "area_km2"]
    )

    dados_densidade = dados_densidade[
        dados_densidade["area_km2"] > 0
    ]

    densidade_demografica = None

    if not dados_densidade.empty:

        densidade_demografica = (
            dados_densidade["populacao_estimada"].sum()
            / dados_densidade["area_km2"].sum()
        )

    # Organiza os indicadores
    resumo = [
        ("UF selecionada", uf),
        ("Municípios processados", total_municipios),
        ("Registros completos", registros_completos),
        ("Registros incompletos", registros_incompletos),
        ("Falhas de coleta registradas", total_falhas),
        ("Percentual de registros completos", percentual_completos),
        ("Municípios com população disponível", municipios_com_populacao),
        ("Municípios com área disponível", municipios_com_area),
        ("População total (habitantes)", populacao_total),
        ("População média (habitantes)", populacao_media),
        ("Área territorial total (km²)", area_total),
        ("Área territorial média (km²)", area_media),
        ("Município mais populoso", municipio_mais_populoso),
        ("Maior população (habitantes)", maior_populacao),
        ("Município com maior área", municipio_maior_area),
        ("Maior área territorial (km²)", maior_area),
        ("Municípios utilizados na densidade", len(dados_densidade)),
        ("Densidade demográfica (hab/km²)", densidade_demografica),
        (
            "Abrangência",
            "Somente os municípios coletados"
        ),
        (
            "Observação",
            "Os indicadores podem possuir anos de referência diferentes."
        )
    ]

    # ========================================================
    # QUALIDADE DOS DADOS
    # ========================================================

    nomes_campos = {
        "prefeito": "Prefeito",
        "gentilico": "Gentílico",
        "populacao_estimada": "População estimada",
        "ano_populacao": "Ano da população",
        "area_km2": "Área territorial",
        "ano_area": "Ano da área"
    }

    # Quantidade de informações ausentes por campo
    for campo in CAMPOS_PORTAL:

        quantidade_ausente = int(
            df[campo].isna().sum()
        )

        resumo.append((
            f"Ausências: {nomes_campos[campo]}",
            quantidade_ausente
        ))

    # Detalhamento dos municípios com problemas
    pendencias = 0

    for _, registro in df.iterrows():

        campos_ausentes = [
            nomes_campos[campo]
            for campo in CAMPOS_PORTAL
            if pd.isna(registro[campo])
        ]

        houve_falha = erros_por_codigo.get(
            registro["codigo_ibge"],
            False
        )

        if houve_falha or campos_ausentes:

            pendencias += 1

            detalhes = []

            if houve_falha:

                detalhes.append(
                    "Falha na coleta. Consulte logs/coleta.log."
                )

            if campos_ausentes:

                detalhes.append(
                    "Campos ausentes: "
                    + ", ".join(campos_ausentes)
                )

            resumo.append((
                f"Pendência: {registro['municipio']} "
                f"({registro['codigo_ibge']})",
                " | ".join(detalhes)
            ))

    if pendencias == 0:

        resumo.append((
            "Pendências identificadas",
            "Nenhuma"
        ))

    return pd.DataFrame(
        resumo,
        columns=["Indicador", "Valor"]
    )


# ============================================================
# 4. FORMATAÇÃO DAS PLANILHAS
# ============================================================

def formatar_planilha(planilha):
    """
    Aplica uma formatação visual ao Excel.
    """

    preenchimento = PatternFill(
        fill_type="solid",
        fgColor="17365D"
    )

    fonte_cabecalho = Font(
        bold=True,
        color="FFFFFF",
        size=11
    )

    # Formatação do cabeçalho
    for celula in planilha[1]:

        celula.fill = preenchimento

        celula.font = fonte_cabecalho

        celula.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    planilha.row_dimensions[1].height = 28

    # Congela o cabeçalho
    planilha.freeze_panes = "A2"

    # Adiciona filtros
    planilha.auto_filter.ref = planilha.dimensions

    # Oculta as linhas de grade
    planilha.sheet_view.showGridLines = False

    # Ajusta a largura das colunas
    for coluna in planilha.columns:

        letra = coluna[0].column_letter

        largura = max(
            len(str(celula.value))
            if celula.value is not None
            else 0
            for celula in coluna
        )

        planilha.column_dimensions[letra].width = min(
            largura + 4,
            75
        )

    preenchimento_alternado = PatternFill(
        fill_type="solid",
        fgColor="EDF3F8"
    )

    # Aplica cores alternadas nas linhas
    for linha in planilha.iter_rows(min_row=2):

        for celula in linha:

            celula.alignment = Alignment(
                vertical="center"
            )

            if celula.row % 2 == 0:

                celula.fill = preenchimento_alternado

        planilha.row_dimensions[linha[0].row].height = 21


# ============================================================
# 5. EXPORTAÇÃO PARA EXCEL
# ============================================================

def exportar_excel(registros, uf):
    """
    Exporta os dados municipais, indicadores estatísticos
    e informações sobre a qualidade da coleta.
    """

    df = preparar_dataframe(registros)

    uf = uf.strip().upper()

    if not df["uf"].eq(uf).fillna(False).all():

        raise ValueError(
            "Existem registros de uma UF diferente "
            "da selecionada."
        )

    # Preserva as falhas associadas aos códigos IBGE.
    # Mantém a primeira ocorrência, assim como o DataFrame.
    erros_por_codigo = {}

    for registro in registros:

        erros_por_codigo.setdefault(
            str(registro["codigo_ibge"]),
            bool(registro.get("_erro_coleta", False))
        )

    df_resumo = gerar_resumo(
        df,
        erros_por_codigo
    )

    PASTA_OUTPUT.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho_arquivo = (
        PASTA_OUTPUT / f"municipios_{uf.lower()}.xlsx"
    )

    with pd.ExcelWriter(
        caminho_arquivo,
        engine="openpyxl",
        date_format="DD/MM/YYYY"
    ) as writer:

        # Aba 1 - Municípios
        df.to_excel(
            writer,
            sheet_name="Municípios",
            index=False,
            na_rep=""
        )

        # Aba 2 - Resumo
        df_resumo.to_excel(
            writer,
            sheet_name="Resumo",
            index=False,
            na_rep=""
        )

        planilha_municipios = writer.sheets["Municípios"]
        planilha_resumo = writer.sheets["Resumo"]

        formatar_planilha(planilha_municipios)
        formatar_planilha(planilha_resumo)

        # Código IBGE como texto
        for celula in planilha_municipios["A"][1:]:

            celula.number_format = "@"

        # População como inteiro
        for celula in planilha_municipios["G"][1:]:

            celula.number_format = "#,##0"

        # Área territorial como decimal
        for celula in planilha_municipios["I"][1:]:

            celula.number_format = "#,##0.000"

        # Formatação das datas
        for celula in planilha_municipios["L"][1:]:

            celula.number_format = "DD/MM/YYYY"

        # Links clicáveis
        for celula in planilha_municipios["K"][1:]:

            if celula.value:

                celula.hyperlink = celula.value

                celula.font = Font(
                    color="0563C1",
                    underline="single"
                )

        # Formatação dos indicadores
        formatos_resumo = {
            "Percentual de registros completos": "0.00%",
            "População total (habitantes)": "#,##0",
            "População média (habitantes)": "#,##0.00",
            "Maior população (habitantes)": "#,##0",
            "Área territorial total (km²)": "#,##0.000",
            "Área territorial média (km²)": "#,##0.000",
            "Maior área territorial (km²)": "#,##0.000",
            "Densidade demográfica (hab/km²)": "#,##0.00"
        }

        planilha_resumo.column_dimensions["A"].width = 55
        planilha_resumo.column_dimensions["B"].width = 75

        for linha in planilha_resumo.iter_rows(min_row=2):

            indicador = linha[0].value

            linha[0].font = Font(bold=True)

            if indicador in formatos_resumo:

                linha[1].number_format = (
                    formatos_resumo[indicador]
                )

            # Destaca os indicadores de qualidade
            if (
                indicador.startswith("Ausências:")
                or indicador == "Falhas de coleta registradas"
            ):

                if linha[1].value > 0:

                    linha[1].fill = PatternFill(
                        fill_type="solid",
                        fgColor="FFF2CC"
                    )

                    linha[1].font = Font(
                        bold=True,
                        color="9C5700"
                    )

            # Formata textos explicativos e pendências
            if (
                indicador == "Observação"
                or indicador.startswith("Pendência:")
            ):

                for celula in linha:

                    celula.alignment = Alignment(
                        wrap_text=True,
                        vertical="center"
                    )

                planilha_resumo.row_dimensions[
                    linha[0].row
                ].height = 60

    print("\n===== EXPORTAÇÃO CONCLUÍDA =====")

    print(f"Arquivo gerado: {caminho_arquivo}")
    print(f"Municípios exportados: {len(df)}")
    print("Abas geradas: Municípios e Resumo")

    return caminho_arquivo
