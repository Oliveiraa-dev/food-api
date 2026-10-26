
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

import database
import models
import schemas

router = APIRouter(prefix="/produtos", tags=["Produtos"])

def get_produto_db_or_404(db: Session, id: int):
    produto = db.query(models.ProdutoDB).filter(models.ProdutoDB.id == id).first()
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

# 1. LISTAR TODOS OS PRODUTOS
@router.get("/", response_model=list[schemas.ProdutoResponse])
def listar_produtos(db: Session = Depends(database.get_db)):
    return db.query(models.ProdutoDB).all()


# 2. BUSCAR UM PRODUTO PELO ID
@router.get("/{id}", response_model=schemas.ProdutoResponse)
def buscar_produtos(id: int, db: Session = Depends(database.get_db)):
    return get_produto_db_or_404(db, id)

# 3. CRIAR NOVO PRODUTO
@router.post("/", response_model=schemas.ProdutoResponse, status_code=201)
def criar_produto(
    produto: schemas.ProdutoCreate,
    db: Session = Depends(database.get_db),
):
    produto_db = models.ProdutoDB(**produto.model_dump())
    db.add(produto_db)
    db.commit()
    db.refresh(produto_db)
    return produto_db

# 4. EDITAR PRODUTO
@router.put("/{id}", response_model=schemas.ProdutoResponse)
def editar_produto(id: int, produto: schemas.ProdutoCreate, db: Session = Depends(database.get_db)):
    produto_db = get_produto_db_or_404(db, id)
    produto_db.nome = produto.nome
    produto_db.preco = produto.preco

    db.commit()
    db.refresh(produto_db)
    return produto_db


# 5. EXCLUIR PRODUTO
@router.delete("/{id}", status_code=204)
def excluir_produto(id: int, db: Session = Depends(database.get_db)):
    produto_db = get_produto_db_or_404(db, id)
    db.delete(produto_db)
    db.commit()