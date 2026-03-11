#!/usr/bin/env bash
# ============================================================
# TCC — Script de Benchmark Automatizado
# Java 25 Virtual Threads vs Go 1.25 Goroutines vs Quarkus Native
#
# Uso:
#   ./scripts/benchmarks/run_benchmarks.sh
#   ./scripts/benchmarks/run_benchmarks.sh --scenario stress
#   ./scripts/benchmarks/run_benchmarks.sh --rounds 1
#
# Saída:
#   results/runs/<timestamp>/<backend>_<scenario>_round<N>.json  — k6 métricas
#   results/runs/<timestamp>/<backend>_<scenario>_round<N>.mem   — RAM do container
# ============================================================

set -euo pipefail

# ── Configuração ──────────────────────────────────────────────
JAVA_URL="${JAVA_URL:-http://localhost:8081/payments}"
GO_URL="${GO_URL:-http://localhost:8082/payments}"
QUARKUS_URL="${QUARKUS_URL:-http://localhost:8083/payments}"
REDIS_CONTAINER="${REDIS_CONTAINER:-tcc-redis}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K6_SCRIPT="$SCRIPT_DIR/stress_test.js"
ROUNDS="${ROUNDS:-3}"
SCENARIO_FILTER="${SCENARIO_FILTER:-all}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="$SCRIPT_DIR/../../results/runs/$TIMESTAMP"

# ── Parse de argumentos ───────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --scenario) SCENARIO_FILTER="$2"; shift 2 ;;
    --rounds)   ROUNDS="$2";          shift 2 ;;
    *) echo "Argumento desconhecido: $1"; exit 1 ;;
  esac
done

# ── Validação de dependências ─────────────────────────────────
command -v k6     >/dev/null 2>&1 || { echo "k6 nao encontrado. Instale: brew install k6"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker nao encontrado."; exit 1; }

mkdir -p "$RESULTS_DIR"

echo ""
echo "============================================================"
echo "  TCC Benchmark Runner -- $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Rounds por cenario : $ROUNDS"
echo "  Cenario(s)         : $SCENARIO_FILTER"
echo "  Resultados em      : results/runs/$TIMESTAMP"
echo "============================================================"
echo ""

# ── Funções auxiliares ────────────────────────────────────────

flush_redis() {
  echo "  [redis] FLUSHALL..."
  docker exec "$REDIS_CONTAINER" redis-cli FLUSHALL > /dev/null 2>&1 \
    || { echo "  AVISO: nao foi possivel limpar Redis"; }
  sleep 1
}

run_scenario() {
  local backend="$1"   # java | go
  local url="$2"
  local scenario="$3"
  local round="$4"
  local output_file="$RESULTS_DIR/${backend}_${scenario}_round${round}.json"
  local mem_file="$RESULTS_DIR/${backend}_${scenario}_round${round}.mem"

  # Mapeia backend para nome do container Docker
  local container_name
  case "$backend" in
    java)    container_name="tcc-backend-java"    ;;
    go)      container_name="tcc-backend-go"      ;;
    quarkus) container_name="tcc-backend-quarkus" ;;
    *)    container_name="tcc-backend-$backend" ;;
  esac

  echo "  >> [$backend] cenario=$scenario round=$round/$ROUNDS"
  flush_redis

  # Captura RAM do container em streaming enquanto o k6 roda.
  # docker stats sem --no-stream emite uma linha por segundo automaticamente.
  # Formato capturado: "256MiB / 8GiB" — o analyze_results.py extrai o pico.
  docker stats --format "{{.MemUsage}}" "$container_name" >> "$mem_file" 2>/dev/null &
  local STATS_PID=$!

  # Executa o k6
  k6 run \
    --env SCENARIO="$scenario" \
    --env TARGET_URL="$url" \
    --out "json=$output_file" \
    --quiet \
    "$K6_SCRIPT" 2>&1 | tail -5 || true

  # Para a coleta de memória
  kill "$STATS_PID" 2>/dev/null || true
  wait "$STATS_PID" 2>/dev/null || true

  local mem_samples
  mem_samples=$(wc -l < "$mem_file" 2>/dev/null || echo "0")
  echo "    OK: $(basename "$output_file")  |  RAM: $mem_samples amostras -> $(basename "$mem_file")"
}

# ── Definição dos cenários ────────────────────────────────────
declare -a SCENARIOS
if [[ "$SCENARIO_FILTER" == "all" ]]; then
  SCENARIOS=("baseline" "stress" "spike")
else
  SCENARIOS=("$SCENARIO_FILTER")
fi

BACKENDS=("java:$JAVA_URL" "go:$GO_URL" "quarkus:$QUARKUS_URL")

# ── Execução principal ────────────────────────────────────────
total_runs=$(( ${#SCENARIOS[@]} * ${#BACKENDS[@]} * ROUNDS ))
current=0

for scenario in "${SCENARIOS[@]}"; do
  echo "------------------------------------------------------------"
  echo "  CENARIO: $(echo "$scenario" | tr '[:lower:]' '[:upper:]')"
  echo "------------------------------------------------------------"

  for round in $(seq 1 "$ROUNDS"); do
    echo ""
    echo "  [ Round $round / $ROUNDS ]"

    for backend_config in "${BACKENDS[@]}"; do
      backend="${backend_config%%:*}"
      url="${backend_config#*:}"
      current=$((current + 1))
      echo ""
      echo "  [$current/$total_runs] Backend: $backend"
      run_scenario "$backend" "$url" "$scenario" "$round"
    done
  done

  echo ""
done

echo ""
echo "============================================================"
echo "  Benchmark concluido!"
echo "  Resultados: results/runs/$TIMESTAMP"
echo "============================================================"
echo ""
echo "  Gerar relatorio estatistico com memoria:"
echo "  python3 scripts/benchmarks/analyze_results.py results/runs/$TIMESTAMP"
echo "  python3 scripts/benchmarks/analyze_results.py results/runs/$TIMESTAMP --format markdown"
echo ""
