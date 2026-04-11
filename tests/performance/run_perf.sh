#!/bin/bash

set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

HostUrl="http://localhost:8000"
Users=10
SpawnRate=2
RunTimeSec=120
Products=30
BuyerPoolSize=200
DbPath="../../data/deliverinno.db"

show_help() {
  cat << EOF
Usage: $0 [OPTIONS]

Options:
  --host-url URL            Target host URL (default: $HostUrl)
  --users NUM               Number of users (default: $Users)
  --spawn-rate NUM          User spawn rate (default: $SpawnRate)
  --run-time-sec SEC        Test duration in seconds (default: $RunTimeSec)
  --products NUM            Number of products (default: $Products)
  --buyer-pool-size NUM     Buyer pool size (default: $BuyerPoolSize)
  --db-path PATH            Database path (default: $DbPath)
  --help                    Show this help message

Examples:
  $0
  $0 --users 20 --spawn-rate 5
  $0 --host-url http://example.com --run-time-sec 300
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --help) show_help ;;
    --host-url) HostUrl="$2"; shift 2 ;;
    --users) Users="$2"; shift 2 ;;
    --spawn-rate) SpawnRate="$2"; shift 2 ;;
    --run-time-sec) RunTimeSec="$2"; shift 2 ;;
    --products) Products="$2"; shift 2 ;;
    --buyer-pool-size) BuyerPoolSize="$2"; shift 2 ;;
    --db-path) DbPath="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; echo "Use --help for usage info"; exit 1 ;;
  esac
done

echo "==> Init test users/products in SQLite..."
poetry run python ./init_test_users.py --db-path "$DbPath" --products "$Products" --buyer-pool-size "$BuyerPoolSize"

echo "==> Starting locust..."
poetry run locust \
  -f ./locustfile.py \
  --host "$HostUrl" \
  --headless \
  -u "$Users" \
  -r "$SpawnRate" \
  -t "${RunTimeSec}s"
