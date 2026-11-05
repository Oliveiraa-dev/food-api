import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# ==============================================================================
# COMANDOS ÚTEIS DO ALEMBIC:
#
# 1. Gerar nova migração automaticamente com base nos modelos:
#    alembic revision --autogenerate -m "descricao_da_migracao"
#
# 2. Aplicar todas as migrações pendentes no banco de dados:
#    alembic upgrade head
#
# 3. Reverter a última migração aplicada:
#    alembic downgrade -1
#
# 4. Exibir histórico de migrações:
#    alembic history --verbose
#
# 5. Exibir a versão atual aplicada no banco:
#    alembic current
# ==============================================================================

# Adiciona o diretório raiz do projeto ao path de importação
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega as variáveis de ambiente do .env
load_dotenv()

# Importa a Base declarativa e a URL de conexão do database.py
from database import SQLALCHEMY_DATABASE_URL, Base
import models  # Garante o registro de todos os modelos

# Configuração do Alembic
config = context.config

# Define a URL de conexão dinamicamente pelo .env / database.py
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Configuração de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados alvo para a geração automática de revisões (autogenerate)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrações no modo 'offline'."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações no modo 'online'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
