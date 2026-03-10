import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

export const errorRate = new Rate('errors');
export const idempotencyHits = new Rate('idempotency_cache_hits');

// ─────────────────────────────────────────────────────────────────────────────
// ATENÇÃO — ISOLAMENTO ENTRE TESTES (CRÍTICO PARA VALIDADE CIENTÍFICA)
//
// O Redis de idempotência persiste entre execuções do k6. Como __ITER reseta
// a zero em cada `k6 run`, um teste que roda APÓS outro vai encontrar as chaves
// do teste anterior no Redis, gerando cache hits espúrios e inflando throughput.
//
// SEMPRE execute antes de cada teste:
//   docker exec tcc-redis redis-cli FLUSHALL
//
// Ou use o helper abaixo para limpar automaticamente via setup():
// ─────────────────────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────────────────────
// SELEÇÃO DE CENÁRIO
// Uso: k6 run -e SCENARIO=baseline -e TARGET_URL=http://... stress_test.js
//
// Cenários:
//   baseline → concorrência baixa (20 VUs): ambos devem se comportar igual.
//              Serve como controle científico.
//   stress   → carga alta sustentada (200 VUs): onde VT vs Goroutines divergem.
//              Cenário principal do TCC.
//   spike    → pico abrupto (500 VUs): testa elasticidade do modelo de concorrência.
//              Evidencia como cada runtime reage a cargas inesperadas.
// ─────────────────────────────────────────────────────────────────────────────
const SCENARIO = __ENV.SCENARIO || 'stress';

const scenarios = {
  baseline: {
    description: 'Controle: 20 VUs por 2 minutos. Ambos devem ser equivalentes.',
    stages: [
      { duration: '30s', target: 10 },
      { duration: '60s', target: 20 },
      { duration: '30s', target: 0 },
    ],
    thresholds: {
      http_req_duration: ['p(95)<1000', 'p(99)<1500'],
      errors: ['rate<0.01'],
    },
  },
  stress: {
    description: 'Principal: 200 VUs sustentados. Cenário-chave para comparar VT vs Goroutines.',
    stages: [
      { duration: '10s', target: 50 },   // Warm-up: sobe para 50 VUs
      { duration: '30s', target: 200 },  // Ramp-up: atinge o pico de 200 VUs
      { duration: '60s', target: 200 },  // Sustenta: coleta dados estáveis
      { duration: '10s', target: 0 },    // Cool-down
    ],
    thresholds: {
      http_req_duration: ['p(95)<800', 'p(99)<1500'],
      errors: ['rate<0.01'],
    },
  },
  spike: {
    description: 'Spike: ramp abrupto para 500 VUs. Mede elasticidade e recuperação.',
    stages: [
      { duration: '10s', target: 10 },   // Baseline estável
      { duration: '5s',  target: 500 },  // Spike abrupto
      { duration: '30s', target: 500 },  // Sustenta o pico
      { duration: '5s',  target: 10 },   // Queda abrupta
      { duration: '10s', target: 0 },    // Cool-down
    ],
    thresholds: {
      http_req_duration: ['p(95)<2000', 'p(99)<4000'],
      errors: ['rate<0.05'],
    },
  },
};

const selected = scenarios[SCENARIO];
if (!selected) {
  throw new Error(`Cenário inválido: "${SCENARIO}". Opções: baseline | stress | spike`);
}

console.log(`\n▶ Executando cenário: ${SCENARIO.toUpperCase()}`);
console.log(`  ${selected.description}\n`);

export const options = {
  stages: selected.stages,
  thresholds: selected.thresholds,
};

export default function () {
  const url = __ENV.TARGET_URL || 'http://localhost:8081/payments';

  const payload = JSON.stringify({
    amount: parseFloat((Math.random() * 1000).toFixed(2)),
    cardNumber: '1234-5678-9012-3456',
  });

  // X-Idempotency-Key único por VU+Iteração:
  // Garante que cada request passe pelo fluxo completo (sem hit no cache),
  // medindo a performance real do backend e não do Redis.
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Idempotency-Key': `k6-vu${__VU}-iter${__ITER}`,
    },
  };

  const res = http.post(url, payload, params);

  const success = check(res, {
    'status is 201': (r) => r.status === 201,
    'has payment id': (r) => {
      try { return JSON.parse(r.body).id !== undefined; } catch { return false; }
    },
  });

  errorRate.add(!success);

  // Sleep mínimo para maximizar requisições concorrentes em-flight.
  // Com 200 VUs e ~350ms de latência do mock, isso resulta em ~400 req/s simultâneos,
  // expondo o comportamento real de Virtual Threads vs Goroutines sob pressão.
  sleep(0.1);
}
