#!/usr/bin/env python3
import argparse
import random
import time
import sys
import os
from datetime import datetime

# =========================
# CONFIGURAÇÕES
# =========================

LOG_FILE_PATH = "/export/logs/openresty/access.log"

ATTACKER_IPS = [
    "45.83.91.5",
    "103.27.124.10",
    "185.220.101.15"
]

LEGIT_IPS = [
    "189.22.45.90",
    "177.84.12.9",
    "191.32.98.11",
    "200.221.149.3"
]

DOMAINS = [
    "portal42.com",
    "empresa10.com.br",
    "api12.net",
    "cloud77.net",
    "blog7.com",
    "loja10.com"
]

ENDPOINTS_ATTACK = [
    "/login",
    "/admin",
    "/wp-login.php",
    "/api/v1/auth"
]

ENDPOINTS_LEGIT = [
    "/",
    "/produtos",
    "/contato",
    "/blog",
    "/sobre"
]

ATTACK_UA = [
    "Mozilla/5.0 (compatible; AttackBot/1.0)",
    "python-requests/2.31.0"
]

LEGIT_UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Chrome/121.0"
]

STATUS_ATTACK = [401, 403, 404]
STATUS_LEGIT = [200, 200, 200, 301, 302]

# =========================
# FUNÇÕES
# =========================

def timestamp():
    return datetime.now().strftime("%d/%b/%Y:%H:%M:%S -0300")

def write_log(f, ip, domain, endpoint, status, ua):
    line = (
        f"{timestamp():<28} {ip:<15} {domain:<20} "
        f"GET {endpoint:<18} {status:<4} {ua}"
    )
    f.write(line + "\n")
    f.flush()

def attack_1ip_1site(f, ip, domain):
    write_log(
        f,
        ip,
        domain,
        random.choice(ENDPOINTS_ATTACK),
        random.choice(STATUS_ATTACK),
        random.choice(ATTACK_UA)
    )

def attack_1ip_multisite(f, ip):
    write_log(
        f,
        ip,
        random.choice(DOMAINS),
        random.choice(ENDPOINTS_ATTACK),
        random.choice(STATUS_ATTACK),
        random.choice(ATTACK_UA)
    )

def attack_multiip_1site(f, domain):
    write_log(
        f,
        random.choice(ATTACKER_IPS),
        domain,
        random.choice(ENDPOINTS_ATTACK),
        random.choice(STATUS_ATTACK),
        random.choice(ATTACK_UA)
    )

def legit_traffic(f):
    write_log(
        f,
        random.choice(LEGIT_IPS),
        random.choice(DOMAINS),
        random.choice(ENDPOINTS_LEGIT),
        random.choice(STATUS_LEGIT),
        random.choice(LEGIT_UA)
    )

def realistic_mode(f, ip_fixed, domain_fixed):
    roll = random.randint(1, 100)

    if roll <= 60:
        legit_traffic(f)
    elif roll <= 70:
        attack_1ip_1site(f, ip_fixed, domain_fixed)
    elif roll <= 80:
        attack_1ip_multisite(f, ip_fixed)
    elif roll <= 95:
        attack_multiip_1site(f, domain_fixed)
    else:
        for _ in range(random.randint(3, 6)):
            attack_1ip_multisite(f, ip_fixed)

# =========================
# MAIN
# =========================

def main():
    parser = argparse.ArgumentParser(
        description="Simulador realista de ataques e tráfego legítimo",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--attack",
        choices=["1ip_1site", "1ip_multisite", "multiip_1site", "realistic"],
        help=(
            "Sintaxes disponíveis:\n\n"
            "  --attack 1ip_1site       → Um IP atacando um único site\n"
            "  --attack 1ip_multisite   → Um IP atacando vários sites\n"
            "  --attack multiip_1site   → Vários IPs atacando um único site\n"
            "  --attack realistic       → Tráfego legítimo + ataques misturados\n"
        )
    )

    parser.add_argument(
        "--duration",
        type=int,
        help="Duração em segundos (ex: 300 = 5 minutos)"
    )

    parser.add_argument(
        "--min-attacks",
        type=int,
        default=0,
        help="Número mínimo garantido de ataques por IP atacante"
    )

    # Se rodar sem argumentos → help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if not args.attack or not args.duration:
        print("\n❌ Erro: --attack e --duration são obrigatórios.\n")
        parser.print_help()
        sys.exit(1)

    # Garante diretório
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    domain_fixed = random.choice(DOMAINS)
    end_time = time.time() + args.duration

    with open(LOG_FILE_PATH, "a") as f:

        # =========================
        # FASE 1 — MÍNIMO GARANTIDO
        # =========================
        if args.min_attacks > 0:
            for ip in ATTACKER_IPS:
                for _ in range(args.min_attacks):
                    attack_1ip_multisite(f, ip)
                    time.sleep(random.uniform(0.1, 0.4))

        # =========================
        # FASE 2 — EXECUÇÃO NORMAL
        # =========================
        ip_fixed = random.choice(ATTACKER_IPS)

        while time.time() < end_time:
            if args.attack == "1ip_1site":
                attack_1ip_1site(f, ip_fixed, domain_fixed)
            elif args.attack == "1ip_multisite":
                attack_1ip_multisite(f, ip_fixed)
            elif args.attack == "multiip_1site":
                attack_multiip_1site(f, domain_fixed)
            elif args.attack == "realistic":
                realistic_mode(f, ip_fixed, domain_fixed)

            time.sleep(random.uniform(0.2, 1.0))

if __name__ == "__main__":
    main()
