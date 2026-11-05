from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import produtos, categorias


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ciclo de vida da aplicação:
    # A criação e versionamento de tabelas é gerenciada exclusivamente pelo Alembic.
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
