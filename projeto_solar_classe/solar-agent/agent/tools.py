import os
import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field


SOLAR_API_URL = os.getenv("SOLAR_API_BASE_URL", "http://localhost:8000")
LIMITE_MAXIMO_CREDITOS_KWH = 800

class BuscarCooperadoInput(BaseModel):
    nome: str = Field(..., min_length=2, description="Nome fantasia ou termo de busca do cooperado.")

def _format_http_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        detail = exc.response.text
        if status == 404:
            return f"Erro HTTP 404 (Não Encontrado): Recurso inexistente na API Solar. Detalhe: {detail}"
        if status == 422:
            return f"Erro HTTP 422 (Dados Inválidos): Parâmetros rejeitados pelo contrato da API. Detalhe: {detail}"
        return f"Erro HTTP {status} na API Solar: {detail}"
    if isinstance(exc, httpx.TimeoutException):
        return "Erro de Timeout: A API Solar excedeu o tempo limite de resposta (10s)."
    return f"Erro de conexão com a API Solar: {str(exc)}"

@tool(args_schema=BuscarCooperadoInput)
def buscar_cooperado(nome: str) -> str:
    """Busca cooperados cadastrados pelo nome fantasia (GET /cooperados?nome=...) para obter cooperado_id e Unidade Consumidora."""
    try:
        with httpx.Client(base_url=SOLAR_API_URL, timeout=10.0) as client:
            response = client.get("/cooperados", params={"nome": nome.strip()})
            response.raise_for_status()
            cooperados = response.json()
            if not cooperados:
                return f"RESULTADO_VAZIO: Nenhum cooperado encontrado para '{nome}'."
            return f"COOPERADOS_ENCONTRADOS: {cooperados}"
    except Exception as exc:
        return _format_http_error(exc)


class BuscarCooperadoInput(BaseModel):
    nome: str = Field(..., min_length=2, description="Nome fantasia ou termo de busca do cooperado.")


@tool(args_schema=BuscarCooperadoInput)
def buscar_cooperado(nome: str) -> str:
    """Busca cooperados cadastrados pelo nome fantasia (GET /cooperados?nome=...) para obter cooperado_id e Unidade Consumidora."""
    try:
        with httpx.Client(base_url=SOLAR_API_URL, timeout=10.0) as client:
            response = client.get("/cooperados", params={"nome": nome.strip()})
            response.raise_for_status()
            cooperados = response.json()
            if not cooperados:
                return f"RESULTADO_VAZIO: Nenhum cooperado encontrado para '{nome}'."
            return f"COOPERADOS_ENCONTRADOS: {cooperados}"
    except Exception as exc:
        return _format_http_error(exc)


class ConsultarContratoInput(BaseModel):
    cooperado_id: int = Field(..., gt=0, description="ID numérico positivo do cooperado.")


@tool(args_schema=ConsultarContratoInput)
def consultar_contrato_energia(cooperado_id: int) -> str:
    """Consulta o contrato de energia vigente do cooperado (GET /contratos-energia/{cooperado_id}), retornando contrato_id, modalidade_cota, status e saldo_creditos_kwh."""
    try:
        with httpx.Client(base_url=SOLAR_API_URL, timeout=10.0) as client:
            response = client.get(f"/contratos-energia/{cooperado_id}")
            response.raise_for_status()
            return f"CONTRATOS_ENCONTRADOS: {response.json()}"
    except Exception as exc:
        return _format_http_error(exc)


class IncluirCreditosInput(BaseModel):
    contrato_id: int = Field(..., gt=0, description="ID numérico positivo do contrato de energia.")
    creditos_kwh: int = Field(
        ...,
        gt=0,
        le=LIMITE_MAXIMO_CREDITOS_KWH,
        description="Quantidade positiva de créditos em kWh (máximo permitido: 800 kWh por operação).",
    )
    motivo: str = Field(..., min_length=5, description="Motivo operacional da concessão de créditos.")


@tool(args_schema=IncluirCreditosInput)
def incluir_creditos_kwh(contrato_id: int, creditos_kwh: int, motivo: str) -> str:
    """Inclui créditos extras de kWh em um contrato ativo (PATCH /contratos-energia/{contrato_id}/creditos). Limite máximo: 800 kWh."""
    if creditos_kwh <= 0:
        return "VALIDACAO_RECUSADA: A quantidade de créditos deve ser estritamente maior que zero."
    if creditos_kwh > LIMITE_MAXIMO_CREDITOS_KWH:
        return (
            f"VALIDACAO_RECUSADA: A quantidade solicitada ({creditos_kwh} kWh) excede o teto operacional "
            f"de {LIMITE_MAXIMO_CREDITOS_KWH} kWh por operação."
        )

    try:
        with httpx.Client(base_url=SOLAR_API_URL, timeout=10.0) as client:
            response = client.patch(
                f"/contratos-energia/{contrato_id}/creditos",
                json={"creditos_kwh": creditos_kwh, "motivo": motivo.strip()},
            )
            response.raise_for_status()
            return f"CREDITOS_INCLUIDOS_SUCESSO: {response.json()}"
    except Exception as exc:
        return _format_http_error(exc)


SOLAR_TOOLS = [
    buscar_cooperado,
    consultar_contrato_energia,
    incluir_creditos_kwh,
]

