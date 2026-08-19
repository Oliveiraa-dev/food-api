from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI()


class Produto(BaseModel):
    nome: str = Field(min_length=2, max_length=100) # min_length = tamanho mínimo / max_length=100 = tamanho máximo de caracteres
    preco: float = Field(gt=0) # greater than = maior que.


produtos = [  # memória temporária
    {
        "id": 1,
        "nome": "X-bacon",
        "preco": 29.90
    },
    {
        "id": 2,
        "nome": "X-salada",
        "preco": 25.90
    }
]


proximo_id = 3


@app.get("/")
def inicio():
    return {"mensagem": "FoodAPI está funcionando!"}


@app.get("/produtos")
def listar_produtos():
    return produtos

@app.get("/produtos/{id}")
def busar_produtos(id: int):

    for produto in produtos:

        if produto["id"] == id:
            return produto

    raise HTTPException(
        status_code=404,
        detail="Produto não encontrado"
    )

@app.post("/produtos")
def criar_produto(produto: Produto):
    global proximo_id

    novo_produto = {
        "id": proximo_id,
        "nome": produto.nome,
        "preco": produto.preco
    }

    produtos.append(novo_produto)

    proximo_id += 1

    return novo_produto


@app.put("/produtos/{id}")
def editar_produto(id: int, produto: Produto):
    for produto_existente in produtos:
         if produto_existente["id"] == id:
            produto_existente["nome"] = produto.nome
            produto_existente["preco"] = produto.preco

            return produto_existente

    raise HTTPException(
        status_code=404,
        detail="Produto não encontrado"
    )
         


@app.delete("/produtos/{id}") # funcao de delete
def excluir_produto(id: int):

    encontrou = False

    for produto in produtos: # para cada "produto" dentro da lista "produtos"

        if produto["id"] == id:
            encontrou = True
            produtos.remove(produto)

    if encontrou == False:
        raise HTTPException(
            status_code=404,
             detail="Produto não encontrado"
        )


