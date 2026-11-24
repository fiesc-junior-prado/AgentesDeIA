from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Cooperado(Base):
    __tablename__ = "cooperados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome_fantasia: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    cnpj_cpf: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    unidade_consumidora: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    contratos: Mapped[list["ContratoEnergia"]] = relationship(back_populates="cooperado")


class ContratoEnergia(Base):
    __tablename__ = "contratos_energia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cooperado_id: Mapped[int] = mapped_column(ForeignKey("cooperados.id"), nullable=False)
    modalidade_cota: Mapped[str] = mapped_column(String(50), nullable=False)  # RESIDENCIAL, COMERCIAL_BASIC, COMERCIAL_PLUS
    cota_mensal_kwh: Mapped[int] = mapped_column(Integer, nullable=False)
    saldo_creditos_kwh: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ATIVO", nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    cooperado: Mapped["Cooperado"] = relationship(back_populates="contratos")


class AuditoriaRegulatoria(Base):
    __tablename__ = "auditoria_regulatoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    contrato_id: Mapped[int] = mapped_column(ForeignKey("contratos_energia.id"), nullable=False)
    tipo_evento: Mapped[str] = mapped_column(String(50), nullable=False)  # TROCA_MODALIDADE, CREDITO_COMPENSATORIO
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    responsavel: Mapped[str] = mapped_column(String(100), default="AGENTE_IA")
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())