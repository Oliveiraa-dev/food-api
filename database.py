from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Definimos o nome/caminho do arquivo do nosso banco de dados.
# O "sqlite:///./" significa que ele vai criar um arquivo na mesma pasta atual.
SQLALCHEMY_DATABASE_URL = "sqlite:///./banco_de_dados.db"

# 2. O "Engine" (Motor) é o responsável por fazer a conexão real com o banco de dados.
# Esse "check_same_thread": False é uma regra específica e necessária quando usamos SQLite com FastAPI.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Criamos uma "fábrica de sessões". Pense na sessão como uma conversa rápida 
# que a sua API tem com o banco de dados (para salvar ou ler algo) e depois desliga.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. A classe "Base" é o molde fundamental. Todos os nossos modelos (tabelas) 
# que vamos criar no próximo passo vão ser baseados nela.
Base = declarative_base()

# 5. Essa função será usada pelas nossas rotas para pedir uma conexão com o banco.
# Ela abre a porta (yield db), deixa a rota usar, e depois fecha a porta com segurança (db.close()).
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
