from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# 1. Tabela de Categorias (Lanches, Bebidas, Sobremesas, etc.)
class CategoriaDB(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), unique=True, index=True, nullable=False)

    # Relacionamento: uma categoria pode ter muitos produtos
    produtos = relationship("ProdutoDB", back_populates="categoria")


# 2. Tabela de Produtos
class ProdutoDB(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), index=True, nullable=False)
    preco = Column(Float, nullable=False)

    # Chave estrangeira que aponta para a tabela "categorias"
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)

    # Relacionamento: cada produto pertence a uma categoria
    categoria = relationship("CategoriaDB", back_populates="produtos")
