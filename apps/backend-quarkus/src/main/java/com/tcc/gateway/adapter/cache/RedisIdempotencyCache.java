// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.cache;

import io.quarkus.redis.datasource.RedisDataSource;
import io.quarkus.redis.datasource.string.StringCommands;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.jboss.logging.Logger;

import java.time.Duration;
import java.util.Optional;

@ApplicationScoped
public class RedisIdempotencyCache implements IdempotencyCache {

    private static final Logger LOG = Logger.getLogger(RedisIdempotencyCache.class);
    private static final Duration TTL = Duration.ofHours(24);

    private final StringCommands<String, String> commands;

    @Inject
    public RedisIdempotencyCache(RedisDataSource ds) {
        this.commands = ds.string(String.class);
    }

    @Override
    public Optional<String> get(String key) {
        try {
            return Optional.ofNullable(commands.get(key));
        } catch (Exception e) {
            LOG.warnf("Redis get failed for key %s: %s", key, e.getMessage());
            return Optional.empty();
        }
    }

    @Override
    public void put(String key, String value) {
        try {
            commands.setex(key, TTL.getSeconds(), value);
        } catch (Exception e) {
            LOG.warnf("Redis put failed for key %s: %s", key, e.getMessage());
        }
    }
}
