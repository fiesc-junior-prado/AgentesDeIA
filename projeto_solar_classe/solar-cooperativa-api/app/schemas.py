from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class CooperadoOut(BaseModel):
    id: int
    nome_fantasia: str
    cnpj_cpf: str
    unidade_consumidora: str

    model_config = {"from_attributes": True}


class ContratoOut(BaseModel):
    id: int
    cooperado_id: int
    modalidade_cota: str
    cota_mensal_kwh: int
    saldo_creditos_kwh: int
    status: str

    model_config = {"from_attributes": True}


class ContratoUpdateModalidade(BaseModel):
    modalidade_cota: Literal["RESIDENCIAL", "COMERCIAL_BASIC", "COMERCIAL_PLUS"]
    cota_mensal_kwh: int = Field(..., gt=0)


class ContratoAddCreditos(BaseModel):
    creditos_kwh: int = Field(..., gt=0, description="Quantidade de kWh a ser creditada")
    motivo: str


class AuditoriaCreate(BaseModel):
    contrato_id: int
    tipo_evento: Literal["TROCA_MODALIDADE", "CREDITO_COMPENSATORIO"]
    descricao: str
    responsavel: str = "AGENTE_IA"


class AuditoriaOut(BaseModel):
    id: int
    contrato_id: int
    tipo_evento: str
    descricao: str
    responsavel: str
    criado_em: datetime

    model_config = {"from_attributes": True}