#!/usr/bin/env python3
"""
TCC -- Analisador Estatistico de Resultados k6 + Memoria Docker
Calcula media e desvio padrao para N rodadas de cada cenario/backend.
Inclui pico e media de RAM capturada via docker stats durante cada run.

Uso:
    python3 scripts/benchmarks/analyze_results.py results/runs/<timestamp>
    python3 scripts/benchmarks/analyze_results.py results/runs/<timestamp> --format markdown
"""

import json
import sys
import math
import os
import re
import glob
from collections import defaultdict
from datetime import datetime, timezone


# ── Helpers estatísticos ──────────────────────────────────────────────────────

def mean(values):
    return sum(values) / len(values) if values else 0.0

def stddev(values):
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))

def cv(values):
    m = mean(values)
    return (stddev(values) / m * 100) if m != 0 else 0.0

def percentile(data, p):
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    f, c = math.floor(k), math.ceil(k)
    return s[f] if f == c else s[f] * (c - k) + s[c] * (k - f)


# ── Parser de memória Docker ──────────────────────────────────────────────────

def parse_mem_mb(mem_str: str) -> float:
    """
    Converte string de memória do 'docker stats' para MB.
    Exemplos de entrada: '256MiB / 8GiB', '1.5GiB / 8GiB', '512KiB / 8GiB'
    """
    used = mem_str.split('/')[0].strip()
    # Remove sufixos e converte
    match = re.match(r'([\d.]+)\s*(GiB|MiB|KiB|GB|MB|KB|B)', used, re.IGNORECASE)
    if not match:
        return 0.0
    value, unit = float(match.group(1)), match.group(2).upper()
    conversions = {'GIB': 1024.0, 'GB': 1000.0, 'MIB': 1.0, 'MB': 1.0,
                   'KIB': 1/1024.0, 'KB': 1/1000.0, 'B': 1/(1024*1024)}
    return value * conversions.get(unit, 1.0)


def load_mem_stats(mem_file: str) -> dict:
    """
    Le o arquivo .mem gerado pelo docker stats durante o benchmark.
    Retorna pico, media e numero de amostras em MB.
    O docker stats streaming emite sequencias ANSI (ex: [H, [K) que sao stripadas.
    """
    result = {"peak_mb": 0.0, "avg_mb": 0.0, "samples": 0}
    if not os.path.exists(mem_file):
        return result

    # Remove sequencias de escape ANSI (ex: \x1b[H, \x1b[K, [H, [K)
    ansi_escape = re.compile(r'(\x1b|\033)?\[[\d;]*[A-Za-z]')

    values = []
    try:
        with open(mem_file, 'r', errors='replace') as f:
            for line in f:
                line = ansi_escape.sub('', line).strip()
                if not line:
                    continue
                mb = parse_mem_mb(line)
                if mb > 0:
                    values.append(mb)
    except Exception as e:
        print(f"  Aviso: erro ao ler {mem_file}: {e}", file=sys.stderr)

    if values:
        result["peak_mb"] = max(values)
        result["avg_mb"] = mean(values)
        result["samples"] = len(values)

    return result


# ── Parser k6 NDJSON ─────────────────────────────────────────────────────────

def load_k6_summary(filepath: str) -> dict:
    """
    Extrai metricas de latencia, throughput e erros do NDJSON do k6.
    Calcula percentis a partir dos pontos brutos (nao usa agregacoes do k6).
    """
    result = {
        "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0,
        "avg_ms": 0.0, "error_rate": 0.0, "total_requests": 0, "rps": 0.0,
    }

    duration_ms_values = []
    http_reqs_count = 0
    error_count = 0
    min_ts = None
    max_ts = None

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

                if entry.get("type") != "Point":
                    continue

                metric = entry.get("metric", "")
                data = entry.get("data", {})
                val = data.get("value", 0)

                # Rastreia timestamps reais para calcular RPS sem hardcode de duracao
                ts_str = data.get("time", "")
                if ts_str and metric == "http_req_duration":
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if min_ts is None or ts < min_ts:
                            min_ts = ts
                        if max_ts is None or ts > max_ts:
                            max_ts = ts
                    except Exception:
                        pass

                if metric == "http_req_duration":
                    duration_ms_values.append(val)
                elif metric == "http_reqs":
                    http_reqs_count += 1
                elif metric == "http_req_failed" and val == 1:
                    error_count += 1

    except Exception as e:
        print(f"  Erro ao processar {filepath}: {e}", file=sys.stderr)
        return result

    if not duration_ms_values:
        return result

    result["total_requests"] = http_reqs_count
    result["avg_ms"] = mean(duration_ms_values)
    result["p50_ms"] = percentile(duration_ms_values, 50)
    result["p95_ms"] = percentile(duration_ms_values, 95)
    result["p99_ms"] = percentile(duration_ms_values, 99)
    result["error_rate"] = error_count / http_reqs_count * 100 if http_reqs_count > 0 else 0.0

    if min_ts and max_ts:
        duration_s = (max_ts - min_ts).total_seconds()
        result["rps"] = round(http_reqs_count / duration_s, 1) if duration_s > 0 else 0.0

    return result


# ── Carregamento do diretório ─────────────────────────────────────────────────

def load_results(results_dir: str):
    """
    Varre o diretorio e carrega pares (k6 JSON + .mem) por backend/cenario/round.
    Retorna: data[scenario][backend] = lista de dicts com metricas + memoria.
    """
    pattern = os.path.join(results_dir, "*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"Nenhum arquivo JSON encontrado em: {results_dir}")
        sys.exit(1)

    print(f"\nAnalisando {len(files)} arquivos em: {results_dir}\n", file=sys.stderr)

    data = defaultdict(lambda: defaultdict(list))
    mem_missing = 0

    for filepath in files:
        filename = os.path.basename(filepath)
        parts = filename.replace(".json", "").split("_")
        if len(parts) < 3:
            continue

        backend = parts[0]                    # java | go
        scenario = "_".join(parts[1:-1])      # baseline | stress | spike
        # round_str = parts[-1]               # round1 | round2 | round3

        metrics = load_k6_summary(filepath)
        if metrics["total_requests"] == 0:
            print(f"  Arquivo vazio ou sem dados: {filename}")
            continue

        # Carrega memoria do arquivo .mem companion
        mem_file = filepath.replace(".json", ".mem")
        mem = load_mem_stats(mem_file)
        if mem["samples"] == 0:
            mem_missing += 1

        metrics.update({
            "mem_peak_mb": mem["peak_mb"],
            "mem_avg_mb":  mem["avg_mb"],
            "mem_samples": mem["samples"],
        })

        data[scenario][backend].append(metrics)

    if mem_missing > 0:
        print(f"  Info: {mem_missing} arquivo(s) .mem ausentes "
              f"(benchmark rodado sem coleta de memoria).\n")

    return data


# ── Formatação ────────────────────────────────────────────────────────────────

def delta_str(a_vals, b_vals, higher_is_better=False, a_label="Java", b_label="Go"):
    """Calcula delta percentual entre medias de dois backends (a=baseline, b=comparado)."""
    if not a_vals or not b_vals:
        return "---"
    a, b = mean(a_vals), mean(b_vals)
    if a == 0 and b == 0:
        return "Empate"
    if a == 0:
        return "---"
    pct = (b - a) / a * 100
    if abs(pct) < 2.0:
        return "Empate"
    if higher_is_better:
        return f"{b_label} +{pct:.1f}%" if pct > 0 else f"{a_label} +{abs(pct):.1f}%"
    else:
        return f"{b_label} -{abs(pct):.1f}%" if pct < 0 else f"{a_label} -{abs(pct):.1f}%"


def fmt_val(vals, unit=""):
    if not vals:
        return "N/A"
    return f"{mean(vals):.1f} +/-{stddev(vals):.1f}{unit}"


# ── Relatórios ────────────────────────────────────────────────────────────────

def print_text_report(data):
    vu_map = {"baseline": "20 VUs", "stress": "200 VUs", "spike": "500 VUs"}

    for scenario in ["baseline", "stress", "spike"]:
        if scenario not in data:
            continue

        print(f"{'=' * 65}")
        print(f"  CENARIO: {scenario.upper()} -- {vu_map.get(scenario, '')}")
        print(f"{'=' * 65}")

        backend_labels = {
            "java":    "Java 25 (VT)",
            "go":      "Go 1.25 (Goroutines)",
            "quarkus": "Quarkus Native",
        }
        for backend in ["java", "go", "quarkus"]:
            if backend not in data[scenario]:
                continue

            rounds = data[scenario][backend]
            label = backend_labels.get(backend, backend)
            print(f"\n  {label} -- {len(rounds)} rodada(s)")
            print(f"  {'-' * 55}")
            print(f"  {'Metrica':<28} {'Media':>10} {'  +/-Sigma':>10} {'CV%':>7}")
            print(f"  {'-' * 55}")

            def row(lbl, vals, fmt=".1f"):
                if not vals or all(v == 0 for v in vals):
                    return
                print(f"  {lbl:<28} {mean(vals):>10.1f}  {stddev(vals):>9.1f}  {cv(vals):>6.1f}%")

            row("Latencia Media (ms)", [r["avg_ms"] for r in rounds])
            row("Mediana p50 (ms)",    [r["p50_ms"] for r in rounds])
            row("p95 (ms)",            [r["p95_ms"] for r in rounds])
            row("p99 (ms)",            [r["p99_ms"] for r in rounds])
            row("Total Requests",      [r["total_requests"] for r in rounds])
            row("RPS (req/s)",         [r["rps"] for r in rounds])
            row("Taxa de Erro (%)",    [r["error_rate"] for r in rounds])

            # Memoria
            mem_peaks = [r["mem_peak_mb"] for r in rounds if r["mem_peak_mb"] > 0]
            mem_avgs  = [r["mem_avg_mb"]  for r in rounds if r["mem_avg_mb"] > 0]
            if mem_peaks:
                print(f"  {'RAM Pico (MB)':<28} {mean(mem_peaks):>10.1f}  "
                      f"{stddev(mem_peaks):>9.1f}  {cv(mem_peaks):>6.1f}%")
                print(f"  {'RAM Media (MB)':<28} {mean(mem_avgs):>10.1f}  "
                      f"{stddev(mem_avgs):>9.1f}  {cv(mem_avgs):>6.1f}%")

        print("")


def print_markdown_report(data, results_dir):
    timestamp = os.path.basename(results_dir)
    vu_map = {
        "baseline": "20 VUs, 2 min",
        "stress":   "200 VUs, ~2 min",
        "spike":    "500 VUs, 1 min",
    }

    print(f"# Relatorio Estatistico -- Benchmark TCC")
    print(f"**Diretorio:** `{results_dir}`")
    print(f"**Gerado em:** {timestamp}\n")
    print("> Valores: media +/- desvio padrao (N rodadas por cenario/backend)")
    print("> RAM capturada via `docker stats` em tempo real durante cada k6 run\n")

    for scenario in ["baseline", "stress", "spike"]:
        if scenario not in data:
            continue

        java_rounds    = data[scenario].get("java",    [])
        go_rounds      = data[scenario].get("go",      [])
        quarkus_rounds = data[scenario].get("quarkus", [])

        has_quarkus = len(quarkus_rounds) > 0

        print(f"## Cenario: {scenario.upper()} ({vu_map.get(scenario, '')})\n")
        if has_quarkus:
            print("| Metrica | Java 25 (VT) | Go 1.25 | Quarkus Native | Java vs Go | Java vs Quarkus | Go vs Quarkus |")
            print("| :--- | ---: | ---: | ---: | :--- | :--- | :--- |")
        else:
            print("| Metrica | Java 25 (VT) | Go 1.25 | Delta |")
            print("| :--- | ---: | ---: | :--- |")

        rows = [
            ("avg_ms",         "Latencia Media (ms)",  False),
            ("p50_ms",         "Mediana p50 (ms)",     False),
            ("p95_ms",         "p95 (ms)",             False),
            ("p99_ms",         "p99 (ms)",             False),
            ("total_requests", "Total Requests",        True),
            ("rps",            "RPS (req/s)",           True),
            ("error_rate",     "Taxa de Erro (%)",     False),
        ]

        for key, label, higher_better in rows:
            jv = [r[key] for r in java_rounds]
            gv = [r[key] for r in go_rounds]
            qv = [r[key] for r in quarkus_rounds]

            if has_quarkus:
                if key == "error_rate" and mean(jv) == 0 and mean(gv) == 0 and mean(qv) == 0:
                    print(f"| {label} | 0.00% | 0.00% | 0.00% | Empate | Empate | Empate |")
                    continue
                djg = delta_str(jv, gv, higher_is_better=higher_better, a_label="Java", b_label="Go")
                djq = delta_str(jv, qv, higher_is_better=higher_better, a_label="Java", b_label="Quarkus")
                dgq = delta_str(gv, qv, higher_is_better=higher_better, a_label="Go",   b_label="Quarkus")
                print(f"| {label} | {fmt_val(jv)} | {fmt_val(gv)} | {fmt_val(qv)} | {djg} | {djq} | {dgq} |")
            else:
                if key == "error_rate" and mean(jv) == 0 and mean(gv) == 0:
                    print(f"| {label} | 0.00% | 0.00% | Empate |")
                    continue
                d = delta_str(jv, gv, higher_is_better=higher_better, a_label="Java", b_label="Go")
                print(f"| {label} | {fmt_val(jv)} | {fmt_val(gv)} | {d} |")

        # Memoria
        j_peaks = [r["mem_peak_mb"] for r in java_rounds    if r["mem_peak_mb"] > 0]
        g_peaks = [r["mem_peak_mb"] for r in go_rounds      if r["mem_peak_mb"] > 0]
        q_peaks = [r["mem_peak_mb"] for r in quarkus_rounds if r["mem_peak_mb"] > 0]
        j_avgs  = [r["mem_avg_mb"]  for r in java_rounds    if r["mem_avg_mb"]  > 0]
        g_avgs  = [r["mem_avg_mb"]  for r in go_rounds      if r["mem_avg_mb"]  > 0]
        q_avgs  = [r["mem_avg_mb"]  for r in quarkus_rounds if r["mem_avg_mb"]  > 0]

        if j_peaks or g_peaks or q_peaks:
            jp = fmt_val(j_peaks, " MB") if j_peaks else "N/A"
            gp = fmt_val(g_peaks, " MB") if g_peaks else "N/A"
            qp = fmt_val(q_peaks, " MB") if q_peaks else "N/A"
            ja = fmt_val(j_avgs,  " MB") if j_avgs  else "N/A"
            ga = fmt_val(g_avgs,  " MB") if g_avgs  else "N/A"
            qa = fmt_val(q_avgs,  " MB") if q_avgs  else "N/A"
            if has_quarkus:
                djgp = delta_str(j_peaks, g_peaks, higher_is_better=False, a_label="Java",   b_label="Go")
                djqp = delta_str(j_peaks, q_peaks, higher_is_better=False, a_label="Java",   b_label="Quarkus")
                dgqp = delta_str(g_peaks, q_peaks, higher_is_better=False, a_label="Go",     b_label="Quarkus")
                djga = delta_str(j_avgs,  g_avgs,  higher_is_better=False, a_label="Java",   b_label="Go")
                djqa = delta_str(j_avgs,  q_avgs,  higher_is_better=False, a_label="Java",   b_label="Quarkus")
                dgqa = delta_str(g_avgs,  q_avgs,  higher_is_better=False, a_label="Go",     b_label="Quarkus")
                print(f"| **RAM Pico (MB)**  | {jp} | {gp} | {qp} | {djgp} | {djqp} | {dgqp} |")
                print(f"| **RAM Media (MB)** | {ja} | {ga} | {qa} | {djga} | {djqa} | {dgqa} |")
            else:
                dp = delta_str(j_peaks, g_peaks, higher_is_better=False, a_label="Java", b_label="Go")
                da = delta_str(j_avgs,  g_avgs,  higher_is_better=False, a_label="Java", b_label="Go")
                print(f"| **RAM Pico (MB)**  | {jp} | {gp} | {dp} |")
                print(f"| **RAM Media (MB)** | {ja} | {ga} | {da} |")
        else:
            if has_quarkus:
                print(f"| **RAM Pico (MB)**  | N/A | N/A | N/A | sem dados .mem | sem dados .mem | sem dados .mem |")
            else:
                print(f"| **RAM Pico (MB)**  | N/A | N/A | sem dados .mem |")

        print()


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main():
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

    if not os.path.isdir(results_dir):
        print(f"Diretorio nao encontrado: {results_dir}")
        sys.exit(1)

    data = load_results(results_dir)

    if not data:
        print("Nenhum dado valido encontrado.")
        sys.exit(1)

    if fmt == "markdown":
        print_markdown_report(data, results_dir)
    else:
        print_text_report(data)


if __name__ == "__main__":
    main()
