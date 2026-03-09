import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Métrica customizada para contar quantos pagamentos falharam
export const errorRate = new Rate('errors');

// Configuração do Teste de Stress
export const options = {
  stages: [
    { duration: '10s', target: 50 },  // Ramp-up: sobe para 50 usuários simultâneos
    { duration: '30s', target: 200 }, // Spike: sobe para 200 usuários (A "Guerra" das Threads começa aqui)
    { duration: '20s', target: 200 }, // Sustenta o pico
    { duration: '10s', target: 0 },   // Ramp-down: esfria o servidor
  ],
  thresholds: {
    // Para o TCC ser válido, 95% das requisições devem ser respondidas em menos de 800ms
    http_req_duration: ['p(95)<800'],
    // Menos de 1% de erro (status 5xx)
    errors: ['rate<0.01'], 
  },
};

export default function () {
  // Altere o target URL dependendo de qual backend quer testar
  // Java: http://localhost:8081/payments
  // Go:   http://localhost:8082/payments
  const url = __ENV.TARGET_URL || 'http://localhost:8081/payments';

  const payload = JSON.stringify({
    amount: (Math.random() * 1000).toFixed(2),
    cardNumber: "1234-5678-9012-3456"
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post(url, payload, params);

  // Verificação de Sucesso
  const success = check(res, {
    'status is 201': (r) => r.status === 201,
  });

  errorRate.add(!success);

  // Sleep de 1 segundo entre requisições de um mesmo "usuário virtual" para não travar o SO rodando o teste localmente
  sleep(1);
}
