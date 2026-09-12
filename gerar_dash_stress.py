import json
import os
from datetime import datetime
import urllib.request
from urllib.parse import quote

HTML_FILE = "graficos_stress.html"

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>TCC Dashboards (Stress - 200 VUs)</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body { background-color: #111217; color: white; font-family: sans-serif; margin: 20px; }
        .chart { width: 100%; height: 500px; margin-bottom: 50px; }
        h1, h2 { text-align: center; color: #E0E0E0; }
    </style>
</head>
<body>
    <h1>Resultados do Benchmark GKE - Cenário Stress (200 VUs - 120s)</h1>
    <div id="chart-throughput" class="chart"></div>
    <div id="chart-latency" class="chart"></div>
    <div id="chart-ram" class="chart"></div>
    <div id="chart-hikaricp" class="chart"></div>

    <script>
        var darkLayout = {
            plot_bgcolor: "#111217", paper_bgcolor: "#111217", font: {color: "#A0A0A0"},
            xaxis: {title: "Segundos (Tempo do Teste)", gridcolor: "#333"},
            yaxis: {gridcolor: "#333"},
            legend: {orientation: "h", y: -0.2}
        };

        Plotly.newPlot('chart-throughput', REPLACE_RPS_DATA, Object.assign({}, darkLayout, {title: "Throughput (RPS) - Lado a Lado", yaxis: {title: "Req/s"}}));
        Plotly.newPlot('chart-latency', REPLACE_LAT_DATA, Object.assign({}, darkLayout, {title: "Latência p95 (ms) - Lado a Lado", yaxis: {title: "ms"}}));
        Plotly.newPlot('chart-ram', REPLACE_RAM_DATA, Object.assign({}, darkLayout, {title: "Footprint de RAM (RSS)", yaxis: {title: "MB"}}));
        Plotly.newPlot('chart-hikaricp', REPLACE_HIKARI_DATA, Object.assign({}, darkLayout, {title: "Pool de Conexões (HikariCP) - Java Stress", yaxis: {title: "Conexões/Threads"}}));
    </script>
</body>
</html>
"""

def parse_mem_mb(mem_str):
    import re
    used = mem_str.split('/')[0].strip()
    match = re.match(r'([\d.]+)\s*(GiB|MiB|KiB|GB|MB|KB|B)', used, re.IGNORECASE)
    if not match: return 0.0
    value, unit = float(match.group(1)), match.group(2).upper()
    conversions = {'GIB': 1024.0, 'GB': 1000.0, 'MIB': 1.0, 'MB': 1.0, 'KIB': 1/1024.0, 'KB': 1/1000.0, 'B': 1/(1024*1024)}
    return value * conversions.get(unit, 1.0)

def main():
    rps_data, lat_data, ram_data = [], [], []
    colors = {"java": "#F5A623", "go": "#00ADD8", "quarkus": "#9933CC"}
    names = {"java": "Java 25", "go": "Go 1.25", "quarkus": "Quarkus Native"}

    RESULTS_DIR = "results/runs_gke/20260831_163523"

    for backend in ["java", "go", "quarkus"]:
        json_file = f"{RESULTS_DIR}/{backend}_stress_round3.json"
        mem_file = f"{RESULTS_DIR}/{backend}_stress_round3.mem"
        
        # Memory
        if os.path.exists(mem_file):
            with open(mem_file, 'r', errors='replace') as f:
                lines = f.readlines()
                y_ram = [parse_mem_mb(l) for l in lines]
                x_ram = [i*2 for i in range(len(y_ram))]
                ram_data.append({"x": x_ram, "y": y_ram, "mode": "lines", "name": names[backend], "line": {"color": colors[backend], "width": 3}})

        # K6 JSON parsing (True RPS and Latency)
        if os.path.exists(json_file):
            t_buckets = {}
            lat_buckets = {}
            t0 = None
            with open(json_file, 'r') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        entry = json.loads(line)
                        if entry.get("type") != "Point": continue
                        metric = entry.get("metric")
                        if metric not in ["http_reqs", "http_req_duration"]: continue
                        
                        ts_str = entry["data"]["time"]
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
                        if t0 is None: t0 = ts
                        
                        sec = int(ts - t0)
                        if metric == "http_reqs":
                            t_buckets[sec] = t_buckets.get(sec, 0) + 1
                        elif metric == "http_req_duration":
                            lat_buckets.setdefault(sec, []).append(entry["data"]["value"])
                    except: pass
            
            x_rps = sorted(t_buckets.keys())
            y_rps = [t_buckets[k] for k in x_rps]
            rps_data.append({"x": x_rps, "y": y_rps, "mode": "lines", "name": names[backend], "line": {"color": colors[backend], "width": 3}})

            x_lat = sorted(lat_buckets.keys())
            y_lat = []
            for k in x_lat:
                vals = sorted(lat_buckets[k])
                p95 = vals[int(len(vals)*0.95)] if vals else 0
                y_lat.append(p95)
            lat_data.append({"x": x_lat, "y": y_lat, "mode": "lines", "name": names[backend], "line": {"color": colors[backend], "width": 3}})

    # HikariCP and Agroal for Spike (1788208250 to 1788208350)
    hikari_data = []
    java_start = 1788208250
    java_end = 1788208350
    
    # Java Pending
    q_java_pend = 'hikaricp_connections_pending{job="backend-java"}'
    url = f"http://localhost:9093/api/v1/query_range?query={quote(q_java_pend)}&start={java_start}&end={java_end}&step=2s"
    try:
        res = json.loads(urllib.request.urlopen(url).read())
        if res.get('status') == 'success' and res['data']['result']:
            vals = res['data']['result'][0]['values']
            t0 = float(vals[0][0])
            hikari_data.append({"x": [float(v[0]) - t0 for v in vals], "y": [float(v[1]) for v in vals], "mode": "lines", "name": "Java (HikariCP) - Esperando", "line": {"color": "#FF9800", "width": 3}})
    except: pass

    # Java Active
    q_java_act = 'hikaricp_connections_active{job="backend-java"}'
    url = f"http://localhost:9093/api/v1/query_range?query={quote(q_java_act)}&start={java_start}&end={java_end}&step=2s"
    try:
        res = json.loads(urllib.request.urlopen(url).read())
        if res.get('status') == 'success' and res['data']['result']:
            vals = res['data']['result'][0]['values']
            t0 = float(vals[0][0])
            hikari_data.append({"x": [float(v[0]) - t0 for v in vals], "y": [float(v[1]) for v in vals], "mode": "lines", "name": "Java (HikariCP) - Ativas", "line": {"color": "#F5A623", "width": 3, "dash": "dash"}})
    except: pass

    # Quarkus Active
    q_qk_act = 'agroal_connections_active_count{job="backend-quarkus"}'
    url = f"http://localhost:9093/api/v1/query_range?query={quote(q_qk_act)}&start={java_start}&end={java_end}&step=2s"
    try:
        res = json.loads(urllib.request.urlopen(url).read())
        if res.get('status') == 'success' and res['data']['result']:
            vals = res['data']['result'][0]['values']
            t0 = float(vals[0][0])
            hikari_data.append({"x": [float(v[0]) - t0 for v in vals], "y": [float(v[1]) for v in vals], "mode": "lines", "name": "Quarkus (Agroal) - Ativas", "line": {"color": "#9933CC", "width": 3}})
    except: pass

    html_out = HTML_TEMPLATE.replace("REPLACE_RPS_DATA", json.dumps(rps_data))
    html_out = html_out.replace("REPLACE_LAT_DATA", json.dumps(lat_data))
    html_out = html_out.replace("REPLACE_RAM_DATA", json.dumps(ram_data))
    html_out = html_out.replace("REPLACE_HIKARI_DATA", json.dumps(hikari_data))
    html_out = html_out.replace("Pool de Conexões (HikariCP) - Java Stress", "Pool de Conexões (HikariCP vs Agroal) - Spike Test")

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_out)

if __name__ == "__main__":
    main()
