from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# O endereço do XAMPP: usuário 'root', sem senha, no seu computador (localhost), banco 'food_api_db'
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost:3306/food_api_db"

# Liga o motor do banco de dados
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Fábrica de conversas com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Molde das tabelas
Base = declarative_base()

# Função que abre e fecha a porta do banco a cada requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()