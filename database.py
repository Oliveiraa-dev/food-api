import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Carrega as configurações do arquivo .env
load_dotenv()

# Configurações do banco de dados a partir de variáveis de ambiente
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "food_api")

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Liga o motor do banco de dados com tratamento de erro
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
except Exception as e:
    raise RuntimeError(
        f"Falha ao inicializar o motor do banco de dados: {e}. "
        f"Verifique as variáveis de ambiente em .env e certifique-se de que o MySQL está em execução."
    ) from e

# Fábrica de conversas com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Molde das tabelas
Base = declarative_base()

# Função que abre e fecha a conexão com o banco a cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
