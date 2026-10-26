from fastapi import FastAPI

import database
import models
from routers import produtos

app = FastAPI()

# 1. Garante que as tabelas no banco SQLite sejam criadas
models.Base.metadata.create_all(bind=database.engine)

# 2. Conecta todas as rotas do nosso arquivo routers/produtos.py ao aplicativo
app.include_router(produtos.router)


# Rota inicial simples apenas para teste
@app.get("/")
def inicio():
    return {"mensagem": "FoodAPI está funcionando!"}