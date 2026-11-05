# FoodAPI

Bem-vindo ao FoodAPI! Este projeto é uma API RESTful desenvolvida com FastAPI e SQLAlchemy para gerenciamento completo de cardápios, categorias e produtos alimentícios integrada ao banco de dados MySQL (via XAMPP).

O projeto prioriza boas práticas de engenharia de software para aplicações em produção: controle de versão do esquema com migrações via Alembic, precisão monetária estrita com Decimal, isolamento total de testes com SQLite em memória e arquitetura desacoplada onde a aplicação não depende de criação automática de tabelas no startup.

---

## Decisões de Arquitetura e Engenharia

1. **Gestão de Esquema Exclusiva com Alembic**  
   A aplicação FastAPI não cria tabelas automaticamente ao iniciar (`create_all` foi retirado do ciclo de vida da aplicação). Toda a criação e evolução de tabelas, índices e restrições é controlada pelo Alembic. Isso garante que ambientes novos e bancos legados sejam atualizados de forma previsível e sem riscos de alterações não rastreadas.

2. **Valores Monetários com Precisão Exata (Decimal)**  
   Valores financeiros nunca devem ser tratados com números de ponto flutuante binário (`float`), devido a distorções cumulativas de arredondamento. No FoodAPI, a coluna de preço utiliza `Numeric(10, 2)` no banco de dados e `Decimal` com validação de no máximo 2 casas decimais no Pydantic. Na serialização JSON, o valor é preservado como string decimal (por exemplo, `"29.90"`), impedindo que clientes HTTP convertam o dado para float e percam precisão.

3. **Padronização do Banco de Dados (`food_api`)**  
   O nome do banco de dados está padronizado como `food_api` em todos os módulos, arquivos de ambiente (`.env` e `.env.example`) e migrações, mantendo compatibilidade direta com a base já existente no ambiente de desenvolvimento local.

4. **Migrações Seguras para Bancos Novos e Existentes**  
   A migração inicial do Alembic foi programada de forma defensiva:
   - Em um banco novo e vazio: cria as tabelas `categorias` e `produtos`, chaves primárias, chaves estrangeiras e índices.
   - Em um banco que já possuía tabelas prévias: detecta o que já existe, cria o que falta (como a tabela de categorias e a coluna `categoria_id`) e atualiza a coluna `preco` para `Numeric(10, 2)`, sem jamais descartar dados existentes.

5. **Testes Automatizados 100% Isolados**  
   A suíte de testes unitários e de integração utiliza SQLite em memória (`:memory:`). Isso assegura que nenhum teste leia, modifique ou apague registros da base de dados MySQL de desenvolvimento. Os testes cobrem endpoints, validação de tipos, limites de casas decimais, paginação inválida e até a execução das migrações do Alembic em bancos vazios e com dados legados.

---

## Funcionalidades da API

### Categorias
- Cadastro de categorias com restrição de nome único.
- Listagem de categorias ordenada crescentemente por ID.
- Consulta detalhada por ID com tratamento amigável de erro (404).
- Atualização com validação contra nomes já utilizados por outras categorias.
- Bloqueio de exclusão quando houver produtos vinculados à categoria.

### Produtos
- Cadastro com preço obrigatório, positivo e formato decimal de até duas casas.
- Associação opcional a uma categoria existente (permite produtos sem categoria, com `categoria_id` nulo).
- Listagem com paginação através dos parâmetros `skip` e `limit`.
- Ordenação dinâmica por `id`, `nome` ou `preco`.
- Busca textual por nome com correspondência sem distinção entre maiúsculas e minúsculas (`ilike`).
- Filtro por ID de categoria.
- Atualização e remoção com consistência transacional e rollback automático em falhas.

---

## Tecnologias Utilizadas

- **Python 3.10+**: Linguagem de programação do projeto.
- **FastAPI**: Framework web moderno para construção de APIs assíncronas de alta performance.
- **SQLAlchemy 2.0**: ORM para modelagem relacional e comunicação com o banco.
- **MySQL (XAMPP)**: Banco de dados relacional padrão do projeto.
- **PyMySQL & Cryptography**: Driver de conexão seguro entre Python e MySQL.
- **Pydantic v2**: Validação de dados, esquemas e regras de negócio.
- **Alembic**: Sistema de controle de versão e migrações do banco de dados.
- **python-dotenv**: Gestão de variáveis de ambiente locais.
- **Pytest & HTTPX**: Testes automatizados rápidos e isolados.
- **Uvicorn**: Servidor ASGI para desenvolvimento e execução.

---

## Estrutura do Projeto

```text
food-api/
├── migrations/                 # Migrações e versionamento do banco (Alembic)
│   ├── versions/               # Arquivos de revisão das migrações
│   │   └── 50d5aa47f7e2_initial_schema.py
│   └── env.py                  # Configuração do ambiente Alembic integrado ao .env
├── routers/                    # Módulos de rotas da aplicação
│   ├── categorias.py           # Endpoints de categorias
│   └── produtos.py             # Endpoints de produtos
├── tests/                      # Bateria de testes automatizados
│   └── test_api.py             # 19 cenários de teste isolados em SQLite
├── .env                        # Configurações locais ativas (ignorado no Git)
├── .env.example                # Modelo de configuração de variáveis
├── .gitignore                  # Arquivos e diretórios ignorados pelo Git
├── alembic.ini                 # Configuração base do Alembic
├── database.py                 # Conexão com MySQL e fábrica de sessões
├── main.py                     # Inicialização da aplicação FastAPI
├── models.py                   # Modelos de dados relacionais (SQLAlchemy)
├── requirements.txt            # Dependências com versões fixadas
├── schemas.py                  # Schemas de validação e serialização (Pydantic)
└── README.md                   # Documentação técnica do projeto
```

---

## Instalação e Execução Passo a Passo

### 1. Pré-requisitos

- Python 3.10 ou superior instalado.
- XAMPP instalado com o serviço MySQL ativo na porta 3306.

### 2. Ambiente Virtual

Abra o terminal no diretório do projeto e ative o ambiente virtual:

No Windows (PowerShell):
```powershell
# Caso ainda não tenha o ambiente criado:
python -m venv .venv

# Ativação:
.\.venv\Scripts\Activate.ps1
```

No Linux ou macOS:
```bash
source .venv/bin/activate
```

### 3. Instalação das Dependências

Instale as bibliotecas requeridas:

```powershell
pip install -r requirements.txt
```

### 4. Configuração do Banco de Dados (.env)

Crie ou edite o arquivo `.env` na raiz da pasta `food-api`:

```env
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
DB_NAME=food_api
DATABASE_URL=mysql+pymysql://root:@localhost:3306/food_api
```

Certifique-se de que o MySQL está em execução no painel de controle do XAMPP e que o banco `food_api` existe.

### 5. Executando as Migrações do Alembic

Como a aplicação não cria tabelas automaticamente no startup, a inicialização e atualização do esquema do banco de dados deve ser realizada pelo Alembic:

```powershell
alembic upgrade head
```

Esse comando aplica a revisão inicial, criando as tabelas `categorias`, `produtos` e seus respectivos relacionamentos e índices caso ainda não existam.

### 6. Executando o Servidor

Inicie a API com recarregamento automático:

```powershell
uvicorn main:app --reload
```

A aplicação estará disponível em:
- Endereço da API: http://127.0.0.1:8000
- Documentação interativa (Swagger UI): http://127.0.0.1:8000/docs
- Documentação alternativa (ReDoc): http://127.0.0.1:8000/redoc

---

## Exemplos de Uso

### 1. Criar Categoria

Endpoint: `POST /categorias/`

Corpo da requisição:
```json
{
  "nome": "Bebidas Quentes"
}
```

Resposta (`201 Created`):
```json
{
  "id": 4,
  "nome": "Bebidas Quentes"
}
```

### 2. Criar Produto

Endpoint: `POST /produtos/`

Corpo da requisição:
```json
{
  "nome": "Café Expresso Especial",
  "preco": "8.50",
  "categoria_id": 4
}
```

Resposta (`201 Created`):
```json
{
  "id": 6,
  "nome": "Café Expresso Especial",
  "preco": "8.50",
  "categoria_id": 4,
  "categoria": {
    "id": 4,
    "nome": "Bebidas Quentes"
  }
}
```

### 3. Listar Produtos com Paginação, Ordenação e Busca

Endpoint: `GET /produtos/?skip=0&limit=10&ordenar_por=preco&busca=expresso`

Resposta (`200 OK`):
```json
[
  {
    "id": 6,
    "nome": "Café Expresso Especial",
    "preco": "8.50",
    "categoria_id": 4,
    "categoria": {
      "id": 4,
      "nome": "Bebidas Quentes"
    }
  }
]
```

---

## Executando os Testes Automatizados

A suíte de testes valida todas as regras de negócio de ponta a ponta sem encostar no banco MySQL de desenvolvimento:

```powershell
pytest -v
```

Cenários cobertos pelos testes:
- Verificação de status e isolamento do MySQL.
- Criação, listagem, duplicidade e proteção contra exclusão em categorias.
- Precisão decimal de preços (rejeição de mais de 2 casas decimais, aceitação de valores inteiros, 1 e 2 casas).
- Preços limites (mínimo de 1 centavo, valores altos, rejeição de zero e negativos).
- Paginação com parâmetros válidos e rejeição com erro 422 para parâmetros inválidos (`skip < 0`, `limit <= 0`, `limit > 100`, textos).
- Ordenação por `id`, `nome` e `preco`, e erro 400 para ordenação inválida.
- Busca por nome sem distinção de caixa alta/baixa e busca sem resultados.
- Execução de migração do Alembic em banco vazio.
- Execução de migração do Alembic em banco legado com dados prévios (validação de preservação de registros).

---

## Comandos Úteis do Alembic

- Gerar nova revisão automaticamente:
  ```powershell
  alembic revision --autogenerate -m "descricao_da_alteracao"
  ```
- Aplicar migrações pendentes:
  ```powershell
  alembic upgrade head
  ```
- Reverter a última migração:
  ```powershell
  alembic downgrade -1
  ```
- Consultar a versão atual do banco:
  ```powershell
  alembic current
  ```
