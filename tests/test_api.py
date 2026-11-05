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

# 1. Configuração de um banco de dados SQLite em memória exclusivo para testes
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
    # Cria as tabelas antes de cada teste usando o engine de teste
    models.Base.metadata.create_all(bind=engine_test)
    yield
    # Limpa as tabelas após cada teste
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

    # 2. Listagem (ordenada por ID)
    res_list = client.get("/categorias/")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1
    assert res_list.json()[0]["nome"] == "Lanches"


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


def test_ordenacao_categorias():
    client.post("/categorias/", json={"nome": "Sobremesas"})
    client.post("/categorias/", json={"nome": "Acompanhamentos"})
    res = client.get("/categorias/")
    assert res.status_code == 200
    dados = res.json()
    assert len(dados) == 2
    assert dados[0]["id"] < dados[1]["id"]


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


def test_criar_produto_sem_categoria():
    # Produto sem categoria (categoria_id=None / nullable=True)
    prod_res = client.post("/produtos/", json={
        "nome": "Água Mineral",
        "preco": 4.50,
        "categoria_id": None
    })
    assert prod_res.status_code == 201
    prod = prod_res.json()
    assert prod["nome"] == "Água Mineral"
    assert prod["categoria_id"] is None
    assert prod["categoria"] is None


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

    res_zero = client.post("/produtos/", json={
        "nome": "Produto Zero",
        "preco": 0.00
    })
    assert res_zero.status_code == 422


def test_preco_decimal_precisao():
    # Testa representação decimal precisa (29.99)
    res = client.post("/produtos/", json={
        "nome": "X-Bacon Especial",
        "preco": 29.99
    })
    assert res.status_code == 201
    prod = res.json()
    assert prod["preco"] == 29.99

    # Busca pelo ID e valida novamente
    res_get = client.get(f"/produtos/{prod['id']}")
    assert res_get.status_code == 200
    assert res_get.json()["preco"] == 29.99


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

    # 2. Busca por texto (case-insensitive com ilike)
    res_busca = client.get("/produtos/?busca=bacon")
    assert len(res_busca.json()) == 1
    assert res_busca.json()[0]["nome"] == "X-Bacon"


def test_paginacao_produtos():
    # Cria 5 produtos
    for i in range(1, 6):
        client.post("/produtos/", json={"nome": f"Produto {i}", "preco": float(10 * i)})

    # Página 1: limit 2, skip 0 -> retorna os 2 primeiros (IDs 1, 2)
    res_p1 = client.get("/produtos/?skip=0&limit=2")
    assert res_p1.status_code == 200
    itens_p1 = res_p1.json()
    assert len(itens_p1) == 2
    assert itens_p1[0]["nome"] == "Produto 1"
    assert itens_p1[1]["nome"] == "Produto 2"

    # Página 2: limit 2, skip 2 -> retorna os 2 seguintes (IDs 3, 4)
    res_p2 = client.get("/produtos/?skip=2&limit=2")
    assert res_p2.status_code == 200
    itens_p2 = res_p2.json()
    assert len(itens_p2) == 2
    assert itens_p2[0]["nome"] == "Produto 3"
    assert itens_p2[1]["nome"] == "Produto 4"

    # Página 3: limit 2, skip 4 -> retorna o último (ID 5)
    res_p3 = client.get("/produtos/?skip=4&limit=2")
    assert res_p3.status_code == 200
    itens_p3 = res_p3.json()
    assert len(itens_p3) == 1
    assert itens_p3[0]["nome"] == "Produto 5"


def test_ordenacao_produtos():
    client.post("/produtos/", json={"nome": "X-Burger", "preco": 30.00})
    client.post("/produtos/", json={"nome": "Açaí", "preco": 15.00})
    client.post("/produtos/", json={"nome": "Pastel", "preco": 10.00})

    # Ordenação por ID (padrão)
    res_id = client.get("/produtos/?ordenar_por=id")
    assert res_id.status_code == 200
    nomes_por_id = [p["nome"] for p in res_id.json()]
    assert nomes_por_id == ["X-Burger", "Açaí", "Pastel"]

    # Ordenação por nome (alfabética)
    res_nome = client.get("/produtos/?ordenar_por=nome")
    assert res_nome.status_code == 200
    nomes_por_nome = [p["nome"] for p in res_nome.json()]
    assert nomes_por_nome == ["Açaí", "Pastel", "X-Burger"]

    # Ordenação por preço
    res_preco = client.get("/produtos/?ordenar_por=preco")
    assert res_preco.status_code == 200
    precos = [p["preco"] for p in res_preco.json()]
    assert precos == [10.00, 15.00, 30.00]

    # Ordenação inválida deve retornar 400
    res_invalida = client.get("/produtos/?ordenar_por=invalido")
    assert res_invalida.status_code == 400
    assert "Campo de ordenação inválido" in res_invalida.json()["detail"]


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

    # Confirmação de que foi excluído
    res_check = client.get(f"/produtos/{prod_id}")
    assert res_check.status_code == 404


def test_bloquear_exclusao_de_categoria_com_produtos():
    cat = client.post("/categorias/", json={"nome": "Sobremesas"}).json()
    client.post("/produtos/", json={"nome": "Pudim", "preco": 12.0, "categoria_id": cat["id"]})

    # Tenta excluir a categoria tendo produto vinculado
    res = client.delete(f"/categorias/{cat['id']}")
    assert res.status_code == 400
    assert "existem produtos vinculados" in res.json()["detail"]


def test_integridade_categoria_duplicada():
    # Cria a primeira vez
    res1 = client.post("/categorias/", json={"nome": "Bebidas Geladas"})
    assert res1.status_code == 201

    # Tenta criar novamente para testar restrição de unicidade e integridade
    res2 = client.post("/categorias/", json={"nome": "Bebidas Geladas"})
    assert res2.status_code == 400
    assert "Já existe uma categoria" in res2.json()["detail"]
