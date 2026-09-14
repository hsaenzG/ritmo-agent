#!/usr/bin/env bash
#
# setup.sh — prepara el entorno del proyecto ritmo-agent.
#
# Crea el entorno virtual, lo activa e instala las dependencias del agente de
# Strands. Con la bandera --langgraph instala además las dependencias de la
# variante de LangGraph (Parte 6 del video).
#
# Uso:
#   ./setup.sh              # instala solo lo del agente de Strands
#   ./setup.sh --langgraph  # instala también las dependencias de LangGraph
#
# Después del setup, activa el entorno en tu terminal con:
#   source .venv/bin/activate

set -euo pipefail

VENV_DIR=".venv"

echo "==> Creando entorno virtual en ${VENV_DIR}"
python3 -m venv "${VENV_DIR}"

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "==> Actualizando pip"
python -m pip install --upgrade pip

echo "==> Instalando dependencias del agente (requirements.txt)"
pip install -r requirements.txt

if [[ "${1:-}" == "--langgraph" ]]; then
  echo "==> Instalando dependencias de la variante LangGraph (requirements-langgraph.txt)"
  pip install -r requirements-langgraph.txt
fi

echo "==> Instalando el starter toolkit de AgentCore (para el deploy)"
pip install bedrock-agentcore-starter-toolkit

echo ""
echo "Listo. Para empezar:"
echo "  source .venv/bin/activate"
echo ""
echo "Recuerda configurar tus credenciales de AWS y la región antes de correr el agente:"
echo "  export AWS_REGION=us-west-2"
echo ""
echo "Correr el agente local (sin AgentCore):"
echo "  python agente_local.py"
echo ""
echo "Correr el agente con AgentCore (servidor local en el puerto 8080):"
echo "  python agente.py"
