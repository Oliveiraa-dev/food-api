# FoodAPI 🍔🍕🥤

API RESTful moderna e robusta para gerenciamento de cardápio, produtos e categorias de restaurantes/lanchonetes, desenvolvida com **FastAPI**, **SQLAlchemy** e integrada ao banco de dados **MySQL** (via XAMPP).

---

## 🎯 Objetivo

Fornecer um backend performático, seguro e bem estruturado para o controle completo de produtos alimentícios e suas respectivas categorias, com validações de integridade, suporte a valores monetários de alta precisão (Decimal), paginação de registros, busca dinâmica e gerenciamento de migrações de banco de dados.

---

## 🛠️ Tecnologias Utilizadas

- **[FastAPI](https://fastapi.tiangolo.com/)**: Framework web assíncrono de alto desempenho para construção de APIs em Python.
- **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)**: ORM padrão da indústria para modelagem e mapeamento de dados relacionais.
- **[MySQL (XAMPP)](https://www.apachefriends.org/)**: Sistema gerenciador de banco de dados relacional.
- **[PyMySQL](https://pymysql.readthedocs.io/) & [Cryptography](https://cryptography.io/)**: Driver de conexão seguro entre Python e MySQL.
- **[Pydantic v2](https://docs.pydantic.dev/)**: Validação estrita de tipos, regras de negócio e serialização JSON.
- **[Alembic](https://alembic.sqlalchemy.org/)**: Controle de versionamento e migrações do esquema do banco de dados.
- **[python-dotenv](https://github.com/theskumar/python-dotenv)**: Gerenciamento seguro de configurações via variáveis de ambiente.
- **[Pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/)**: Suíte de testes automatizados com banco isolado em memória (SQLite).
- **[Uvicorn](https://www.uvicorn.org/)**: Servidor ASGI rápido para execução da aplicação.

---

## ✨ Funcionalidades

- **Gerenciamento de Categorias**:
  - Cadastro de categorias com validação de unicidade de nome.
  - Listagem ordenada por ID.
  - Consulta por ID com tratamento amigável de erro (404).
  - Edição com validação contra nomes duplicados em outras categorias.
  - Exclusão protegida (impede exclusão se houver produtos vinculados).
- **Gerenciamento de Produtos**:
  - Cadastro de produtos com preço monetário exato (`Decimal(10, 2)` / `gt=0`).
  - Vinculação a categorias com validação de chave estrangeira existente (permite produtos sem categoria).
  - Listagem com **paginação** (`skip` e `limit`).
  - Ordenação dinâmica por `id`, `nome` ou `preco`.
  - Filtro por ID de categoria.
  - Busca por nome com correspondência *case-insensitive* (`ilike`).
  - Edição e remoção de produtos com transações seguras (`rollback` em erros).
- **Arquitetura Resiliente**:
  - Gerenciamento de ciclo de vida (`lifespan`) para inicialização de tabelas sem bloqueio em imports.
  - Isolamento completo do ambiente de testes via banco de dados SQLite em memória (`:memory:`).

---

## 📂 Estrutura de Pastas

```text
food-api/
├── migrations/                 # Migrações do banco de dados (Alembic)
│   ├── versions/               # Histórico de revisões das migrações
│   └── env.py                  # Configuração do ambiente Alembic
├── routers/                    # Módulos de rotas da aplicação
│   ├── __init__.py
│   ├── categorias.py           # Endpoints de categorias
│   └── produtos.py             # Endpoints de produtos
├── tests/                      # Suíte de testes automatizados
│   └── test_api.py             # Testes unitários e de integração
├── .env                        # Variáveis de ambiente locais (ignorado no git)
├── .env.example                # Exemplo de configuração de variáveis
├── .gitignore                  # Arquivos e pastas ignorados pelo controle de versão
├── alembic.ini                 # Arquivo de configuração do Alembic
├── database.py                 # Conexão com o banco de dados e sessão SQLAlchemy
├── main.py                     # Ponto de entrada FastAPI e ciclo de vida da API
├── models.py                   # Modelos relacionais ORM (SQLAlchemy)
├── requirements.txt            # Dependências do projeto
├── schemas.py                  # Modelos Pydantic (validação de entrada e saída)
└── README.md                   # Documentação do projeto
```

---

## 🚀 Instalação e Configuração

### 1. Pré-requisitos

- Python 3.10 ou superior instalado.
- [XAMPP](https://www.apachefriends.org/) instalado com o serviço **MySQL** ativo.

### 2. Configurar o Ambiente Virtual

No diretório raiz do projeto:

```powershell
# Criação do ambiente virtual (caso ainda não exista)
python -m venv .venv

# Ativação no Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Ativação no Linux/macOS (Bash)
source .venv/bin/activate
```

### 3. Instalar as Dependências

```powershell
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente (`.env`)

Copie o arquivo `.env.example` para `.env`:

```powershell
cp .env.example .env
```

Edite o arquivo `.env` conforme seu ambiente MySQL (padrão XAMPP):

```env
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
DB_NAME=food_api_db
DATABASE_URL=mysql+pymysql://root:@localhost:3306/food_api_db
```

### 5. Iniciar o Banco de Dados MySQL

1. Abra o painel de controle do **XAMPP Control Panel**.
2. Clique em **Start** no módulo **MySQL** (porta padrão: `3306`).
3. Certifique-se de que o banco `food_api_db` existe (pode ser criado via phpMyAdmin em `http://localhost/phpmyadmin` ou pelo console MySQL).

---

## 🏃 Executando a Aplicação

Para iniciar o servidor FastAPI em modo de desenvolvimento (com recarregamento automático):

```powershell
uvicorn main:app --reload
```

A API estará acessível em:
- **URL Base**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentação Interativa (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Documentação Alternativa (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Executando os Testes Automatizados

Os testes rodam de forma 100% isolada utilizando SQLite em memória, sem interferir nem depender dos dados do MySQL:

```powershell
pytest -v
```

---

## 📡 Exemplos de Uso da API

### Criar uma Categoria
**Requisição:**
`POST /categorias/`
```json
{
  "nome": "Lanches Especiais"
}
```

**Resposta (`201 Created`):**
```json
{
  "id": 1,
  "nome": "Lanches Especiais"
}
```

---

### Criar um Produto Vinculado
**Requisição:**
`POST /produtos/`
```json
{
  "nome": "X-Picanha Cheddar",
  "preco": 38.90,
  "categoria_id": 1
}
```

**Resposta (`201 Created`):**
```json
{
  "id": 1,
  "nome": "X-Picanha Cheddar",
  "preco": 38.90,
  "categoria_id": 1,
  "categoria": {
    "id": 1,
    "nome": "Lanches Especiais"
  }
}
```

---

### Listar Produtos com Paginação e Ordenação
**Requisição:**
`GET /produtos/?skip=0&limit=10&ordenar_por=preco&busca=cheddar`

**Resposta (`200 OK`):**
```json
[
  {
    "id": 1,
    "nome": "X-Picanha Cheddar",
    "preco": 38.90,
    "categoria_id": 1,
    "categoria": {
      "id": 1,
      "nome": "Lanches Especiais"
    }
  }
]
```

---

## 🔄 Gerenciando Migrações com Alembic

O projeto está configurado para gerenciar alterações na estrutura das tabelas usando Alembic:

- **Gerar uma nova migração baseada nos modelos:**
  ```powershell
  alembic revision --autogenerate -m "descricao_da_alteracao"
  ```

- **Aplicar as migrações no banco MySQL:**
  ```powershell
  alembic upgrade head
  ```

- **Reverter a última migração aplicada:**
  ```powershell
  alembic downgrade -1
  ```

- **Verificar a versão atual aplicada no banco:**
  ```powershell
  alembic current
  ```
