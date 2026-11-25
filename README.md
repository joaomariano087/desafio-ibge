
# Coletor de Dados Municipais do IBGE

Projeto desenvolvido para o desafio técnico de estágio em Desenvolvimento de Aplicações da QCA.

## Sobre o projeto

Aplicação desenvolvida em Python para automatizar a consulta, coleta, tratamento e exportação de informações sobre os municípios brasileiros.

O projeto integra o consumo de APIs REST, automação de navegação web, Web Scraping e processamento de dados, aplicando conceitos de Robotic Process Automation (RPA).

Os dados são obtidos da API de Localidades e do portal Cidades e Estados do IBGE, sendo organizados e exportados em planilhas Excel.

## Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem principal |
| httpx | Consumo da API REST |
| Playwright | Automação de navegação web |
| BeautifulSoup4 | Extração de dados HTML |
| pandas | Tratamento e análise de dados |
| openpyxl | Exportação e formatação do Excel |
| logging | Registro de operações e erros |
| unittest | Testes automatizados |
| unittest.mock | Simulação de comportamentos e falhas |

## Funcionalidades

- Consulta dinâmica das 27 unidades federativas brasileiras.
- Seleção de estado por número ou sigla.
- Ordenação alfabética dos municípios.
- Limite padrão de cinco municípios.
- Personalização da quantidade de registros.
- Validação das entradas do usuário.
- Validação dos códigos IBGE.
- Geração automática das URLs dos municípios.
- Normalização de acentos e nomes compostos.
- Navegação automatizada com Playwright.
- Validação da URL e do título da página acessada.
- Extração de indicadores com BeautifulSoup4.
- Validação de números no formato brasileiro.
- Tratamento de informações indisponíveis.
- Remoção de registros duplicados.
- Continuidade da coleta após falhas tratadas.
- Exportação de planilhas Excel formatadas.
- Geração de resumo estatístico.
- Detalhamento de falhas e campos ausentes.
- Sistema de logs com rotação automática.
- 50 testes automatizados.

## Estrutura do projeto

```text
desafio-ibge/
├── output/
│   ├── municipios_pe.xlsx
│   └── municipios_sp.xlsx
├── tests/
│   ├── __init__.py
│   ├── test_ibge_api.py
│   ├── test_main.py
│   ├── test_portal.py
│   ├── test_portal_validacao.py
│   └── test_processamento.py
├── config_logger.py
├── ibge_api.py
├── main.py
├── portal.py
├── processamento.py
├── requirements.txt
├── .gitignore
└── README.md
```

As pastas `venv/` e `logs/` são mantidas localmente e não são versionadas no Git.

## Arquitetura

O projeto utiliza uma arquitetura modular, separando as responsabilidades de cada etapa da automação.

| Arquivo | Responsabilidade |
|---|---|
| ibge_api.py | Comunicação com a API, validação e organização dos municípios |
| portal.py | Navegação, validação de páginas e extração dos indicadores |
| processamento.py | Tratamento dos dados, cálculos e exportação para Excel |
| config_logger.py | Configuração e gerenciamento dos logs |
| main.py | Coordenação do fluxo de execução |
| tests/ | Testes automatizados da aplicação |

## Fluxo de funcionamento

1. Consultar as unidades federativas na API do IBGE.
2. Apresentar os estados disponíveis.
3. Receber a UF e a quantidade desejada.
4. Consultar e ordenar os municípios.
5. Gerar as URLs das páginas individuais.
6. Acessar as páginas utilizando Playwright.
7. Validar a identidade da página acessada.
8. Capturar o HTML renderizado.
9. Extrair os indicadores utilizando BeautifulSoup4.
10. Combinar os dados da API e do portal.
11. Validar e tratar os registros utilizando pandas.
12. Gerar o resumo estatístico.
13. Exportar os resultados para Excel.
14. Registrar as operações nos logs.

## Instalação

### Pré-requisitos

- Python 3.14.3 (versão utilizada no desenvolvimento).
- Git.
- Conexão com a internet.
- Ambiente gráfico para execução do navegador Chromium.

O desafio permite Python 3.11 ou superior. Entretanto,
recomenda-se utilizar Python 3.14.3 para reproduzir o
ambiente com as versões fixadas no requirements.txt.

A compatibilidade com todas as versões anteriores
do Python não foi validada.

### 1. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
cd desafio-ibge
```

### 2. Criar o ambiente virtual

```bash
python -m venv venv
```

### 3. Ativar o ambiente virtual

Windows (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

Linux ou macOS:

```bash
source venv/bin/activate
```

### 4. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

### 5. Instalar o navegador Chromium

```bash
python -m playwright install chromium
```

### 6. Verificar as dependências

```bash
python -m pip check
```

## Como executar

Na pasta principal do projeto, execute:

```bash
python main.py
```

A aplicação apresentará uma lista das 27 unidades
federativas brasileiras.

Exemplo:

```text
Escolha um estado (número ou UF): PE
Quantidade de municípios [5]: 5
```

A seleção pode ser realizada pelo número apresentado
na lista ou pela sigla da unidade federativa.

Caso nenhuma quantidade seja informada, serão
selecionados cinco municípios.

Se a quantidade solicitada for superior à quantidade
disponível, a coleta será limitada aos registros existentes.

Os municípios são selecionados em ordem alfabética.

## Fontes de dados

### API de Localidades do IBGE

Consulta das unidades federativas:

https://servicodados.ibge.gov.br/api/v1/localidades/estados

Consulta dos municípios:

https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios

A API fornece os códigos IBGE, nomes dos municípios,
unidades federativas e informações regionais.

### Portal Cidades e Estados do IBGE

https://www.ibge.gov.br/cidades-e-estados.html

Exemplo de página:

https://www.ibge.gov.br/cidades-e-estados/pe/recife.html

O portal fornece os indicadores relacionados aos
prefeitos, gentílicos, população estimada e área territorial.

## Estrutura dos dados exportados

| Coluna | Descrição | Tipo |
|---|---|---|
| codigo_ibge | Código oficial de sete dígitos | Texto |
| municipio | Nome do município | Texto |
| uf | Sigla da unidade federativa | Texto |
| regiao | Região geográfica | Texto |
| prefeito | Nome do prefeito | Texto |
| gentilico | Gentílico do município | Texto |
| populacao_estimada | População estimada | Inteiro |
| ano_populacao | Ano de referência da população | Inteiro |
| area_km2 | Área territorial em km² | Decimal |
| ano_area | Ano de referência da área | Inteiro |
| url_fonte | Endereço da página consultada | Texto |
| data_coleta | Data da execução da coleta | Data |

Os dados são associados ao código IBGE de cada município,
evitando duplicidades na planilha final.

Informações indisponíveis são representadas por células
vazias, sem utilização de valores fictícios.

## Exportação dos resultados

Os arquivos são armazenados na pasta `output/`,
seguindo o padrão:

```text
municipios_{uf}.xlsx
```

Exemplos gerados:

```text
output/municipios_pe.xlsx
output/municipios_sp.xlsx
```

Cada arquivo possui duas abas.

### Aba Municípios

Contém os registros individuais, organizados em
12 colunas, com:

- Cabeçalho formatado.
- Filtros por coluna.
- Congelamento do cabeçalho.
- Linhas com cores alternadas.
- Códigos IBGE armazenados como texto.
- Formatação numérica.
- Datas formatadas.
- Links clicáveis para as páginas consultadas.

### Aba Resumo

Apresenta indicadores estatísticos e informações
relacionadas à qualidade da coleta:

- UF selecionada.
- Quantidade de municípios processados.
- Registros completos e incompletos.
- Falhas de coleta registradas.
- Percentual de registros completos.
- População total e média.
- Área territorial total e média.
- Município mais populoso.
- Município com maior área territorial.
- Densidade demográfica agregada.
- Quantidade de campos ausentes.
- Identificação dos municípios com pendências.

A densidade demográfica é calculada utilizando apenas
os municípios que possuem população e área disponíveis,
com área superior a zero.

Os indicadores representam exclusivamente os municípios
coletados, e não necessariamente todo o estado.

Os cálculos são realizados pelo Python durante a
exportação e não são recalculados automaticamente
após alterações manuais no Excel.

Uma nova execução para a mesma UF substitui o arquivo
anterior correspondente.

## Validação dos dados

A aplicação implementa mecanismos de validação para
reduzir inconsistências durante a coleta:

- Verificação dos códigos IBGE de sete dígitos.
- Validação das respostas recebidas da API.
- Remoção de municípios duplicados.
- Verificação da URL final e do título da página.
- Validação do formato brasileiro dos números.
- Tratamento de valores numéricos malformados.
- Identificação de marcadores de indisponibilidade.
- Preservação dos anos de referência.

Exemplos de conversão:

| Valor original | Resultado |
|---|---|
| 1.588.983 | 1588983 |
| 218,843 | 218.843 |
| 1.234,567 | 1234.567 |
| abc123 | Ausente |
| 1.2.3 | Ausente |
| Não informado | Ausente |

## Tratamento de erros

A aplicação possui tratamento para:

- Falhas de conexão.
- Erros HTTP.
- Timeouts.
- Respostas JSON inválidas.
- Estruturas de resposta inesperadas.
- Entradas inválidas.
- Páginas indisponíveis.
- Redirecionamentos incompatíveis.
- Falhas durante a navegação.
- Indicadores ausentes.
- Problemas de permissão na exportação.

Quando uma falha tratada ocorre durante a coleta
de um município, as informações disponíveis na API
são preservadas e a aplicação continua processando
os próximos registros.

As falhas e ausências são registradas nos logs e
apresentadas na aba Resumo.

## Sistema de logs

Os registros são armazenados automaticamente em:

```text
logs/coleta.log
```

O sistema registra:

- Data e horário das operações.
- Estado selecionado.
- Quantidade de municípios solicitados.
- URLs consultadas.
- Status HTTP das respostas.
- Coletas completas e parciais.
- Erros e avisos.
- Resultados da exportação.

Os arquivos utilizam codificação UTF-8 e rotação
automática, com limite de 5 MB e até três backups.

Para visualizar os logs no PowerShell:

```powershell
Get-Content .\logs\coleta.log -Encoding UTF8
```

Os arquivos de logs são gerados localmente e
não são enviados ao repositório.

## Testes automatizados

O projeto possui 50 testes automatizados,
desenvolvidos com unittest e unittest.mock.

| Arquivo | Testes |
|---|---:|
| test_ibge_api.py | 10 |
| test_main.py | 3 |
| test_portal.py | 20 |
| test_portal_validacao.py | 7 |
| test_processamento.py | 10 |
| Total | 50 |

Os testes contemplam:

- Consumo da API.
- Tratamento de erros HTTP.
- Timeouts e falhas de conexão.
- Respostas JSON inválidas.
- Validação das entradas.
- Ordenação e limites.
- Normalização de textos.
- Geração de URLs.
- Conversões numéricas.
- Extração de indicadores HTML.
- Validação da identidade das páginas.
- Tratamento de informações ausentes.
- Continuidade após falhas simuladas.
- Processamento de dados.
- Cálculos estatísticos.
- Exportação para Excel.

Para executar:

```bash
python -m unittest discover -s tests -v
```

Resultado obtido durante a validação:

```text
Ran 50 tests in 0.536s

OK
```

Os testes utilizam dados fictícios, exemplos de HTML,
mocks e arquivos temporários, evitando consultas
desnecessárias ao IBGE.

## Resultados obtidos

Foram realizadas coletas reais em Pernambuco
e São Paulo.

| UF | Municípios | Coletas completas | Falhas |
|---|---:|---:|---:|
| PE | 5 | 5 | 0 |
| SP | 3 | 3 | 0 |
| Total | 8 | 8 | 0 |

### Pernambuco

- Abreu e Lima
- Afogados da Ingazeira
- Afrânio
- Agrestina
- Água Preta

### São Paulo

- Adamantina
- Adolfo
- Aguaí

Os resultados correspondem às execuções realizadas
durante o desenvolvimento e não garantem a disponibilidade
permanente das fontes externas.

## Limitações conhecidas

- A aplicação depende da disponibilidade da API
  e do portal do IBGE.
- Alterações no HTML podem exigir ajustes nos
  seletores do BeautifulSoup4.
- Mudanças nos padrões de URLs e títulos podem
  exigir ajustes nas validações.
- Algumas páginas podem apresentar verificações
  de segurança.
- O navegador é executado em modo visível e pode
  solicitar interação manual com o portal.
- Caso a página permaneça indisponível, a falha
  é registrada e a coleta continua.
- Os indicadores podem possuir diferentes anos
  de referência.
- Os testes automatizados não abrangem todos os
  possíveis cenários de falhas externas.
- A execução completa foi validada no Windows.
  Outros ambientes gráficos não foram validados.

## Acesso responsável às fontes

As consultas são realizadas sequencialmente,
sem múltiplas navegações simultâneas.

A aplicação reutiliza os dados dos estados durante
a execução, evitando requisições redundantes.

Não são utilizadas técnicas para contornar
mecanismos de segurança do portal.

Os testes automatizados utilizam respostas simuladas
sempre que possível, reduzindo acessos desnecessários
às fontes externas.

## Considerações finais

O projeto demonstra a integração de ferramentas
Python para automatizar processos de consulta,
coleta, tratamento e exportação de dados.

A solução prioriza a organização modular,
a integridade das informações, o tratamento de falhas,
a manutenção do código e a reprodutibilidade.

## Autor

**João Mariano Leite Valadares**

Estudante de Ciência da Computação.

GitHub: https://github.com/joaomariano087

Projeto desenvolvido para o desafio técnico da QCA.
