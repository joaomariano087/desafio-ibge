
import logging

from pathlib import Path
from logging.handlers import RotatingFileHandler


# Define o diretório principal do projeto
BASE_DIR = Path(__file__).resolve().parent

# Define a pasta de logs
PASTA_LOGS = BASE_DIR / "logs"

# Cria a pasta automaticamente
PASTA_LOGS.mkdir(parents=True, exist_ok=True)

# Define o arquivo de logs
ARQUIVO_LOG = PASTA_LOGS / "coleta.log"


def configurar_logger():
    """
    Configura o sistema de logs da aplicação.
    """

    logger = logging.getLogger("coletor_ibge")

    logger.setLevel(logging.INFO)

    # Evita a duplicação de registros
    logger.propagate = False

    if logger.handlers:
        return logger

    # Define o formato das mensagens
    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S"
    )

    # Configura o armazenamento dos logs
    arquivo_handler = RotatingFileHandler(
        ARQUIVO_LOG,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )

    arquivo_handler.setLevel(logging.INFO)

    arquivo_handler.setFormatter(formato)

    logger.addHandler(arquivo_handler)

    return logger


# Disponibiliza o logger para os demais arquivos
logger = configurar_logger()
