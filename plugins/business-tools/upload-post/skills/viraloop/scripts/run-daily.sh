#!/bin/bash
# Wrapper que carga credenciales y ejecuta viraloop diario
# Usado por el cron job para tener las variables de entorno correctas

set -e

SKILL_DIR="$(dirname "$0")/.."
cd "$SKILL_DIR"

# Cargar credenciales locales
if [ -f "/home/node/clawd/skills/larry/.env.local" ]; then
  export $(grep -v '^#' /home/node/clawd/skills/larry/.env.local | xargs)
fi

# También cargar de upload-post si existe
if [ -f "/home/node/clawd/skills/upload-post/.env.local" ]; then
  export $(grep -v '^#' /home/node/clawd/skills/upload-post/.env.local | xargs)
fi

echo "✅ Credenciales cargadas"
echo "   UPLOADPOST_TOKEN: ${UPLOADPOST_TOKEN:0:20}..."
echo "   UPLOADPOST_USER: ${UPLOADPOST_PROFILE:-influencersde}"
echo "   GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."

# Exportar usuario si no está definido
export UPLOADPOST_USER="${UPLOADPOST_PROFILE:-influencersde}"

echo ""
echo "🚀 Ejecutando viraloop..."
