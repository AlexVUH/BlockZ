#!/bin/bash

### =========================
### CONFIGURAÇÕES
### =========================
SET_NAME="blacklistz"
TIMEOUT=1800   # 30 minutos
LOG_DIR="/export/logs"
LOG_TXT="$LOG_DIR/blockz.log"
LOG_JSON="$LOG_DIR/block.json"

### =========================
### CORES
### =========================
GREEN="\e[32m"
YELLOW="\e[33m"
RED="\e[31m"
BLUE="\e[34m"
RESET="\e[0m"

### =========================
### EXIT CODES
### =========================
# 0 = sucesso
# 1 = erro genérico
# 2 = uso inválido
# 3 = recurso inexistente (ipset)
# 4 = IP já bloqueado
# 5 = IP não bloqueado

### =========================
### FUNÇÕES AUXILIARES
### =========================
log_block() {
  local ip="$1"
  local ts
  ts="$(date '+%Y-%m-%d %H:%M:%S')"

  echo "$ts $ip" >> "$LOG_TXT"
  echo "{\"datetime\":\"$ts\",\"ip\":\"$ip\"}" >> "$LOG_JSON"
}

require_root() {
  if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Erro: execute como root${RESET}"
    exit 1
  fi
}

check_ipset_exists() {
  if ! ipset list "$SET_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW}Aviso: ipset \"$SET_NAME\" não existe${RESET}"
    echo "Crie com:"
    echo "ipset create $SET_NAME hash:ip timeout $TIMEOUT"
    return 1
  fi
  return 0
}

ensure_iptables_rule() {
  if ! iptables -C INPUT -m set --match-set "$SET_NAME" src -j DROP 2>/dev/null; then
    iptables -I INPUT -m set --match-set "$SET_NAME" src -j DROP
  fi
}

help_msg() {
  cat <<EOF
Uso:
  $0 fw <IP> add
  $0 fw <IP> del
  $0 fw <IP> check
  $0 fw list
  $0 fw flush
  $0 help

Exit codes:
  0  Sucesso
  1  Erro genérico
  2  Uso inválido
  3  ipset inexistente
  4  IP já bloqueado
  5  IP não bloqueado

Requisitos:
  - ipset instalado
  - iptables presente
  - ipset "$SET_NAME" criado manualmente:
      ipset create $SET_NAME hash:ip timeout $TIMEOUT
EOF
}

### =========================
### INÍCIO
### =========================
require_root

ACTION="$1"
IP="$2"
CMD="$3"

case "$ACTION" in
  help|"")
    help_msg
    exit 0
    ;;
  fw)
    ;;
  *)
    echo -e "${RED}Erro: comando inválido \"$ACTION\"${RESET}"
    exit 2
    ;;
esac

# comandos que NÃO precisam de IP
if [[ "$IP" == "list" || "$IP" == "flush" ]]; then
  CMD="$IP"
  IP=""
fi

# valida ipset (apenas aviso)
check_ipset_exists || true

case "$CMD" in
  add)
    if ! check_ipset_exists; then
      exit 3
    fi

    ensure_iptables_rule

    if ipset test "$SET_NAME" "$IP" >/dev/null 2>&1; then
      echo -e "${YELLOW}$IP IP já está bloqueado${RESET}"
      exit 4
    fi

    ipset add "$SET_NAME" "$IP" timeout "$TIMEOUT"
    log_block "$IP"
    echo -e "${GREEN}$IP IP bloqueado com sucesso${RESET}"
    exit 0
    ;;

  del)
    if ! check_ipset_exists; then
      exit 3
    fi

    if ! ipset test "$SET_NAME" "$IP" >/dev/null 2>&1; then
      echo -e "${BLUE}$IP IP não está bloqueado${RESET}"
      exit 5
    fi

    ipset del "$SET_NAME" "$IP"
    echo -e "${GREEN}$IP IP removido do bloqueio${RESET}"
    exit 0
    ;;

  check)
    if ! check_ipset_exists; then
      exit 3
    fi

    if ipset test "$SET_NAME" "$IP" >/dev/null 2>&1; then
      echo -e "${GREEN}$IP IP está bloqueado${RESET}"
      exit 0
    else
      echo -e "${BLUE}$IP IP não está bloqueado${RESET}"
      exit 5
    fi
    ;;

  list)
    if ! check_ipset_exists; then
      exit 3
    fi
    ipset list "$SET_NAME"
    exit 0
    ;;

  flush)
    if ! check_ipset_exists; then
      exit 3
    fi
    ipset flush "$SET_NAME"
    echo -e "${GREEN}Blacklist esvaziada${RESET}"
    exit 0
    ;;

  *)
    echo -e "${RED}Erro: comando inválido \"$CMD\"${RESET}"
    echo "Use: add | del | check | list | flush"
    exit 2
    ;;
esac
