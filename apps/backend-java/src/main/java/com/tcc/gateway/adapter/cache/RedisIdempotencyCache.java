// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.cache;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tcc.gateway.adapter.controller.dto.PaymentResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.Optional;

/**
 * Implementação Redis do cache de idempotência.
 * Usa StringRedisTemplate com serialização JSON via Jackson.
 * Equivalente ao RedisIdempotencyCache do Go (go-redis + encoding/json).
 */
@Component
public class RedisIdempotencyCache implements IdempotencyCache {

    private static final Logger log = LoggerFactory.getLogger(RedisIdempotencyCache.class);
    private static final Duration TTL = Duration.ofHours(24);

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;

    public RedisIdempotencyCache(StringRedisTemplate redisTemplate, ObjectMapper objectMapper) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
    }

    @Override
    public Optional<PaymentResponse> get(String key) {
        try {
            String value = redisTemplate.opsForValue().get(key);
            if (value == null) return Optional.empty();
            return Optional.of(objectMapper.readValue(value, PaymentResponse.class));
        } catch (Exception e) {
            // Redis indisponível: degradação graciosa — não bloqueia o fluxo de pagamento
            log.warn("[Idempotência] Falha ao consultar Redis: {}", e.getMessage());
            return Optional.empty();
        }
    }

    @Override
    public void set(String key, PaymentResponse response) {
        try {
            String value = objectMapper.writeValueAsString(response);
            redisTemplate.opsForValue().set(key, value, TTL);
        } catch (Exception e) {
            // Redis indisponível: degradação graciosa — pagamento já foi processado com sucesso
            log.warn("[Idempotência] Falha ao salvar no Redis: {}", e.getMessage());
        }
    }
}
