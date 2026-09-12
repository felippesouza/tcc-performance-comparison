import urllib.request, json, urllib.parse
q = 'histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket{job="backend-java"}[10s])) by (le))'
url = 'http://localhost:9093/api/v1/query_range?query=' + urllib.parse.quote(q) + '&start=1788208200&end=1788208600&step=2s'
req = urllib.request.urlopen(url)
res = json.loads(req.read())
print(res['data']['result'][0]['values'][:10])
