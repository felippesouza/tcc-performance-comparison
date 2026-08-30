#!/usr/bin/env bash
# ============================================================
# TCC — Script de Benchmark GKE (Kubernetes)
# Java 25 Virtual Threads vs Go 1.25 Goroutines vs Quarkus Native
#
# Uso:
#   ./scripts/benchmarks/run_benchmarks_gke.sh
#   ./scripts/benchmarks/run_benchmarks_gke.sh --scenario stress
#   ./scripts/benchmarks/run_benchmarks_gke.sh --rounds 1
# ============================================================

set -euo pipefail

# ── Configuração ──────────────────────────────────────────────
NAMESPACE="tcc"
ROUNDS="${ROUNDS:-3}"
SCENARIO_FILTER="${SCENARIO_FILTER:-all}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="$SCRIPT_DIR/../../results/runs_gke/$TIMESTAMP"

# ── Parse de argumentos ───────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --scenario) SCENARIO_FILTER="$2"; shift 2 ;;
    --rounds)   ROUNDS="$2";          shift 2 ;;
    *) echo "Argumento desconhecido: $1"; exit 1 ;;
  esac
done

# ── Validação de dependências ─────────────────────────────────
command -v kubectl >/dev/null 2>&1 || { echo "kubectl nao encontrado. Configure o gcloud/kubectl."; exit 1; }

mkdir -p "$RESULTS_DIR"

echo ""
echo "============================================================"
echo "  TCC GKE Benchmark Runner -- $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Rounds por cenario : $ROUNDS"
echo "  Cenario(s)         : $SCENARIO_FILTER"
echo "  Namespace K8s      : $NAMESPACE"
echo "  Resultados em      : results/runs_gke/$TIMESTAMP"
echo "============================================================"
echo ""

# ── Funções auxiliares ────────────────────────────────────────

flush_redis() {
  echo "  [redis] FLUSHALL..."
  kubectl exec -n "$NAMESPACE" deploy/redis-cache -- redis-cli FLUSHALL > /dev/null 2>&1 \
    || { echo "  AVISO: nao foi possivel limpar Redis"; }
  sleep 1
}

isolate_backend() {
  local active="$1"
  echo "  [k8s] Isolando backend: $active"
  
  # Define réplicas
  local java_rep=0
  local go_rep=0
  local quarkus_rep=0
  
  case "$active" in
    java)    java_rep=1 ;;
    go)      go_rep=1 ;;
    quarkus) quarkus_rep=1 ;;
  esac

  kubectl scale deployment -n "$NAMESPACE" backend-java --replicas=$java_rep >/dev/null
  kubectl scale deployment -n "$NAMESPACE" backend-go --replicas=$go_rep >/dev/null
  kubectl scale deployment -n "$NAMESPACE" backend-quarkus --replicas=$quarkus_rep >/dev/null

  # Aguarda o deploy ativo ficar Pronto
  echo "  [k8s] Aguardando inicializacao do backend-$active..."
  kubectl rollout status -n "$NAMESPACE" deployment/backend-$active --timeout=90s >/dev/null
  sleep 2
}

collect_memory() {
  local backend="$1"
  local mem_file="$2"
  local stop_flag_file="$3"

  # Encontra o nome exato do Pod do backend
  local pod_name=""
  while [[ -z "$pod_name" ]]; do
    pod_name=$(kubectl get pod -n "$NAMESPACE" -l app=backend-$backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
    sleep 0.5
  done

  # Loop de captura de memória em background
  while [[ -f "$stop_flag_file" ]]; do
    local mem_usage
    mem_usage=$(kubectl top pod -n "$NAMESPACE" "$pod_name" --no-headers 2>/dev/null | awk '{print $3}' || true)
    if [[ -n "$mem_usage" ]]; then
      # Limpa e converte '789Mi' para '789MiB / 16GiB' para compatibilidade com analyze_results.py
      local clean_mem
      clean_mem=$(echo "$mem_usage" | tr -d 'i') # remove o 'i' de 'Mi' ou 'Gi' -> '789M'
      echo "${clean_mem}B / 16GiB" >> "$mem_file"
    fi
    sleep 2
  done
}

run_scenario() {
  local backend="$1"
  local scenario="$2"
  local round="$3"
  
  local output_file="$RESULTS_DIR/${backend}_${scenario}_round${round}.json"
  local mem_file="$RESULTS_DIR/${backend}_${scenario}_round${round}.mem"
  local stop_flag="/tmp/mem_stop_${backend}_${scenario}_r${round}"

  local target_url
  case "$backend" in
    java)    target_url="http://backend-java:8081/payments" ;;
    go)      target_url="http://backend-go:8082/payments" ;;
    quarkus) target_url="http://backend-quarkus:8083/payments" ;;
  esac

  echo "  >> [$backend] cenario=$scenario round=$round/$ROUNDS"
  
  # Garante isolamento de processo e limpa Redis
  isolate_backend "$backend"
  flush_redis

  # Inicia coleta de memória em background
  touch "$stop_flag"
  collect_memory "$backend" "$mem_file" "$stop_flag" &
  local MEM_PID=$!

  # Executa o k6 dentro do cluster usando kubectl run overrides
  echo "  [k6] Iniciando pod de carga..."
  kubectl run k6-benchmark -n "$NAMESPACE" \
    --image=grafana/k6:0.51.0 \
    --restart=Never \
    --overrides='{
      "spec": {
        "containers": [
          {
            "name": "helper",
            "image": "alpine:3.18",
            "command": ["sh", "-c", "sleep 3600"],
            "volumeMounts": [
              {
                "name": "shared-volume",
                "mountPath": "/shared"
              }
            ]
          },
          {
            "name": "k6",
            "image": "grafana/k6:0.51.0",
            "command": ["k6", "run", "--out", "json=/shared/result.json", "/scripts/stress_test.js"],
            "env": [
              {"name": "TARGET_URL", "value": "'"$target_url"'"},
              {"name": "SCENARIO", "value": "'"$scenario"'"}
            ],
            "volumeMounts": [
              {
                "name": "script-volume",
                "mountPath": "/scripts"
              },
              {
                "name": "shared-volume",
                "mountPath": "/shared"
              }
            ]
          }
        ],
        "volumes": [
          {
            "name": "script-volume",
            "configMap": {
              "name": "k6-script"
            }
          },
          {
            "name": "shared-volume",
            "emptyDir": {}
          }
        ]
      }
    }' >/dev/null

  # Aguarda o container helper comecar a rodar
  while true; do
    local helper_state
    helper_state=$(kubectl get pod -n "$NAMESPACE" k6-benchmark -o jsonpath='{.status.containerStatuses[?(@.name=="helper")].state.running}' 2>/dev/null || true)
    if [[ -n "$helper_state" ]]; then
      break
    fi
    sleep 1
  done

  # Acompanha logs do k6 ate a conclusao
  echo "  [k6] Testando..."
  kubectl logs -n "$NAMESPACE" k6-benchmark -c k6 -f || true

  # Para a coleta de memória
  rm -f "$stop_flag"
  wait "$MEM_PID" 2>/dev/null || true

  # Copia arquivo de resultados
  echo "  [k6] Coletando resultados..."
  MSYS_NO_PATHCONV=1 kubectl exec -n "$NAMESPACE" k6-benchmark -c helper -- cat //shared/result.json > "$output_file"

  # Remove pod do k6
  kubectl delete pod -n "$NAMESPACE" k6-benchmark --grace-period=0 --force >/dev/null 2>&1

  local mem_samples
  mem_samples=$(wc -l < "$mem_file" 2>/dev/null || echo "0")
  echo "    OK: $(basename "$output_file")  |  RAM: $mem_samples amostras"
}

# ── Definição dos cenários ────────────────────────────────────
declare -a SCENARIOS
if [[ "$SCENARIO_FILTER" == "all" ]]; then
  SCENARIOS=("baseline" "stress" "spike")
else
  SCENARIOS=("$SCENARIO_FILTER")
fi

BACKENDS=("java" "go" "quarkus")

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

    for backend in "${BACKENDS[@]}"; do
      current=$((current + 1))
      echo ""
      echo "  [$current/$total_runs] Backend: $backend"
      run_scenario "$backend" "$scenario" "$round"
    done
  done

  echo ""
done

echo ""
echo "============================================================"
echo "  Benchmark GKE concluido!"
echo "  Resultados: results/runs_gke/$TIMESTAMP"
echo "============================================================"
echo ""
echo "  Gerar relatorio estatistico com memoria:"
echo "  python3 scripts/benchmarks/analyze_results.py results/runs_gke/$TIMESTAMP"
echo "  python3 scripts/benchmarks/analyze_results.py results/runs_gke/$TIMESTAMP --format markdown"
echo ""
