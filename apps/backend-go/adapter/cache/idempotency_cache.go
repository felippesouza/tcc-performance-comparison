// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package cache

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/tcc/backend-go/adapter/http/dto"
)

const idempotencyTTL = 24 * time.Hour

// IdempotencyCache define o contrato para verificação de idempotência.
// Permite que o controller evite reprocessar o mesmo pagamento em retries do cliente.
type IdempotencyCache interface {
	Get(ctx context.Context, key string) (*dto.PaymentResponse, error)
	Set(ctx context.Context, key string, response dto.PaymentResponse) error
}

// RedisIdempotencyCache é a implementação usando Redis.
// Equivalente ao RedisIdempotencyCache do Java (spring-data-redis + StringRedisTemplate).
type RedisIdempotencyCache struct {
	client *redis.Client
}

// NewRedisIdempotencyCache constrói o adaptador Redis.
func NewRedisIdempotencyCache(client *redis.Client) *RedisIdempotencyCache {
	return &RedisIdempotencyCache{client: client}
}

// Get busca uma resposta cacheada pela chave de idempotência.
// Retorna (nil, nil) se a chave não existir — ausência não é erro.
func (r *RedisIdempotencyCache) Get(ctx context.Context, key string) (*dto.PaymentResponse, error) {
	val, err := r.client.Get(ctx, key).Result()
	if errors.Is(err, redis.Nil) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	var response dto.PaymentResponse
	if err := json.Unmarshal([]byte(val), &response); err != nil {
		return nil, err
	}
	return &response, nil
}

// Set armazena a resposta no Redis com TTL de 24h.
func (r *RedisIdempotencyCache) Set(ctx context.Context, key string, response dto.PaymentResponse) error {
	data, err := json.Marshal(response)
	if err != nil {
		return err
	}
	return r.client.Set(ctx, key, data, idempotencyTTL).Err()
}
