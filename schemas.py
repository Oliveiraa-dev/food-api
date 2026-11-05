from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_serializer


# ==========================================
# SCHEMAS DE CATEGORIAS
# ==========================================

class CategoriaBase(BaseModel):
    nome: str = Field(min_length=2, max_length=50, description="Nome da categoria (ex: Lanches, Bebidas)")


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaResponse(CategoriaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# SCHEMAS DE PRODUTOS
# ==========================================

class ProdutoBase(BaseModel):
    nome: str = Field(min_length=2, max_length=100, description="Nome do produto")
    preco: Decimal = Field(gt=0, decimal_places=2, max_digits=10, description="Preço unitário em Reais, maior que zero")
    categoria_id: int | None = Field(default=None, description="ID da categoria à qual o produto pertence")

    @field_serializer("preco", when_used="json")
    def serialize_preco(self, v: Decimal):
        return float(v)


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoResponse(ProdutoBase):
    id: int
    categoria: CategoriaResponse | None = None

    model_config = ConfigDict(from_attributes=True)
