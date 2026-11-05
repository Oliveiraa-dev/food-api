import importlib
import os
import sys
from decimal import Decimal

# Garante que a pasta food-api esteja no caminho de imports do Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

import database
import models
from main import app

# ==============================================================================
# CONFIGURAÇÃO DE TESTE ISOLADO COM SQLITE EM MEMÓRIA (NÃO ACESSA O MYSQL REAL)
# ==============================================================================
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


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
    # Cria as tabelas antes de cada teste usando o engine de teste isolado
    models.Base.metadata.create_all(bind=engine_test)
    yield
    # Limpa as tabelas após cada teste
    models.Base.metadata.drop_all(bind=engine_test)


# ==============================================================================
# 1. TESTES DE STATUS E ISOLAMENTO DE BANCO
# ==============================================================================

def test_status_api():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_garantia_isolamento_mysql():
    """Garante que a dependência get_db está sobreposta para o SQLite de teste."""
    assert app.dependency_overrides[database.get_db] is override_get_db
    # Valida que o engine de teste é SQLite em memória
    assert "sqlite" in str(engine_test.url)


# ==============================================================================
# 2. TESTES DE CATEGORIAS
# ==============================================================================

def test_criar_e_listar_categoria():
    res = client.post("/categorias/", json={"nome": "Lanches"})
    assert res.status_code == 201
    criada = res.json()
    assert criada["nome"] == "Lanches"
    assert "id" in criada

    res_list = client.get("/categorias/")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1
    assert res_list.json()[0]["nome"] == "Lanches"


def test_erro_categoria_duplicada():
    client.post("/categorias/", json={"nome": "Bebidas"})
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


def test_bloquear_exclusao_de_categoria_com_produtos():
    cat = client.post("/categorias/", json={"nome": "Sobremesas"}).json()
    client.post("/produtos/", json={"nome": "Pudim", "preco": "12.00", "categoria_id": cat["id"]})

    res = client.delete(f"/categorias/{cat['id']}")
    assert res.status_code == 400
    assert "existem produtos vinculados" in res.json()["detail"]


# ==============================================================================
# 3. TESTES DE PRODUTOS E PRECISÃO DECIMAL
# ==============================================================================

def test_criar_produto_vinculado_a_categoria():
    cat_res = client.post("/categorias/", json={"nome": "Lanches"})
    cat_id = cat_res.json()["id"]

    prod_res = client.post("/produtos/", json={
        "nome": "X-Burger Artesanal",
        "preco": "32.50",
        "categoria_id": cat_id
    })
    assert prod_res.status_code == 201
    prod = prod_res.json()
    assert prod["nome"] == "X-Burger Artesanal"
    assert Decimal(str(prod["preco"])) == Decimal("32.50")
    assert prod["categoria_id"] == cat_id
    assert prod["categoria"]["nome"] == "Lanches"


def test_criar_produto_sem_categoria():
    prod_res = client.post("/produtos/", json={
        "nome": "Água Mineral",
        "preco": "4.50",
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
        "preco": "8.00",
        "categoria_id": 999
    })
    assert res.status_code == 400
    assert "não existe" in res.json()["detail"]


def test_limites_casas_decimais():
    # 2 casas decimais: válido
    res_2casas = client.post("/produtos/", json={"nome": "Preço Exato", "preco": "29.99"})
    assert res_2casas.status_code == 201
    assert Decimal(str(res_2casas.json()["preco"])) == Decimal("29.99")

    # 1 casa decimal: válido
    res_1casa = client.post("/produtos/", json={"nome": "Preço Uma Casa", "preco": "15.5"})
    assert res_1casa.status_code == 201
    assert Decimal(str(res_1casa.json()["preco"])) == Decimal("15.50")

    # Inteiro: válido
    res_inteiro = client.post("/produtos/", json={"nome": "Preço Inteiro", "preco": "20"})
    assert res_inteiro.status_code == 201
    assert Decimal(str(res_inteiro.json()["preco"])) == Decimal("20.00")

    # Mais de 2 casas decimais (ex: 29.999): deve ser rejeitado (422)
    res_3casas = client.post("/produtos/", json={"nome": "Preço 3 Casas", "preco": "29.999"})
    assert res_3casas.status_code == 422

    # 4 casas decimais: deve ser rejeitado (422)
    res_4casas = client.post("/produtos/", json={"nome": "Preço 4 Casas", "preco": 10.1234})
    assert res_4casas.status_code == 422


def test_precos_valores_monetarios_diferentes():
    # Menor valor positivo válido (1 centavo)
    res_min = client.post("/produtos/", json={"nome": "Bala Avulsa", "preco": "0.01"})
    assert res_min.status_code == 201
    assert Decimal(str(res_min.json()["preco"])) == Decimal("0.01")

    # Valor monetário alto
    res_alto = client.post("/produtos/", json={"nome": "Banquete Completo", "preco": "99999.99"})
    assert res_alto.status_code == 201
    assert Decimal(str(res_alto.json()["preco"])) == Decimal("99999.99")

    # Preço zero: inválido (422)
    res_zero = client.post("/produtos/", json={"nome": "Brinde", "preco": "0.00"})
    assert res_zero.status_code == 422

    # Preço negativo: inválido (422)
    res_neg = client.post("/produtos/", json={"nome": "Desconto", "preco": "-5.50"})
    assert res_neg.status_code == 422


def test_editar_e_excluir_produto():
    prod = client.post("/produtos/", json={"nome": "Batata", "preco": "15.00"}).json()
    prod_id = prod["id"]

    res_edit = client.put(f"/produtos/{prod_id}", json={"nome": "Batata Frita Especial", "preco": "18.00"})
    assert res_edit.status_code == 200
    assert res_edit.json()["nome"] == "Batata Frita Especial"
    assert Decimal(str(res_edit.json()["preco"])) == Decimal("18.00")

    res_del = client.delete(f"/produtos/{prod_id}")
    assert res_del.status_code == 204

    res_check = client.get(f"/produtos/{prod_id}")
    assert res_check.status_code == 404


# ==============================================================================
# 4. TESTES DE PAGINAÇÃO, BUSCA E ORDENAÇÃO
# ==============================================================================

def test_paginacao_produtos():
    for i in range(1, 6):
        client.post("/produtos/", json={"nome": f"Produto {i}", "preco": f"{10 * i}.00"})

    # Página 1
    res_p1 = client.get("/produtos/?skip=0&limit=2")
    assert res_p1.status_code == 200
    itens_p1 = res_p1.json()
    assert len(itens_p1) == 2
    assert itens_p1[0]["nome"] == "Produto 1"
    assert itens_p1[1]["nome"] == "Produto 2"

    # Página 2
    res_p2 = client.get("/produtos/?skip=2&limit=2")
    assert res_p2.status_code == 200
    itens_p2 = res_p2.json()
    assert len(itens_p2) == 2
    assert itens_p2[0]["nome"] == "Produto 3"
    assert itens_p2[1]["nome"] == "Produto 4"

    # Página 3
    res_p3 = client.get("/produtos/?skip=4&limit=2")
    assert res_p3.status_code == 200
    itens_p3 = res_p3.json()
    assert len(itens_p3) == 1
    assert itens_p3[0]["nome"] == "Produto 5"


def test_paginacao_parametros_invalidos():
    # skip negativo (< 0) -> 422
    res_skip_neg = client.get("/produtos/?skip=-1")
    assert res_skip_neg.status_code == 422

    # limit zero (<= 0) -> 422
    res_limit_zero = client.get("/produtos/?limit=0")
    assert res_limit_zero.status_code == 422

    # limit acima do máximo permitido (> 100) -> 422
    res_limit_alto = client.get("/produtos/?limit=101")
    assert res_limit_alto.status_code == 422

    # skip não numérico -> 422
    res_skip_str = client.get("/produtos/?skip=invalido")
    assert res_skip_str.status_code == 422

    # limit não numérico -> 422
    res_limit_str = client.get("/produtos/?limit=abc")
    assert res_limit_str.status_code == 422


def test_ordenacao_produtos():
    client.post("/produtos/", json={"nome": "X-Burger", "preco": "30.00"})
    client.post("/produtos/", json={"nome": "Açaí", "preco": "15.00"})
    client.post("/produtos/", json={"nome": "Pastel", "preco": "10.00"})

    # Por ID
    res_id = client.get("/produtos/?ordenar_por=id")
    assert res_id.status_code == 200
    assert [p["nome"] for p in res_id.json()] == ["X-Burger", "Açaí", "Pastel"]

    # Por Nome
    res_nome = client.get("/produtos/?ordenar_por=nome")
    assert res_nome.status_code == 200
    assert [p["nome"] for p in res_nome.json()] == ["Açaí", "Pastel", "X-Burger"]

    # Por Preço
    res_preco = client.get("/produtos/?ordenar_por=preco")
    assert res_preco.status_code == 200
    assert [Decimal(str(p["preco"])) for p in res_preco.json()] == [Decimal("10.00"), Decimal("15.00"), Decimal("30.00")]

    # Campo inválido -> 400
    res_inv = client.get("/produtos/?ordenar_por=data_criacao")
    assert res_inv.status_code == 400
    assert "Campo de ordenação inválido" in res_inv.json()["detail"]


def test_busca_case_insensitive_e_filtros():
    client.post("/produtos/", json={"nome": "X-Bacon Supremo", "preco": "32.00"})
    client.post("/produtos/", json={"nome": "Suco de Laranja", "preco": "8.00"})

    # Minúsculo
    res_lower = client.get("/produtos/?busca=bacon")
    assert res_lower.status_code == 200
    assert len(res_lower.json()) == 1
    assert res_lower.json()[0]["nome"] == "X-Bacon Supremo"

    # Maiúsculo
    res_upper = client.get("/produtos/?busca=BACON")
    assert res_upper.status_code == 200
    assert len(res_upper.json()) == 1

    # Misto
    res_mixed = client.get("/produtos/?busca=BaCoN")
    assert res_mixed.status_code == 200
    assert len(res_mixed.json()) == 1

    # Busca sem correspondência
    res_vazio = client.get("/produtos/?busca=termo_inexistente_xyz")
    assert res_vazio.status_code == 200
    assert res_vazio.json() == []


# ==============================================================================
# 5. TESTES DE MIGRAÇÃO ALEMBIC (ISOLADOS EM BANCO TEMPORÁRIO)
# ==============================================================================

def test_migracao_alembic_banco_vazio():
    """Testa aplicação da migração inicial em um banco SQLite vazio."""
    migration = importlib.import_module("migrations.versions.50d5aa47f7e2_initial_schema")
    engine_temp = sa.create_engine("sqlite:///:memory:")

    with engine_temp.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            migration.upgrade()
            conn.commit()

        inspector = sa.inspect(conn)
        tables = inspector.get_table_names()
        assert "categorias" in tables
        assert "produtos" in tables

        cat_cols = {c["name"] for c in inspector.get_columns("categorias")}
        assert "id" in cat_cols
        assert "nome" in cat_cols

        prod_cols = {c["name"] for c in inspector.get_columns("produtos")}
        assert "id" in prod_cols
        assert "nome" in prod_cols
        assert "preco" in prod_cols
        assert "categoria_id" in prod_cols

        # Valida inserção no esquema gerado
        conn.execute(text("INSERT INTO categorias (id, nome) VALUES (1, 'Lanches')"))
        conn.execute(text("INSERT INTO produtos (id, nome, preco, categoria_id) VALUES (1, 'X-Burger', 25.50, 1)"))
        conn.commit()

        row = conn.execute(text("SELECT nome, preco FROM produtos WHERE id = 1")).fetchone()
        assert row[0] == "X-Burger"
        assert Decimal(str(row[1])) == Decimal("25.50")


def test_migracao_alembic_banco_com_dados_legados():
    """Testa aplicação da migração em banco que já possuía tabelas e dados pré-existentes."""
    migration = importlib.import_module("migrations.versions.50d5aa47f7e2_initial_schema")
    engine_temp = sa.create_engine("sqlite:///:memory:")

    with engine_temp.connect() as conn:
        # Simula estrutura legada: tabela produtos sem categoria_id e preco como FLOAT
        conn.execute(text("CREATE TABLE produtos (id INTEGER PRIMARY KEY, nome VARCHAR(100), preco FLOAT)"))
        conn.execute(text("INSERT INTO produtos (id, nome, preco) VALUES (1, 'Produto Legado', 19.90)"))
        conn.commit()

        # Executa migração
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            migration.upgrade()
            conn.commit()

        inspector = sa.inspect(conn)
        tables = inspector.get_table_names()
        assert "categorias" in tables
        assert "produtos" in tables

        # Confirma que categoria_id foi adicionada
        prod_cols = {c["name"] for c in inspector.get_columns("produtos")}
        assert "categoria_id" in prod_cols

        # Confirma preservação de dados
        rows = conn.execute(text("SELECT id, nome, preco, categoria_id FROM produtos")).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 1
        assert rows[0][1] == "Produto Legado"
        assert Decimal(str(rows[0][2])) == Decimal("19.90")
        assert rows[0][3] is None  # categoria_id nulo para legados
