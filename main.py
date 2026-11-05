from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
import database
import models
from routers import produtos, categorias


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executado ao iniciar o servidor: cria as tabelas no MySQL se não existirem
    try:
        models.Base.metadata.create_all(bind=database.engine)
    except SQLAlchemyError as e:
        print(f"AVISO: Falha ao inicializar tabelas no banco de dados: {e}")
        print("Certifique-se de que o servidor MySQL (XAMPP) está ativo e acessível.")
    yield


app = FastAPI(
    title="Food API",
    description="API para gerenciamento de cardápio, produtos e categorias integrada ao MySQL (XAMPP).",
    version="1.0.0",
    lifespan=lifespan,
)

# Conecta as rotas dos módulos ao aplicativo principal
app.include_router(categorias.router)
app.include_router(produtos.router)


# Rota inicial de verificação da API
@app.get("/", tags=["Status"])
def status_api():
    return {
        "status": "online",
        "mensagem": "FoodAPI está rodando com sucesso no MySQL!",
        "docs": "/docs",
    }
