"""cantidad, categorias, prioridad, precio y reservas por unidad

Revision ID: 8b7dd4843e58
Revises: 264cedb6c13a
Create Date: 2026-08-14 20:36:56.236245

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b7dd4843e58"
down_revision: Union[str, None] = "264cedb6c13a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


prioridad_enum = sa.Enum(
    "URGENTE", "NORMAL", "PUEDE_ESPERAR", name="prioridad", create_type=False
)
rango_precio_enum = sa.Enum(
    "BAJO", "MEDIO", "ALTO", name="rangoprecio", create_type=False
)


def upgrade() -> None:
    # add_column no emite el CREATE TYPE: hay que crearlos antes.
    sa.Enum("URGENTE", "NORMAL", "PUEDE_ESPERAR", name="prioridad").create(
        op.get_bind(), checkfirst=True
    )
    sa.Enum("BAJO", "MEDIO", "ALTO", name="rangoprecio").create(
        op.get_bind(), checkfirst=True
    )

    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )

    # server_default para que las filas existentes queden válidas; se
    # mantiene después porque simplifica los INSERT desde la app.
    op.add_column(
        "items",
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "items",
        sa.Column(
            "cantidad_recibida", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "items",
        sa.Column(
            "prioridad",
            prioridad_enum,
            nullable=False,
            server_default="NORMAL",
        ),
    )
    op.add_column(
        "items",
        sa.Column("rango_precio", rango_precio_enum, nullable=True),
    )
    op.add_column("items", sa.Column("categoria_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_items_categoria",
        "items",
        "categorias",
        ["categoria_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Backfill: los items ya adquiridos tienen su única unidad recibida.
    op.execute(
        "UPDATE items SET cantidad_recibida = 1 WHERE estado = 'ADQUIRIDO'"
    )

    op.create_check_constraint("ck_items_cantidad_positiva", "items", "cantidad >= 1")
    op.create_check_constraint(
        "ck_items_recibida_valida",
        "items",
        "cantidad_recibida >= 0 AND cantidad_recibida <= cantidad",
    )

    # En la v1 solo podía haber una reserva activa por item, así que todas
    # las existentes corresponden a la unidad 1.
    op.add_column(
        "reservas",
        sa.Column("unidad", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("reservas", sa.Column("mensaje", sa.Text(), nullable=True))

    op.drop_index(
        "uq_reservas_item_activa",
        table_name="reservas",
        postgresql_where="(released_at IS NULL)",
    )
    op.create_index(
        "uq_reservas_item_unidad",
        "reservas",
        ["item_id", "unidad"],
        unique=True,
        postgresql_where="released_at IS NULL",
    )


def downgrade() -> None:
    op.drop_index(
        "uq_reservas_item_unidad",
        table_name="reservas",
        postgresql_where="released_at IS NULL",
    )
    op.create_index(
        "uq_reservas_item_activa",
        "reservas",
        ["item_id"],
        unique=True,
        postgresql_where="(released_at IS NULL)",
    )
    op.drop_column("reservas", "mensaje")
    op.drop_column("reservas", "unidad")

    op.drop_constraint("ck_items_recibida_valida", "items", type_="check")
    op.drop_constraint("ck_items_cantidad_positiva", "items", type_="check")
    op.drop_constraint("fk_items_categoria", "items", type_="foreignkey")
    op.drop_column("items", "categoria_id")
    op.drop_column("items", "rango_precio")
    op.drop_column("items", "prioridad")
    op.drop_column("items", "cantidad_recibida")
    op.drop_column("items", "cantidad")
    op.drop_table("categorias")

    # drop_column no elimina los tipos ENUM de Postgres; sin esto un ciclo
    # downgrade/upgrade falla con "type already exists".
    sa.Enum(name="prioridad").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="rangoprecio").drop(op.get_bind(), checkfirst=True)
