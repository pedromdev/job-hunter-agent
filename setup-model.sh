#!/usr/bin/env bash
set -e

# ──────────────────────────────────────────────
# Job Hunter Agent — Setup do Modelo de IA
# ──────────────────────────────────────────────
# Configura o provedor/modelo no config.json
# Opções: Gemini (grátis, 1M contexto), DeepSeek (pago)
# ──────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"
ENV_FILE="$SCRIPT_DIR/.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}ℹ${NC} $1"; }
ok()    { echo -e "${GREEN}✔${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
err()   { echo -e "${RED}✘${NC} $1"; }

# ── Detectar config.json existente ────────────
detect_current_provider() {
  if [[ -f "$CONFIG_FILE" ]]; then
    CURRENT_PROVIDER=$(python3 -c "
import json
try:
    with open('$CONFIG_FILE') as f:
        c = json.load(f)
    preset = c.get('agents', {}).get('defaults', {}).get('modelPreset', 'primary')
    p = c.get('modelPresets', {}).get(preset, {})
    prov = p.get('provider', '')
    model = p.get('model', '')
    print(f'{prov}|{model}')
except:
    print('|')
" 2>/dev/null) || CURRENT_PROVIDER="|"
    echo "$CURRENT_PROVIDER"
  else
    echo "|"
  fi
}

# ── Gerar config.json ─────────────────────────
generate_config() {
  local provider_key="$1"
  local provider_label="$2"
  local model="$3"
  local api_key_var="$4"
  local preset_name="$5"
  local temperature="$6"
  local max_tokens="$7"
  local ctx_window="$8"

  cat > "$CONFIG_FILE" << JSONEOF
{
  "providers": {
    "$provider_key": {
      "apiKey": "\${${api_key_var}}"
    }
  },
  "modelPresets": {
    "$preset_name": {
      "label": "$provider_label",
      "provider": "$provider_key",
      "model": "$model",
      "maxTokens": $max_tokens,
      "contextWindowTokens": $ctx_window,
      "temperature": $temperature
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "\${TELEGRAM_TOKEN}",
      "allowFrom": ["\${TELEGRAM_ALLOW_FROM}"]
    },
    "websocket": {
      "enabled": false
    }
  },
  "agents": {
    "defaults": {
      "modelPreset": "$preset_name",
      "provider": "$provider_key",
      "model": "$model",
      "maxTokens": $max_tokens,
      "contextWindowTokens": $ctx_window,
      "temperature": $temperature,
      "dream": {
        "enabled": true,
        "intervalM": 240
      }
    }
  },
  "tools": {
    "web": {
      "search": { "enabled": true },
      "fetch": { "enabled": true }
    },
    "restrictToWorkspace": false
  },
  "gateway": {
    "host": "0.0.0.0",
    "port": 18790
  }
}
JSONEOF
  ok "config.json gerado com $provider_label"
}

# ── Atualizar variável no .env ────────────────
update_env() {
  local var_name="$1"
  local var_value="$2"

  if [[ -f "$ENV_FILE" ]]; then
    if grep -q "^${var_name}=" "$ENV_FILE"; then
      sed -i "s|^${var_name}=.*|${var_name}=${var_value}|" "$ENV_FILE"
    else
      echo "${var_name}=${var_value}" >> "$ENV_FILE"
    fi
  else
    echo "${var_name}=${var_value}" > "$ENV_FILE"
  fi
  ok ".env atualizado com ${var_name}"
}

# ── Setup Gemini ──────────────────────────────
setup_gemini() {
  echo ""
  info "Você escolheu: ${GREEN}Google Gemini${NC} (grátis, sem cartão de crédito)"
  echo ""
  info "Para obter sua chave da API Gemini:"
  info "1. Acesse https://aistudio.google.com/apikey"
  echo "   (faça login com sua conta Google)"
  info "2. Clique em 'Create API Key'"
  info "3. Copie a chave gerada"
  echo ""

  read -rp "Cole sua API key Gemini: " api_key
  api_key="${api_key:-}"

  if [[ -z "$api_key" ]]; then
    err "API key não pode ficar vazia"
    exit 1
  fi

  update_env "GEMINI_API_KEY" "$api_key"
  generate_config "gemini" "Gemini" "gemini-2.5-flash" "GEMINI_API_KEY" "primary" "0.3" "8192" "1048576"

  info "Você pode testar com: nanobot agent -m 'Olá'"
}

# ── Setup DeepSeek ────────────────────────────
setup_deepseek() {
  echo ""
  info "Você escolheu: ${GREEN}DeepSeek${NC} (pago por uso, ~\$0.14/M tokens)"
  echo ""
  info "Para obter sua chave da API DeepSeek:"
  info "1. Acesse https://platform.deepseek.com"
  echo "   (crie uma conta e faça login)"
  info "2. Vá em 'API Keys' no menu lateral"
  info "3. Clique em 'Create new key'"
  info "4. Copie a chave (começa com sk-)"
  echo ""
  info "💰 DeepSeek V4 Flash custa ~\$0.14 por milhão de tokens de entrada"
  info "   Um chat típico custa centavos de dólar."
  echo ""

  read -rp "Cole sua API key DeepSeek (sk-...): " api_key
  api_key="${api_key:-}"

  if [[ -z "$api_key" ]]; then
    err "API key não pode ficar vazia"
    exit 1
  fi

  update_env "DEEPSEEK_API_KEY" "$api_key"
  generate_config "deepseek" "DeepSeek" "deepseek-chat" "DEEPSEEK_API_KEY" "primary" "0.3" "8192" "65536"

  info "Você pode testar com: nanobot agent -m 'Olá'"
}

# ── Validar configuração ──────────────────────
validate_config() {
  echo ""
  info "Validando configuração..."

  NANOBOT_PATH=""
  if command -v nanobot &>/dev/null; then
    NANOBOT_PATH="$(command -v nanobot 2>/dev/null)"
    if [ ! -x "$NANOBOT_PATH" ]; then
      NANOBOT_PATH=""
    fi
  fi

  if [ -n "$NANOBOT_PATH" ]; then
    if nanobot status 2>&1 | head -20; then
      ok "Nanobot reconheceu a configuração"
    else
      warn "nanobot status falhou — verifique se a API key está correta"
    fi
  else
    warn "nanobot não encontrado no PATH. A configuração será usada dentro do Docker."
    info "Para testar, rode: docker compose run --rm job-hunter-cli agent -m 'Olá'"
  fi
}

# ── Menu principal ────────────────────────────
main() {
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║     Job Hunter Agent — Setup do Modelo       ║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
  echo ""

  CURRENT=$(detect_current_provider)
  IFS='|' read -r CUR_PROV CUR_MODEL <<< "$CURRENT"

  if [[ -n "$CUR_PROV" && "$CUR_PROV" != " " ]]; then
    info "Configuração atual: ${CYAN}${CUR_PROV}${NC} / ${CYAN}${CUR_MODEL}${NC}"
    echo ""
    read -rp "Deseja manter a configuração atual? (S/n): " keep
    if [[ "${keep,,}" != "n" ]]; then
      ok "Configuração mantida"
      exit 0
    fi
    echo ""
  fi

  echo -e "Escolha um provedor de IA:"
  echo ""
  echo -e "  ${GREEN}1)${NC} Google Gemini — Grátis (sem cartão de crédito)"
  echo -e "     Modelo: Gemini 2.5 Flash"
  echo -e "     Limites: 1.500 req/dia, 1M tokens de contexto"
  echo ""
  echo -e "  ${GREEN}2)${NC} DeepSeek — Pago por uso (~\$0.14/M tokens)"
  echo -e "     Modelo: DeepSeek V4 Flash"
  echo -e "     Qualidade excelente, 1M tokens de contexto"
  echo ""
  read -rp "Opção (1/2) [1]: " opt
  opt="${opt:-1}"

  case "$opt" in
    1) setup_gemini ;;
    2) setup_deepseek ;;
    *) err "Opção inválida"; exit 1 ;;
  esac

  echo ""
  info "──────────────────────────────────────────"
  ok "Configuração concluída!"
  echo ""
  info "Resumo:"
  echo -e "  • Provedor:    ${CYAN}$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['modelPresets']['primary']['label'])" 2>/dev/null)${NC}"
  echo -e "  • Modelo:      ${CYAN}$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['modelPresets']['primary']['model'])" 2>/dev/null)${NC}"
  echo -e "  • Arquivos:    ${CONFIG_FILE}"
  echo -e "  •             ${ENV_FILE}"
  echo ""
  info "Próximos passos:"
  echo "  1. Preencha seu RESUME.md com seus dados"
  echo "  2. Configure o TELEGRAM_TOKEN no .env"
  echo "  3. Rode: docker compose build && docker compose up -d"
  echo ""

  validate_config

  echo ""
  info "Quer trocar de provedor depois? Basta rodar este script novamente."
  echo ""
}

main "$@"
