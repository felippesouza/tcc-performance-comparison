// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.cache;

import com.tcc.gateway.adapter.controller.dto.PaymentResponse;

import java.util.Optional;

/**
 * Contrato para verificação de idempotência de pagamentos.
 * Evita reprocessar a mesma transação em caso de retry do cliente.
 * Equivalente à interface IdempotencyCache do Go.
 */
public interface IdempotencyCache {

    /**
     * Busca uma resposta cacheada pela chave de idempotência.
     * Retorna Optional.empty() se a chave não existir — ausência não é erro.
     */
    Optional<PaymentResponse> get(String key);

    /**
     * Armazena a resposta no cache com TTL de 24h.
     */
    void set(String key, PaymentResponse response);
}
