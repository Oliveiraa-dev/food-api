from pydantic import BaseModel, Field, ConfigDict

class ProdutoBase(BaseModel):
    nome: str = Field(min_length=2, max_length=100) # min_length = tamanho mínimo / max_length=100 = tamanho máximo de caracteres
    preco: float = Field(gt=0) # greater than = maior que.  


class ProdutoCreate(ProdutoBase):
    pass 


class ProdutoResponse(ProdutoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
