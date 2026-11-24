"""Cria tabelas iniciais e popula dados de teste

Revision ID: 001_init
Revises:
Create Date: 2026-11-18 00:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = "001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    cooperados_table = op.create_table(
        "cooperados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome_fantasia", sa.String(length=150), nullable=False),
        sa.Column("cnpj_cpf", sa.String(length=20), nullable=False, unique=True),
        sa.Column("unidade_consumidora", sa.String(length=30), nullable=False, unique=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
    )

    contratos_table = op.create_table(
        "contratos_energia",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cooperado_id", sa.Integer(), sa.ForeignKey("cooperados.id"), nullable=False),
        sa.Column("modalidade_cota", sa.String(length=50), nullable=False),
        sa.Column("cota_mensal_kwh", sa.Integer(), nullable=False),
        sa.Column("saldo_creditos_kwh", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ATIVO"),
        sa.Column("atualizado_em", sa.DateTime(), server_default=sa.func.now()),
    )

    auditoria_table = op.create_table(
        "auditoria_regulatoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contrato_id", sa.Integer(), sa.ForeignKey("contratos_energia.id"), nullable=False),
        sa.Column("tipo_evento", sa.String(length=50), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("responsavel", sa.String(length=100), nullable=False, server_default="SISTEMA"),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
    )

    # Seed inicial (População do banco)
    op.bulk_insert(
        cooperados_table,
        [
            {
                "id": 1,
                "nome_fantasia": "Padaria Pão Dourado",
                "cnpj_cpf": "12.345.678/0001-90",
                "unidade_consumidora": "UC-8849201",
            },
            {
                "id": 2,
                "nome_fantasia": "Mercado Bom Preço",
                "cnpj_cpf": "98.765.432/0001-10",
                "unidade_consumidora": "UC-7731044",
            },
            {
                "id": 3,
                "nome_fantasia": "Residência Família Oliveira",
                "cnpj_cpf": "123.456.789-00",
                "unidade_consumidora": "UC-5510922",
            },
        ],
    )

    op.bulk_insert(
        contratos_table,
        [
            {
                "id": 10,
                "cooperado_id": 1,
                "modalidade_cota": "RESIDENCIAL",
                "cota_mensal_kwh": 600,
                "saldo_creditos_kwh": 150,
                "status": "ATIVO",
            },
            {
                "id": 11,
                "cooperado_id": 2,
                "modalidade_cota": "COMERCIAL_BASIC",
                "cota_mensal_kwh": 1800,
                "saldo_creditos_kwh": 420,
                "status": "ATIVO",
            },
            {
                "id": 12,
                "cooperado_id": 3,
                "modalidade_cota": "RESIDENCIAL",
                "cota_mensal_kwh": 450,
                "saldo_creditos_kwh": 80,
                "status": "ATIVO",
            },
        ],
    )

    op.bulk_insert(
        auditoria_table,
        [
            {
                "id": 1,
                "contrato_id": 10,
                "tipo_evento": "CREDITO_COMPENSATORIO",
                "descricao": "Crédito inicial de adesão à cooperativa (150 kWh).",
                "responsavel": "MIGRATION_SEED",
            }
        ],
    )

    # Ajusta as sequences do PostgreSQL após inserção manual de IDs
    op.execute("SELECT setval('cooperados_id_seq', (SELECT MAX(id) FROM cooperados));")
    op.execute("SELECT setval('contratos_energia_id_seq', (SELECT MAX(id) FROM contratos_energia));")
    op.execute("SELECT setval('auditoria_regulatoria_id_seq', (SELECT MAX(id) FROM auditoria_regulatoria));")


def downgrade() -> None:
    op.drop_table("auditoria_regulatoria")
    op.drop_table("contratos_energia")
    op.drop_table("cooperados")