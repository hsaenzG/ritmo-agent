"""
crear_memoria.py — crea el recurso de AgentCore Memory para Ritmo.

Se corre UNA sola vez. Imprime el ID del recurso de memoria. Copia ese ID a la
variable de entorno RITMO_MEMORY_ID y `agente.py` activará la memoria solo.

    python crear_memoria.py
    export RITMO_MEMORY_ID=<el-id-que-imprime>

Necesita credenciales de AWS con acceso a AgentCore Memory en tu región.
Después de grabar, borra el recurso para no dejar cosas colgando en la cuenta.
"""

import os

from bedrock_agentcore.memory import MemoryClient


def main():
    region = os.environ.get("AWS_REGION", "us-west-2")
    client = MemoryClient(region_name=region)

    memoria = client.create_memory(
        name="RitmoMemory",
        description="Memoria de conversación del asistente Ritmo (demo).",
    )

    memory_id = memoria.get("id")
    print("\nRecurso de memoria creado.")
    print(f"  ID: {memory_id}")
    print("\nExporta esto en tu terminal para activarlo en el agente:")
    print(f"  export RITMO_MEMORY_ID={memory_id}\n")


if __name__ == "__main__":
    main()
