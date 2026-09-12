import json
import os
import urllib.request
from urllib.parse import quote

HTML_FILE = "graficos_tcc.html"
PROM_URL = "http://localhost:9093/api/v1/query_range?query="

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>TCC Dashboards (Spike 500 VUs)</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body { background-color: #111217; color: white; font-family: sans-serif; margin: 20px; }
        .chart { width: 100%; height: 500px; margin-bottom: 50px; }
        h1, h2 { text-align: center; color: #E0E0E0; }
    </style>
</head>
<body>
    <h1>Resultados do Benchmark GKE - Cenário Spike (500 VUs)</h1>
    <div id="chart-throughput" class="chart"></div>
    <div id="chart-latency" class="chart"></div>
    <div id="chart-hikaricp" class="chart"></div>
    <div id="chart-ram" class="chart"></div>

    <script>
        var darkLayout = {
            plot_bgcolor: "#111217", paper_bgcolor: "#111217", font: {color: "#A0A0A0"},
            xaxis: {title: "Segundos (Tempo do Teste)", gridcolor: "#333", range: [0, 65]},
            yaxis: {gridcolor: "#333"},
            legend: {orientation: "h", y: -0.2}
        };

        var dataRPS = REPLACE_RPS_DATA;
        Plotly.newPlot('chart-throughput', dataRPS, Object.assign({}, darkLayout, {title: "Throughput (RPS)", yaxis: {title: "Req/s"}}));

        var dataLat = REPLACE_LAT_DATA;
        Plotly.newPlot('chart-latency', dataLat, Object.assign({}, darkLayout, {title: "Latência p95 (Segundos)", yaxis: {title: "Segundos"}}));

        var dataHikari = REPLACE_HIKARI_DATA;
        Plotly.newPlot('chart-hikaricp', dataHikari, Object.assign({}, darkLayout, {title: "Pool de Conexões - Threads em Espera (HikariCP)", yaxis: {title: "Conexões/Threads"}}));

        var dataRAM = REPLACE_RAM_DATA;
        Plotly.newPlot('chart-ram', dataRAM, Object.assign({}, darkLayout, {title: "Footprint de RAM (RSS) - Coletado via Kubernetes", yaxis: {title: "MB"}}));
    </script>
</body>
</html>
"""

def query_prometheus(q):
    # Janela exata do Spike Test (17:30 as 17:36 local time)
    start_time = 1788208200
    end_time = 1788208600
    try:
        url = f"{PROM_URL}{quote(q)}&start={start_time}&end={end_time}&step=2s"
        req = urllib.request.urlopen(url)
        res = json.loads(req.read())
        if res.get('status') == 'success' and res['data']['result']:
            return res['data']['result'][0]['values']
    except Exception as e:
        pass
    return []

def align_series(values, color, name):
    if not values: return None
    # Pega apenas os pontos onde ha carga real
    filtered = [v for v in values if float(v[1]) > 0.1]
    if not filtered: return None
    
    t0 = float(filtered[0][0])
    x = [float(v[0]) - t0 for v in filtered]
    y = [float(v[1]) for v in filtered]
    
    return {"x": x, "y": y, "mode": "lines", "name": name, "line": {"color": color, "width": 3}}

def parse_mem_mb(mem_str):
    import re
    used = mem_str.split('/')[0].strip()
    match = re.match(r'([\d.]+)\s*(GiB|MiB|KiB|GB|MB|KB|B)', used, re.IGNORECASE)
    if not match: return 0.0
    value, unit = float(match.group(1)), match.group(2).upper()
    conversions = {'GIB': 1024.0, 'GB': 1000.0, 'MIB': 1.0, 'MB': 1.0, 'KIB': 1/1024.0, 'KB': 1/1000.0, 'B': 1/(1024*1024)}
    return value * conversions.get(unit, 1.0)

def main():
    rps_data, lat_data, hikari_data, ram_data = [], [], [], []
    colors = {"java": "#F5A623", "go": "#00ADD8", "quarkus": "#9933CC"}
    names = {"java": "Java 25", "go": "Go 1.25", "quarkus": "Quarkus Native"}

    for backend in ["java", "go", "quarkus"]:
        # Throughput
        q_rps = f'sum(rate(http_server_requests_seconds_count{{job="backend-{backend}"}}[10s]))'
        s_rps = align_series(query_prometheus(q_rps), colors[backend], names[backend])
        if s_rps: rps_data.append(s_rps)

        # Latency p95
        q_lat = f'histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket{{job="backend-{backend}"}}[10s])) by (le))'
        s_lat = align_series(query_prometheus(q_lat), colors[backend], names[backend])
        if s_lat:
            for i in range(len(s_lat['y'])):
                if s_lat['y'][i] != s_lat['y'][i] or str(s_lat['y'][i]) == 'nan': s_lat['y'][i] = 0
            lat_data.append(s_lat)

        # Memory (from .mem files)
        mem_file = f"results/runs_gke/20260831_173044/{backend}_spike_round1.mem"
        if os.path.exists(mem_file):
            with open(mem_file, 'r', errors='replace') as f:
                lines = f.readlines()
                y_ram = [parse_mem_mb(l) for l in lines]
                x_ram = [i*2 for i in range(len(y_ram))] # a cada 2 seg
                ram_data.append({"x": x_ram, "y": y_ram, "mode": "lines", "name": names[backend], "line": {"color": colors[backend], "width": 3}})

    # HikariCP
    s_hikari = align_series(query_prometheus('hikaricp_connections_pending{job="backend-java"}'), colors["java"], "Java - Threads em Espera (HikariCP)")
    if s_hikari: hikari_data.append(s_hikari)

    html_out = HTML_TEMPLATE.replace("REPLACE_RPS_DATA", json.dumps(rps_data))
    html_out = html_out.replace("REPLACE_LAT_DATA", json.dumps(lat_data))
    html_out = html_out.replace("REPLACE_HIKARI_DATA", json.dumps(hikari_data))
    html_out = html_out.replace("REPLACE_RAM_DATA", json.dumps(ram_data))

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_out)

if __name__ == "__main__":
    main()
