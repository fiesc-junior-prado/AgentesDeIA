from typing import Annotated, Literal
from typing_extensions import TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

load_dotenv()

# 1. FERRAMENTA COM ENTRADA E SAÍDA ESTRUTURADAS (Pydantic)
class ConsultaPedidoInput(BaseModel):
    pedido_id: str = Field(description="Código do pedido no formato PED-XXX (ex: PED-101)")

class ConsultaPedidoOutput(BaseModel):
    pedido_id: str
    encontrado: bool
    status: str
    previsao: str

@tool(args_schema=ConsultaPedidoInput)
def consultar_status_pedido(pedido_id: str) -> dict:
    """Consulta o status atual e previsão de entrega de um pedido no sistema."""
    banco_ficticio = {
        "PED-101": {"status": "Em trânsito", "previsao": "2 dias úteis"},
        "PED-102": {"status": "Pagamento pendente", "previsao": "Aguardando compensação"},
        "PED-103": {"status": "Entregue", "previsao": "Concluído"},
    }
    dados = banco_ficticio.get(pedido_id.upper())
    if not dados:
        saida = ConsultaPedidoOutput(
            pedido_id=pedido_id.upper(),
            encontrado=False,
            status="Não localizado",
            previsao="N/A"
        )
    else:
        saida = ConsultaPedidoOutput(
            pedido_id=pedido_id.upper(),
            encontrado=True,
            status=dados["status"],
            previsao=dados["previsao"]
        )
    return saida.model_dump()

ferramentas = [consultar_status_pedido]


# 2. DEFINIÇÃO DO ESTADO DO GRAFO
class EstadoAgente(TypedDict):
    # `add_messages` garante que novas mensagens sejam anexadas ao histórico, não sobrescritas
    messages: Annotated[list, add_messages]

# 3. CONFIGURAÇÃO DO MODELO E PROMPT
SYSTEM_PROMPT = SystemMessage(content="""
# PAPEL
Você é um Assistente de Suporte ao Cliente da loja TechStore.

# OBJETIVO
Ajudar clientes a verificar o status de seus pedidos de forma precisa e educada.

# CONTEXTO
- Use exclusivamente a ferramenta `consultar_status_pedido` para obter dados.
- Nunca invente status ou prazos.
- Se o código do pedido estiver ausente ou incompleto, solicite-o claramente ao usuário.

# FORMATO DE SAÍDA
Responda de forma concisa em tópicos:
- **Pedido:** [código]
- **Status:** [situação]
- **Previsão:** [prazo]
""")

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.0)
llm_com_tools = llm.bind_tools(ferramentas)

# 4. DEFINIÇÃO DOS NÓS (NODES)
def no_agente(state: EstadoAgente):
    """Nó que invoca o LLM com o histórico atual."""
    mensagens_completas = [SYSTEM_PROMPT] + state["messages"]
    resposta = llm_com_tools.invoke(mensagens_completas)
    return {"messages": [resposta]}

# ToolNode é um nó pré-construído do LangGraph que executa as tools chamadas pelo LLM
no_ferramentas = ToolNode(ferramentas)

# 5. DEFINIÇÃO DAS TRANSIÇÕES (CONDITIONAL EDGES)
def decidir_proximo_passo(state: EstadoAgente) -> Literal["ferramentas", "__end__"]:
    """Verifica se a última mensagem do agente contém pedido de chamada de ferramenta."""
    ultima_mensagem = state["messages"][-1]
    if ultima_mensagem.tool_calls:
        return "ferramentas"
    return "__end__"

# 6. MONTAGEM E COMPILAÇÃO DO GRAFO
workflow = StateGraph(EstadoAgente)

workflow.add_node("agente", no_agente)
workflow.add_node("ferramentas", no_ferramentas)

workflow.add_edge(START, "agente")
workflow.add_conditional_edges("agente", decidir_proximo_passo)
workflow.add_edge("ferramentas", "agente") # Loop: após rodar a tool, volta para o agente

app = workflow.compile()