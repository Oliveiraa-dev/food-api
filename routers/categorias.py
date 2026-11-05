from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

import database
import models
import schemas

router = APIRouter(prefix="/categorias", tags=["Categorias"])


def get_categoria_db_or_404(db: Session, id: int) -> models.CategoriaDB:
    categoria = db.query(models.CategoriaDB).filter(models.CategoriaDB.id == id).first()
    if categoria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada"
        )
    return categoria


# 1. LISTAR TODAS AS CATEGORIAS
@router.get("/", response_model=list[schemas.CategoriaResponse])
def listar_categorias(db: Session = Depends(database.get_db)):
    return db.query(models.CategoriaDB).all()


# 2. BUSCAR CATEGORIA POR ID
@router.get("/{id}", response_model=schemas.CategoriaResponse)
def buscar_categoria(id: int, db: Session = Depends(database.get_db)):
    return get_categoria_db_or_404(db, id)


# 3. CRIAR NOVA CATEGORIA
@router.post("/", response_model=schemas.CategoriaResponse, status_code=status.HTTP_201_CREATED)
def criar_categoria(
    categoria: schemas.CategoriaCreate,
    db: Session = Depends(database.get_db),
):
    # Verifica se já existe categoria com esse nome
    existente = db.query(models.CategoriaDB).filter(models.CategoriaDB.nome == categoria.nome).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe uma categoria cadastrada com o nome '{categoria.nome}'."
        )

    nova_categoria = models.CategoriaDB(nome=categoria.nome)
    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria


# 4. EDITAR CATEGORIA
@router.put("/{id}", response_model=schemas.CategoriaResponse)
def editar_categoria(
    id: int,
    categoria: schemas.CategoriaCreate,
    db: Session = Depends(database.get_db),
):
    categoria_db = get_categoria_db_or_404(db, id)

    # Verifica se o novo nome já está em uso por OUTRA categoria
    duplicada = (
        db.query(models.CategoriaDB)
        .filter(models.CategoriaDB.nome == categoria.nome, models.CategoriaDB.id != id)
        .first()
    )
    if duplicada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe outra categoria com o nome '{categoria.nome}'."
        )

    categoria_db.nome = categoria.nome
    db.commit()
    db.refresh(categoria_db)
    return categoria_db


# 5. EXCLUIR CATEGORIA
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_categoria(id: int, db: Session = Depends(database.get_db)):
    categoria_db = get_categoria_db_or_404(db, id)

    # Verifica se existem produtos associados a esta categoria antes de excluir
    produtos_vinculados = (
        db.query(models.ProdutoDB)
        .filter(models.ProdutoDB.categoria_id == id)
        .first()
    )
    if produtos_vinculados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível excluir esta categoria porque existem produtos vinculados a ela."
        )

    db.delete(categoria_db)
    db.commit()

