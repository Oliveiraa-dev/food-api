"""initial schema

Revision ID: 50d5aa47f7e2
Revises: 
Create Date: 2026-11-05 19:49:51.673661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '50d5aa47f7e2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. Tabela categorias
    if "categorias" not in existing_tables:
        op.create_table(
            "categorias",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=50), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_categorias_id"), "categorias", ["id"], unique=False)
        op.create_index(op.f("ix_categorias_nome"), "categorias", ["nome"], unique=True)
    else:
        # Se categorias já existe, garante os índices necessários se ausentes
        cat_indexes = [idx["name"] for idx in inspector.get_indexes("categorias")]
        if "ix_categorias_id" not in cat_indexes and op.f("ix_categorias_id") not in cat_indexes:
            try:
                op.create_index(op.f("ix_categorias_id"), "categorias", ["id"], unique=False)
            except Exception:
                pass
        if "ix_categorias_nome" not in cat_indexes and op.f("ix_categorias_nome") not in cat_indexes:
            try:
                op.create_index(op.f("ix_categorias_nome"), "categorias", ["nome"], unique=True)
            except Exception:
                pass

    # Atualiza lista de tabelas após criação de categorias
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 2. Tabela produtos
    if "produtos" not in existing_tables:
        op.create_table(
            "produtos",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nome", sa.String(length=100), nullable=False),
            sa.Column("preco", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("categoria_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ["categoria_id"],
                ["categorias.id"],
                name="fk_produtos_categoria_id",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_produtos_id"), "produtos", ["id"], unique=False)
        op.create_index(op.f("ix_produtos_nome"), "produtos", ["nome"], unique=False)
    else:
        # Tabela produtos já existe: aplicar modificações incrementais e não destrutivas
        prod_columns = [col["name"] for col in inspector.get_columns("produtos")]
        
        with op.batch_alter_table("produtos") as batch_op:
            # Adiciona categoria_id com foreign key se não existir
            if "categoria_id" not in prod_columns:
                batch_op.add_column(sa.Column("categoria_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_produtos_categoria_id",
                    "categorias",
                    ["categoria_id"],
                    ["id"],
                )
            
            # Atualiza o tipo de preco para Numeric(10, 2)
            batch_op.alter_column(
                "preco",
                type_=sa.Numeric(precision=10, scale=2),
                existing_nullable=False,
            )

        # Garante índices em produtos
        prod_indexes = [idx["name"] for idx in inspector.get_indexes("produtos")]
        if "ix_produtos_id" not in prod_indexes and op.f("ix_produtos_id") not in prod_indexes:
            try:
                op.create_index(op.f("ix_produtos_id"), "produtos", ["id"], unique=False)
            except Exception:
                pass
        if "ix_produtos_nome" not in prod_indexes and op.f("ix_produtos_nome") not in prod_indexes:
            try:
                op.create_index(op.f("ix_produtos_nome"), "produtos", ["nome"], unique=False)
            except Exception:
                pass


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "produtos" in existing_tables:
        with op.batch_alter_table("produtos") as batch_op:
            try:
                batch_op.drop_constraint("fk_produtos_categoria_id", type_="foreignkey")
            except Exception:
                pass
        op.drop_table("produtos")

    if "categorias" in existing_tables:
        op.drop_table("categorias")
