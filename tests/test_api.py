import os
import sys

# Garante que a pasta food-api esteja no caminho de imports do Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database
import models
from main import app

# 1. Configuração de um banco de dados em memória exclusivo para testes (não afeta o MySQL)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


# 2. Substituição da dependência get_db para usar o banco de testes isolado
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[database.get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_banco():
    # Cria as tabelas antes de cada teste e limpa depois
    models.Base.metadata.create_all(bind=engine_test)
    yield
    models.Base.metadata.drop_all(bind=engine_test)


# ========================================================
# TESTES DE STATUS E BOAS-VINDAS
# ========================================================

def test_status_api():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


# ========================================================
# TESTES DE CATEGORIAS
# ========================================================

def test_criar_e_listar_categoria():
    # 1. Criação
    res = client.post("/categorias/", json={"nome": "Lanches"})
    assert res.status_code == 201
    criada = res.json()
    assert criada["nome"] == "Lanches"
    assert "id" in criada

    # 2. Listagem
    res_list = client.get("/categorias/")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1


def test_erro_categoria_duplicada():
    client.post("/categorias/", json={"nome": "Bebidas"})
    # Tenta criar outra com o mesmo nome
    res = client.post("/categorias/", json={"nome": "Bebidas"})
    assert res.status_code == 400
    assert "Já existe uma categoria" in res.json()["detail"]


def test_buscar_categoria_nao_existente():
    res = client.get("/categorias/999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Categoria não encontrada"


# ========================================================
# TESTES DE PRODUTOS E RELACIONAMENTO
# ========================================================

def test_criar_produto_vinculado_a_categoria():
    # 1. Cria categoria
    cat_res = client.post("/categorias/", json={"nome": "Lanches"})
    cat_id = cat_res.json()["id"]

    # 2. Cria produto vinculado
    prod_res = client.post("/produtos/", json={
        "nome": "X-Burger Artesanal",
        "preco": 32.50,
        "categoria_id": cat_id
    })
    assert prod_res.status_code == 201
    prod = prod_res.json()
    assert prod["nome"] == "X-Burger Artesanal"
    assert prod["preco"] == 32.50
    assert prod["categoria_id"] == cat_id
    assert prod["categoria"]["nome"] == "Lanches"


def test_erro_criar_produto_com_categoria_inexistente():
    res = client.post("/produtos/", json={
        "nome": "Refrigerante",
        "preco": 8.00,
        "categoria_id": 999  # ID inexistente
    })
    assert res.status_code == 400
    assert "não existe" in res.json()["detail"]


def test_validacao_preco_invalido():
    # Preço zero ou negativo deve ser barrado pelo Pydantic (status 422)
    res = client.post("/produtos/", json={
        "nome": "Produto Grátis",
        "preco": -5.00
    })
    assert res.status_code == 422


def test_filtrar_produtos_por_categoria_e_busca():
    # Cria categorias
    cat_lanche = client.post("/categorias/", json={"nome": "Lanches"}).json()
    cat_bebida = client.post("/categorias/", json={"nome": "Bebidas"}).json()

    # Cria produtos
    client.post("/produtos/", json={"nome": "X-Salada", "preco": 25.0, "categoria_id": cat_lanche["id"]})
    client.post("/produtos/", json={"nome": "X-Bacon", "preco": 30.0, "categoria_id": cat_lanche["id"]})
    client.post("/produtos/", json={"nome": "Coca-Cola", "preco": 8.0, "categoria_id": cat_bebida["id"]})

    # 1. Filtra apenas bebidas
    res_bebidas = client.get(f"/produtos/?categoria_id={cat_bebida['id']}")
    assert len(res_bebidas.json()) == 1
    assert res_bebidas.json()[0]["nome"] == "Coca-Cola"

    # 2. Busca por texto
    res_busca = client.get("/produtos/?busca=Bacon")
    assert len(res_busca.json()) == 1
    assert res_busca.json()[0]["nome"] == "X-Bacon"


def test_editar_e_excluir_produto():
    prod = client.post("/produtos/", json={"nome": "Batata", "preco": 15.0}).json()
    prod_id = prod["id"]

    # Edição
    res_edit = client.put(f"/produtos/{prod_id}", json={"nome": "Batata Frita Especial", "preco": 18.0})
    assert res_edit.status_code == 200
    assert res_edit.json()["nome"] == "Batata Frita Especial"
    assert res_edit.json()["preco"] == 18.0

    # Exclusão
    res_del = client.delete(f"/produtos/{prod_id}")
    assert res_del.status_code == 204

    # Confirmação de que sumiu
    res_check = client.get(f"/produtos/{prod_id}")
    assert res_check.status_code == 404


def test_bloquear_exclusao_de_categoria_com_produtos():
    cat = client.post("/categorias/", json={"nome": "Sobremesas"}).json()
    client.post("/produtos/", json={"nome": "Pudim", "preco": 12.0, "categoria_id": cat["id"]})

    # Tenta excluir a categoria tendo produto vinculado
    res = client.delete(f"/categorias/{cat['id']}")
    assert res.status_code == 400
    assert "existem produtos vinculados" in res.json()["detail"]
