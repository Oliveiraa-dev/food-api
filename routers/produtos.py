from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import database
import models
import schemas

router = APIRouter(prefix="/produtos", tags=["Produtos"])


def get_produto_db_or_404(db: Session, id: int) -> models.ProdutoDB:
    produto = db.query(models.ProdutoDB).filter(models.ProdutoDB.id == id).first()
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    return produto


def validar_categoria_existente(db: Session, categoria_id: int | None):
    """Garante que o ID da categoria informado realmente existe no banco."""
    if categoria_id is not None:
        categoria = db.query(models.CategoriaDB).filter(models.CategoriaDB.id == categoria_id).first()
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A categoria com id {categoria_id} não existe."
            )


# 1. LISTAR PRODUTOS (Com suporte a paginação, ordenação, filtro por categoria e busca por nome)
@router.get("/", response_model=list[schemas.ProdutoResponse])
def listar_produtos(
    categoria_id: int | None = Query(default=None, description="Filtrar produtos por ID da categoria"),
    busca: str | None = Query(default=None, description="Buscar produtos por parte do nome"),
    skip: int = Query(default=0, ge=0, description="Número de registros a pular (paginação)"),
    limit: int = Query(default=10, ge=1, le=100, description="Número máximo de registros a retornar"),
    ordenar_por: str = Query(default="id", description="Campo para ordenação: 'id', 'nome' ou 'preco'"),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.ProdutoDB)

    if categoria_id is not None:
        query = query.filter(models.ProdutoDB.categoria_id == categoria_id)

    if busca:
        query = query.filter(models.ProdutoDB.nome.ilike(f"%{busca}%"))

    campos_ordenacao = {
        "id": models.ProdutoDB.id,
        "nome": models.ProdutoDB.nome,
        "preco": models.ProdutoDB.preco,
    }
    coluna = campos_ordenacao.get(ordenar_por)
    if coluna is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campo de ordenação inválido. Escolha entre: 'id', 'nome' ou 'preco'."
        )

    return query.order_by(coluna.asc()).offset(skip).limit(limit).all()


# 2. BUSCAR UM PRODUTO PELO ID
@router.get("/{id}", response_model=schemas.ProdutoResponse)
def buscar_produto(id: int, db: Session = Depends(database.get_db)):
    return get_produto_db_or_404(db, id)


# 3. CRIAR NOVO PRODUTO
@router.post("/", response_model=schemas.ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(
    produto: schemas.ProdutoCreate,
    db: Session = Depends(database.get_db),
):
    validar_categoria_existente(db, produto.categoria_id)

    produto_db = models.ProdutoDB(**produto.model_dump())
    db.add(produto_db)
    try:
        db.commit()
        db.refresh(produto_db)
        return produto_db
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao cadastrar produto. Verifique os dados informados."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no banco de dados ao salvar o produto."
        )


# 4. EDITAR PRODUTO
@router.put("/{id}", response_model=schemas.ProdutoResponse)
def editar_produto(
    id: int,
    produto: schemas.ProdutoCreate,
    db: Session = Depends(database.get_db),
):
    produto_db = get_produto_db_or_404(db, id)
    validar_categoria_existente(db, produto.categoria_id)

    produto_db.nome = produto.nome
    produto_db.preco = produto.preco
    produto_db.categoria_id = produto.categoria_id

    try:
        db.commit()
        db.refresh(produto_db)
        return produto_db
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao atualizar produto. Verifique os dados informados."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no banco de dados ao atualizar o produto."
        )


# 5. EXCLUIR PRODUTO
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_produto(id: int, db: Session = Depends(database.get_db)):
    produto_db = get_produto_db_or_404(db, id)
    try:
        db.delete(produto_db)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível excluir o produto devido a vínculos existentes no banco de dados."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no banco de dados ao excluir o produto."
        )
