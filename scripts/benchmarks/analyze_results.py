#!/usr/bin/env python3
"""
TCC — Analisador Estatístico de Resultados k6
Calcula média e desvio padrão para 3 rodadas de cada cenário/backend.

Uso:
    python3 scripts/benchmarks/analyze_results.py results/runs/<timestamp>
    python3 scripts/benchmarks/analyze_results.py results/runs/<timestamp> --format markdown
"""

import json
import sys
import math
import os
import glob
from collections import defaultdict


def load_k6_json(filepath: str) -> dict:
    """Extrai métricas principais de um arquivo JSON de saída do k6."""
    metrics = {
        "http_reqs": [],
        "http_req_duration_p95": None,
        "http_req_duration_p99": None,
        "http_req_duration_med": None,
        "http_req_duration_avg": None,
        "http_req_failed_rate": None,
        "iterations": None,
        "rps": None,
    }

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if entry.get("type") != "Point":
                    continue

                metric = entry.get("metric", "")
                data = entry.get("data", {})

                if metric == "http_req_duration":
                    # k6 emite pontos de métricas agregadas ao final
                    pass

        # Segunda passagem: pegar métricas summary
        with open(filepath, 'r') as f:
            content = f.read()

        # k6 JSON format: procurar pelos valores de summary no final
        lines = content.strip().split('\n')
        for line in lines:
            try:
                entry = json.loads(line)
            except Exception:
                continue

            if entry.get("type") == "Metric":
                metric_name = entry.get("data", {}).get("name", "")
                if metric_name == "http_reqs":
                    contains = entry.get("data", {}).get("contains", "")

            if entry.get("type") == "Point":
                metric = entry.get("metric", "")
                val = entry.get("data", {}).get("value", 0)

                if metric == "http_reqs":
                    metrics["http_reqs"].append(val)
                elif metric == "http_req_failed":
                    metrics["http_req_failed_rate"] = val

    except Exception as e:
        print(f"  Aviso: erro ao ler {filepath}: {e}", file=sys.stderr)

    return metrics


def load_k6_summary(filepath: str) -> dict:
    """
    Extrai métricas do formato summary do k6 JSON.
    O k6 --out json gera linhas NDJSON. As linhas com type='Metric' no final
    contêm os valores agregados (avg, p95, p99, etc).
    """
    result = {
        "rps": 0.0,
        "p50_ms": 0.0,
        "p95_ms": 0.0,
        "p99_ms": 0.0,
        "avg_ms": 0.0,
        "error_rate": 0.0,
        "total_requests": 0,
        "duration_s": 0.0,
    }

    duration_ms_values = []
    http_reqs_count = 0
    error_count = 0
    test_start = None
    test_end = None

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue

                t = entry.get("type", "")
                metric = entry.get("metric", "")
                data = entry.get("data", {})

                if t == "Point":
                    ts = data.get("time", "")
                    if test_start is None:
                        test_start = ts
                    test_end = ts

                    if metric == "http_req_duration":
                        val = data.get("value", 0)
                        duration_ms_values.append(val)

                    elif metric == "http_reqs":
                        http_reqs_count += 1

                    elif metric == "http_req_failed":
                        if data.get("value", 0) == 1:
                            error_count += 1

    except Exception as e:
        print(f"  Erro ao processar {filepath}: {e}", file=sys.stderr)
        return result

    if not duration_ms_values:
        return result

    sorted_vals = sorted(duration_ms_values)
    n = len(sorted_vals)

    def percentile(data, p):
        if not data:
            return 0
        k = (len(data) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return data[int(k)]
        return data[f] * (c - k) + data[c] * (k - f)

    result["total_requests"] = http_reqs_count
    result["avg_ms"] = sum(duration_ms_values) / n if n > 0 else 0
    result["p50_ms"] = percentile(sorted_vals, 50)
    result["p95_ms"] = percentile(sorted_vals, 95)
    result["p99_ms"] = percentile(sorted_vals, 99)
    result["error_rate"] = error_count / http_reqs_count * 100 if http_reqs_count > 0 else 0

    return result


def mean(values):
    return sum(values) / len(values) if values else 0.0


def stddev(values):
    if len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def cv(values):
    """Coeficiente de variação (desvio padrão / média * 100)"""
    m = mean(values)
    if m == 0:
        return 0.0
    return stddev(values) / m * 100


def analyze_directory(results_dir: str, output_format: str = "text"):
    """Analisa todos os arquivos JSON em um diretório de resultados."""

    if not os.path.isdir(results_dir):
        print(f"Diretório não encontrado: {results_dir}")
        sys.exit(1)

    # Encontrar todos os arquivos de resultado
    pattern = os.path.join(results_dir, "*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"Nenhum arquivo JSON encontrado em: {results_dir}")
        sys.exit(1)

    print(f"\nAnalisando {len(files)} arquivos em: {results_dir}\n")

    # Organizar por backend e cenário
    data = defaultdict(lambda: defaultdict(list))

    for filepath in files:
        filename = os.path.basename(filepath)
        # Formato esperado: java_stress_round1.json
        parts = filename.replace(".json", "").split("_")
        if len(parts) < 3:
            continue

        backend = parts[0]     # java | go
        scenario = "_".join(parts[1:-1])  # baseline | stress | spike
        round_str = parts[-1]  # round1 | round2 | round3

        metrics = load_k6_summary(filepath)
        if metrics["total_requests"] > 0:
            data[scenario][backend].append(metrics)
        else:
            print(f"  Arquivo vazio ou sem dados: {filename}")

    if not data:
        print("Nenhum dado válido encontrado.")
        sys.exit(1)

    # ── Gerar Relatório ───────────────────────────────────────
    scenarios_order = ["baseline", "stress", "spike"]
    backends_order = ["java", "go"]

    if output_format == "markdown":
        print_markdown_report(data, scenarios_order, backends_order, results_dir)
    else:
        print_text_report(data, scenarios_order, backends_order)


def print_text_report(data, scenarios_order, backends_order):
    for scenario in scenarios_order:
        if scenario not in data:
            continue

        vu_map = {"baseline": "20 VUs", "stress": "200 VUs", "spike": "500 VUs"}
        print(f"{'=' * 62}")
        print(f"  CENARIO: {scenario.upper()} -- {vu_map.get(scenario, '')}")
        print(f"{'=' * 62}")

        for backend in backends_order:
            if backend not in data[scenario]:
                continue

            rounds = data[scenario][backend]
            n = len(rounds)

            p95_vals = [r["p95_ms"] for r in rounds]
            p99_vals = [r["p99_ms"] for r in rounds]
            avg_vals = [r["avg_ms"] for r in rounds]
            p50_vals = [r["p50_ms"] for r in rounds]
            req_vals = [r["total_requests"] for r in rounds]
            err_vals = [r["error_rate"] for r in rounds]

            label = "Java 25 (VT)" if backend == "java" else "Go 1.25 (Goroutines)"
            print(f"\n  {label} -- {n} rodada(s)")
            print(f"  {'-' * 50}")
            print(f"  {'Metrica':<25} {'Media':>10} {'+/-StdDev':>10} {'CV%':>7}")
            print(f"  {'-' * 50}")

            def row(label, vals):
                if not vals or all(v == 0 for v in vals):
                    return
                print(f"  {label:<25} {mean(vals):>9.1f}  {stddev(vals):>9.1f}  {cv(vals):>6.1f}%")

            row("Latencia Media (ms)", avg_vals)
            row("Mediana p50 (ms)", p50_vals)
            row("p95 (ms)", p95_vals)
            row("p99 (ms)", p99_vals)
            row("Total Requests", req_vals)
            row("Taxa de Erro (%)", err_vals)

        print("")


def print_markdown_report(data, scenarios_order, backends_order, results_dir):
    timestamp = os.path.basename(results_dir)
    print(f"# Relatorio Estatistico -- Benchmark TCC")
    print(f"**Rodadas analisadas:** {results_dir}")
    print(f"**Gerado em:** {timestamp}\n")
    print("> Valores calculados como media +/- desvio padrao (N rodadas por cenario)")
    print()

    for scenario in scenarios_order:
        if scenario not in data:
            continue

        vu_map = {"baseline": "20 VUs, 2 min", "stress": "200 VUs, ~2 min", "spike": "500 VUs, 1 min"}
        print(f"## Cenario: {scenario.upper()} ({vu_map.get(scenario, '')})")
        print()
        print("| Metrica | Java 25 (VT) | Go 1.25 | Delta |")
        print("| :--- | ---: | ---: | ---: |")

        metrics_map = {
            "avg_ms": "Latencia Media (ms)",
            "p50_ms": "Mediana p50 (ms)",
            "p95_ms": "p95 (ms)",
            "p99_ms": "p99 (ms)",
            "total_requests": "Total Requests",
            "error_rate": "Taxa de Erro (%)",
        }

        java_rounds = data[scenario].get("java", [])
        go_rounds = data[scenario].get("go", [])

        for metric_key, metric_label in metrics_map.items():
            java_vals = [r[metric_key] for r in java_rounds]
            go_vals = [r[metric_key] for r in go_rounds]

            java_str = f"{mean(java_vals):.1f} +/-{stddev(java_vals):.1f}" if java_vals else "N/A"
            go_str = f"{mean(go_vals):.1f} +/-{stddev(go_vals):.1f}" if go_vals else "N/A"

            if java_vals and go_vals and mean(java_vals) > 0:
                delta_pct = (mean(go_vals) - mean(java_vals)) / mean(java_vals) * 100
                if abs(delta_pct) < 2:
                    delta_str = "Empate"
                elif delta_pct < 0:
                    delta_str = f"Go -{abs(delta_pct):.1f}%"
                else:
                    delta_str = f"Java -{abs(delta_pct):.1f}%"
            else:
                delta_str = "---"

            print(f"| {metric_label} | {java_str} | {go_str} | {delta_str} |")

        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUso: python3 analyze_results.py <results_dir> [--format markdown|text]")
        sys.exit(1)

    results_dir = sys.argv[1]
    fmt = "text"
    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            fmt = sys.argv[idx + 1]

    analyze_directory(results_dir, fmt)
