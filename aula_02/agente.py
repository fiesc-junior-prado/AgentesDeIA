import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
# 3. ENGENHARIA DE PROMPT (Papel, Objetivo, Contexto, Formato de Saída)
SYSTEM_PROMPT = """
# PAPEL
Você é um Assistente de Suporte ao Cliente da loja TechStore.

# OBJETIVO
Ajudar clientes a verificar o status de seus pedidos de forma precisa e educada.

# CONTEXTO
- Você tem acesso apenas à ferramenta `consultar_status_pedido`.
- Nunca invente informações de pedidos que não vieram da ferramenta.
- Se o cliente não informar o código do pedido (formato PED-XXX), peça o código antes de consultar.

# FORMATO DE SAÍDA
Responda sempre de forma direta, em tópicos curtos, destacando o Status e a Previsão.
"""
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODELO = "openai/gpt-oss-120b"

# 1. FERRAMENTA SIMPLES (Simulando consulta a um banco de dados)
def consultar_status_pedido(pedido_id: str) -> str:
    """Consulta o status de um pedido pelo código."""
    banco_ficticio = {
        "PED-101": {"status": "Em trânsito", "previsao": "2 dias úteis"},
        "PED-102": {"status": "Pagamento pendente", "previsao": "Aguardando compensação"},
        "PED-103": {"status": "Entregue", "previsao": "Concluído"},
    }
    resultado = banco_ficticio.get(pedido_id.upper())
    if not resultado:
        return json.dumps({"erro": f"Pedido {pedido_id} não encontrado."})
    return json.dumps({"pedido_id": pedido_id.upper(), **resultado})

# 2. SCHEMA DA FERRAMENTA (Contrato de entrada estruturada para o LLM)
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "consultar_status_pedido",
            "description": "Busca o status atual e previsão de entrega de um pedido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_id": {
                        "type": "string",
                        "description": "O código identificador do pedido (ex: PED-101).",
                    }
                },
                "required": ["pedido_id"],
            },
        },
    }
]


def executar_agente_puro(pergunta_usuario: str):
    mensagens = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": pergunta_usuario},
    ]

    # Primeira chamada: o LLM decide se responde direto ou chama uma tool
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=mensagens,
        tools=tools_schema,
        tool_choice="auto",
        temperature=0.0,
    )

    msg_assistente = resposta.choices[0].message
    mensagens.append(msg_assistente)

    # Verifica se o modelo pediu para executar uma ferramenta
    if msg_assistente.tool_calls:
        for tool_call in msg_assistente.tool_calls:
            nome_funcao = tool_call.function.name
            argumentos = json.loads(tool_call.function.arguments)
            print(f"  [LOG INTERNO] LLM acionou '{nome_funcao}' com args: {argumentos}")

            if nome_funcao == "consultar_status_pedido":
                resultado_tool = consultar_status_pedido(**argumentos)

                # Devolve o resultado da ferramenta para o histórico
                mensagens.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": nome_funcao,
                        "content": resultado_tool,
                    }
                )

        # Segunda chamada: o LLM lê o retorno da tool e gera a resposta final
        resposta_final = client.chat.completions.create(
            model=MODELO,
            messages=mensagens,
            temperature=0.0,
        )
        return resposta_final.choices[0].message.content

    return msg_assistente.content

if __name__ == "__main__":
    print("--- TESTE AGENTE PURO ---")
    print(executar_agente_puro("Onde está meu pedido PED-122?"))