from langchain_core.messages import HumanMessage
from agente2 import app  # Nota: se o Python reclamar do número no início, renomeie para agente_langgraph.py

def rodar_cenario(titulo: str, entrada_usuario: str):
    print(f"\n{'='*50}")
    print(f"CENÁRIO: {titulo}")
    print(f"USUÁRIO: {entrada_usuario}")
    print("-" * 50)

    estado_inicial = {"messages": [HumanMessage(content=entrada_usuario)]}

    # `stream` permite observar cada transição de nó acontecendo em tempo real
    for evento in app.stream(estado_inicial, stream_mode="updates"):
        for nome_no, dados_no in evento.items():
            ultima_msg = dados_no["messages"][-1]
            if nome_no == "agente" and ultima_msg.tool_calls:
                print(f"[Nó: {nome_no}] Decidiu chamar tool -> {ultima_msg.tool_calls[0]['args']}")
            elif nome_no == "ferramentas":
                print(f"[Nó: {nome_no}] Retorno estruturado -> {ultima_msg.content}")
            elif nome_no == "agente":
                print(f"[Nó: {nome_no}] Resposta Final:\n{ultima_msg.content}")

if __name__ == "__main__":
    # 1. CASO ESPERADO (Caminho feliz)
    rodar_cenario(
        "1. Caso Esperado (Pedido válido)",
        "Olá, gostaria de saber como está o meu pedido PED-102."
    )

    # 2. AMBIGUIDADE (Falta parâmetro obrigatório)
    rodar_cenario(
        "2. Ambiguidade (Usuário não informa o código)",
        "Comprei um teclado ontem e quero saber se já saiu para entrega."
    )

    # 3. FALHA / DADO INEXISTENTE (Alucinação controlada)
    rodar_cenario(
        "3. Falha de Negócio (Pedido inexistente no banco)",
        "Verifica pra mim o pedido PED-999, por favor."
    )

    # 4. FORA DE ESCOPO (Tentativa de desvio de papel)
    rodar_cenario(
        "4. Fora de Escopo (Pergunta não relacionada)",
        "Você pode me ajudar a escrever um código em Python para ordenar listas?"
    )