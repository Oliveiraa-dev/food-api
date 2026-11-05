# FoodAPI

Bem-vindo ao FoodAPI! Este projeto nasceu da necessidade de criar um backend limpo, confiável e bem estruturado para o gerenciamento de cardápios, categorias e produtos alimentícios. 

A ideia central aqui foi ir além de um CRUD básico, aplicando boas práticas de engenharia de software do mundo real: isolamento de banco de dados nos testes, controle estrito de tipos monetários, paginação e ordenação flexíveis e versionamento do esquema do banco com migrações.

---

## Por que o projeto foi desenhado desta forma?

Durante o desenvolvimento, tomamos algumas decisões arquiteturais importantes que valem a pena destacar:

1. **Valores monetários com precisão exata (Decimal)**  
   Trabalhar com dinheiro usando números de ponto flutuante (`float`) é uma armadilha comum que gera erros cumulativos de arredondamento. Aqui, usamos `Numeric(10, 2)` no banco de dados e `Decimal` com validações no Pydantic, garantindo precisão de centavos em qualquer transação.

2. **Ciclo de vida assíncrono com Lifespan**  
   Em versões anteriores, a criação automática de tabelas rodava diretamente no momento em que o módulo era importado. Isso causava dores de cabeça, pois importar o aplicativo para rodar um teste tentava conectar ao MySQL antes da hora. Movemos essa inicialização para o evento de `lifespan` do FastAPI. Agora, o MySQL só é chamado quando a API sobe de verdade para atender requisições.

3. **Testes automatizados 100% seguros e independentes**  
   Os testes rodam sobre um banco SQLite em memória (`:memory:`), criando e destruindo as tabelas dinamicamente a cada bateria de testes. Isso significa que você pode rodar a suíte de testes quantas vezes quiser sem qualquer risco de alterar, sujar ou apagar os registros do seu MySQL local.

4. **Tratamento defensivo de transações**  
   Operações que alteram dados (criação, edição e exclusão) são protegidas com blocos try/except específicos para erros de banco. Se algo falhar — como uma tentativa de duplicar uma categoria com nome já existente —, a transação sofre rollback imediatamente e o usuário recebe uma mensagem clara e amigável em vez de um erro 500 confuso.

---

## O que a API faz na prática

### Gestão de Categorias
- Criação de categorias com garantia de nome único.
- Consulta de categorias pelo identificador (ID).
- Listagem geral sempre organizada em ordem crescente por ID.
- Atualização de nomes respeitando a unicidade no banco.
- Exclusão segura: a API recusa a exclusão de qualquer categoria que ainda possua produtos atrelados a ela.

### Gestão de Produtos
- Cadastro de produtos com preço obrigatório, positivo e formato decimal.
- Associação a categorias existentes ou opção de cadastrar produtos avulsos sem categoria (`categoria_id` nulo).
- Listagem completa com paginação customizável via parâmetros `skip` e `limit`.
- Ordenação dinâmica por `id`, `nome` ou `preco`.
- Filtro por categoria específica.
- Busca textual flexível por nome com correspondência sem distinção entre maiúsculas e minúsculas (`ilike`).
- Atualização e exclusão com consistência transacional.

---

## Tecnologias que dão vida ao projeto

- **Python 3.10+**: Linguagem base do projeto.
- **FastAPI**: Framework web moderno, focado em performance, tipagem estrita e documentação automática.
- **SQLAlchemy 2.0**: O ORM utilizado para mapear os modelos relacionais e gerenciar as consultas ao banco.
- **MySQL / PyMySQL**: Banco de dados relacional executado localmente via XAMPP com driver em Python puro.
- **Pydantic v2**: Validação robusta de esquemas de entrada e serialização de saída.
- **Alembic**: Ferramenta de versionamento e gerenciamento de migrações do banco de dados.
- **python-dotenv**: Carregamento seguro de credenciais a partir de arquivos `.env`.
- **Pytest & HTTPX**: Criação e execução dos testes unitários e de integração através de um cliente assíncrono.
- **Uvicorn**: Servidor ASGI que roda a aplicação com suporte a hot reload.

---

## Estrutura de Pastas

```text
food-api/
├── migrations/                 # Controle de versionamento do banco (Alembic)
│   ├── versions/               # Arquivos gerados para cada migração
│   └── env.py                  # Configuração do ambiente de migração
├── routers/                    # Divisão das rotas por domínio de negócio
│   ├── categorias.py           # Endpoints relacionados a categorias
│   └── produtos.py             # Endpoints relacionados a produtos
├── tests/                      # Bateria de testes automatizados
│   └── test_api.py             # Cenários de teste com SQLite em memória
├── .env                        # Variáveis locais de ambiente (fora do Git)
├── .env.example                # Arquivo modelo com as variáveis necessárias
├── .gitignore                  # Arquivos e diretórios ignorados pelo Git
├── alembic.ini                 # Arquivo de inicialização do Alembic
├── database.py                 # Conexão, sessão e configurações do banco
├── main.py                     # Instância principal da API e ciclo de vida
├── models.py                   # Modelos relacionais (tabelas do banco)
├── requirements.txt            # Dependências fixadas do projeto
├── schemas.py                  # Schemas do Pydantic (validação e formato)
└── README.md                   # Esta documentação
```

---

## Como Rodar o Projeto Passo a Passo

### 1. Pré-requisitos no seu computador

- Python instalado (versão 3.10 ou mais recente).
- XAMPP instalado (ou outro servidor MySQL local equivalente rodando na porta 3306).

### 2. Configurando o ambiente virtual

Recomendamos utilizar um ambiente virtual isolado para evitar conflito com outros pacotes do seu sistema.

No terminal (PowerShell no Windows):

```powershell
# Criar o ambiente virtual caso ainda não exista
python -m venv .venv

# Ativar o ambiente virtual
.\.venv\Scripts\Activate.ps1
```

Caso esteja utilizando Linux ou macOS:

```bash
source .venv/bin/activate
```

### 3. Instalando as dependências

Com o ambiente ativado, instale as bibliotecas necessárias:

```powershell
pip install -r requirements.txt
```

### 4. Configurando as variáveis de ambiente

Copie o arquivo de exemplo para criar o seu `.env` local:

```powershell
cp .env.example .env
```

Abra o arquivo `.env` gerado e confirme as credenciais de acesso ao seu MySQL (as padrões do XAMPP já vêm configuradas):

```env
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
DB_NAME=food_api_db
DATABASE_URL=mysql+pymysql://root:@localhost:3306/food_api_db
```

### 5. Iniciando o servidor MySQL

1. Abra o painel do **XAMPP Control Panel**.
2. Clique no botão **Start** ao lado de **MySQL**.
3. Verifique se a porta `3306` está ativa.
4. O banco `food_api_db` será utilizado para persistir os dados.

### 6. Executando a API

Com o banco de dados ligado e o ambiente ativado, suba a aplicação com o comando:

```powershell
uvicorn main:app --reload
```

A API estará pronta para receber requisições em:
- Endereço principal: `http://127.0.0.1:8000`
- Documentação interativa (Swagger UI): `http://127.0.0.1:8000/docs`
- Documentação alternativa (ReDoc): `http://127.0.0.1:8000/redoc`

---

## Exemplos Práticos de Uso

Você pode testar esses exemplos diretamente pelo Swagger UI no navegador ou usando clientes como Postman, Insomnia ou cURL.

### 1. Cadastrando uma Categoria

Envie uma requisição `POST` para `/categorias/` com o corpo:

```json
{
  "nome": "Sanduíches Especiais"
}
```

Retorno esperado (`201 Created`):

```json
{
  "id": 1,
  "nome": "Sanduíches Especiais"
}
```

### 2. Cadastrando um Produto Vinculado

Envie uma requisição `POST` para `/produtos/` com o corpo:

```json
{
  "nome": "Hambúrguer de Costela",
  "preco": 34.90,
  "categoria_id": 1
}
```

Retorno esperado (`201 Created`):

```json
{
  "id": 1,
  "nome": "Hambúrguer de Costela",
  "preco": 34.90,
  "categoria_id": 1,
  "categoria": {
    "id": 1,
    "nome": "Sanduíches Especiais"
  }
}
```

### 3. Listando Produtos com Filtros, Paginação e Ordenação

Para buscar produtos ordenados por preço, pulando o primeiro e limitando a dez itens:

```text
GET /produtos/?skip=0&limit=10&ordenar_por=preco&busca=costela
```

Retorno esperado (`200 OK`):

```json
[
  {
    "id": 1,
    "nome": "Hambúrguer de Costela",
    "preco": 34.90,
    "categoria_id": 1,
    "categoria": {
      "id": 1,
      "nome": "Sanduíches Especiais"
    }
  }
]
```

---

## Executando a Bateria de Testes

Para rodar todos os testes automatizados e conferir a cobertura das regras de negócio:

```powershell
pytest -v
```

Todos os testes rodam de maneira isolada em memória, garantindo rapidez e zero impacto nos seus dados reais.

---

## Gerenciando o Banco com Alembic

Se você alterar qualquer campo nos arquivos de modelo (`models.py`) e precisar refletir isso no banco de dados sem perder dados existentes, utilize os comandos do Alembic:

- **Gerar automaticamente um arquivo de migração:**
  ```powershell
  alembic revision --autogenerate -m "descreva a sua alteracao aqui"
  ```

- **Aplicar as migrações pendentes no MySQL:**
  ```powershell
  alembic upgrade head
  ```

- **Reverter a última alteração aplicada:**
  ```powershell
  alembic downgrade -1
  ```

- **Ver a versão atual da base de dados:**
  ```powershell
  alembic current
  ```

---

## Conclusão

Este repositório foi construído com cuidado para servir tanto como uma base sólida para projetos reais quanto como referência de arquitetura limpa com FastAPI e SQLAlchemy. Sinta-se à vontade para explorar os módulos, enviar sugestões ou adaptar às suas necessidades!
