"""regalos, fotos de regalo y etapa

Revision ID: 84d35ddd3ae4
Revises: 8b7dd4843e58
Create Date: 2026-08-15 08:57:41.669869

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "84d35ddd3ae4"
down_revision: Union[str, None] = "8b7dd4843e58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ETAPAS = (
    "CUALQUIERA",
    "RECIEN_NACIDO",
    "M0_3",
    "M3_6",
    "M6_12",
    "A1_2",
    "A2_MAS",
)

# postgresql.ENUM (no sa.Enum) porque es el único que respeta
# create_type=False: create_table emite el CREATE TYPE por su cuenta y
# chocaría con el que creamos explícitamente más abajo.
etapa_enum = postgresql.ENUM(*ETAPAS, name="etapa", create_type=False)
origen_regalo_enum = postgresql.ENUM(
    "REGALO", "NOSOTROS", name="origenregalo", create_type=False
)


def upgrade() -> None:
    sa.Enum(*ETAPAS, name="etapa").create(op.get_bind(), checkfirst=True)
    sa.Enum("REGALO", "NOSOTROS", name="origenregalo").create(
        op.get_bind(), checkfirst=True
    )

    op.create_table(
        "regalos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("persona", sa.String(length=255), nullable=False, server_default=""),
        sa.Column(
            "origen", origen_regalo_enum, nullable=False, server_default="REGALO"
        ),
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("fecha", sa.Date(), nullable=False, server_default=sa.func.now()),
        sa.Column("nota", sa.Text(), nullable=True),
        sa.Column(
            "agradecido", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("reserva_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("cantidad >= 1", name="ck_regalos_cantidad_positiva"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reserva_id"], ["reservas.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reserva_id"),
    )
    op.create_index(op.f("ix_regalos_item_id"), "regalos", ["item_id"], unique=False)
    op.create_index(op.f("ix_regalos_persona"), "regalos", ["persona"], unique=False)

    op.create_table(
        "fotos_regalo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("regalo_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["regalo_id"], ["regalos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fotos_regalo_regalo_id"), "fotos_regalo", ["regalo_id"], unique=False
    )

    op.add_column(
        "items",
        sa.Column("etapa", etapa_enum, nullable=False, server_default="CUALQUIERA"),
    )

    # --- Backfill ---
    # 1) Regalos que vinieron de la wishlist: el nombre está limpio en la
    #    reserva revelada, así que se puede enlazar uno a uno.
    op.execute(
        """
        INSERT INTO regalos (item_id, persona, origen, cantidad, fecha,
                             nota, reserva_id)
        SELECT r.item_id, r.nombre_reservante, 'REGALO'::origenregalo, 1,
               COALESCE(r.released_at::date, CURRENT_DATE), r.mensaje, r.id
        FROM reservas r
        WHERE r.revelado = true
        """
    )
    # 2) El resto de lo recibido. items.gifter_name es un string concatenado
    #    con comas y no hay forma segura de partirlo (un nombre puede llevar
    #    coma), así que se vuelca entero en un único regalo. Se descuenta lo
    #    ya cargado en el paso 1 para no contar dos veces.
    op.execute(
        """
        INSERT INTO regalos (item_id, persona, origen, cantidad, fecha)
        SELECT i.id,
               COALESCE(i.gifter_name, ''),
               (CASE WHEN i.gifter_name IS NULL THEN 'NOSOTROS'
                     ELSE 'REGALO' END)::origenregalo,
               i.cantidad_recibida - COALESCE(rev.ya_cargados, 0),
               CURRENT_DATE
        FROM items i
        LEFT JOIN (
            SELECT item_id, COUNT(*) AS ya_cargados
            FROM reservas WHERE revelado = true GROUP BY item_id
        ) rev ON rev.item_id = i.id
        WHERE i.cantidad_recibida - COALESCE(rev.ya_cargados, 0) > 0
        """
    )

    op.drop_column("items", "gifter_name")


def downgrade() -> None:
    op.add_column(
        "items",
        sa.Column("gifter_name", sa.VARCHAR(length=255), nullable=True),
    )
    # Reconstruye el string concatenado a partir de los regalos.
    op.execute(
        """
        UPDATE items i
        SET gifter_name = sub.nombres
        FROM (
            SELECT item_id, string_agg(persona, ', ' ORDER BY fecha, id) AS nombres
            FROM regalos WHERE persona <> '' GROUP BY item_id
        ) sub
        WHERE sub.item_id = i.id
        """
    )
    op.drop_column("items", "etapa")
    op.drop_index(op.f("ix_fotos_regalo_regalo_id"), table_name="fotos_regalo")
    op.drop_table("fotos_regalo")
    op.drop_index(op.f("ix_regalos_persona"), table_name="regalos")
    op.drop_index(op.f("ix_regalos_item_id"), table_name="regalos")
    op.drop_table("regalos")

    # drop_table/drop_column no eliminan los tipos ENUM de Postgres.
    sa.Enum(name="etapa").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="origenregalo").drop(op.get_bind(), checkfirst=True)
