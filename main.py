from fastapi import FastAPI
import database
import models
from routers import produtos, categorias

app = FastAPI(
    title="Food API",
    description="API para gerenciamento de cardápio, produtos e categorias integrada ao MySQL (XAMPP).",
    version="1.0.0",
)

# 1. Garante a criação automática das tabelas no banco de dados (MySQL)
models.Base.metadata.create_all(bind=database.engine)

# 2. Conecta as rotas dos módulos ao aplicativo principal
app.include_router(categorias.router)
app.include_router(produtos.router)


# Rota inicial de verificação da API
@app.get("/", tags=["Status"])
def status_api():
    return {
        "status": "online",
        "mensagem": "FoodAPI está rodando com sucesso no MySQL!",
        "docs": "/docs"
    }
