// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package main

import (
	"context"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	goredis "github.com/redis/go-redis/v9"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"

	"github.com/tcc/backend-go/adapter/cache"
	"github.com/tcc/backend-go/adapter/gateway"
	"github.com/tcc/backend-go/adapter/http/controller"
	"github.com/tcc/backend-go/adapter/repository"
	"github.com/tcc/backend-go/usecase"

	// Necessário para a geração do Swagger
	_ "github.com/tcc/backend-go/docs"
)

// httpRequestDuration expõe métricas HTTP equivalentes ao Spring Boot Actuator.
// Nome e labels idênticos ao Micrometer para queries simétricas no Grafana.
var httpRequestDuration = prometheus.NewHistogramVec(
	prometheus.HistogramOpts{
		Name:    "http_server_requests_seconds",
		Help:    "Duração das requisições HTTP em segundos",
		Buckets: []float64{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5},
	},
	[]string{"method", "uri", "status", "outcome"},
)

func init() {
	prometheus.MustRegister(httpRequestDuration)
}

// prometheusMiddleware registra a duração de cada request com os mesmos labels
// que o Spring Boot Actuator usa, permitindo queries idênticas no Grafana.
func prometheusMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		c.Next()

		status := c.Writer.Status()
		outcome := "SUCCESS"
		if status >= 500 {
			outcome = "SERVER_ERROR"
		} else if status >= 400 {
			outcome = "CLIENT_ERROR"
		}

		httpRequestDuration.WithLabelValues(
			c.Request.Method,
			c.FullPath(),
			strconv.Itoa(status),
			outcome,
		).Observe(time.Since(start).Seconds())
	}
}

// @title TCC Performance Gateway API
// @version 1.0
// @description Backend em Go utilizando Goroutines para o TCC de Engenharia de Software.
// @host localhost:8082
// @BasePath /
func main() {
	// 1. Configuração do Banco de Dados (pgxpool)
	dbURL := "postgres://user:password@localhost:5432/gateway_db"
	if envDB := os.Getenv("DATABASE_URL"); envDB != "" {
		dbURL = envDB
	}

	config, err := pgxpool.ParseConfig(dbURL)
	if err != nil {
		log.Fatalf("Erro ao fazer parse da URL do banco: %v", err)
	}

	// Tuning equivalente ao HikariCP do Java para alta concorrência
	config.MaxConns = 200

	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		log.Fatalf("Erro ao conectar no banco de dados: %v", err)
	}
	defer pool.Close()

	// 2. Criação do schema (Apenas para TCC; em prod usaríamos o Flyway/Liquibase)
	if _, err = pool.Exec(context.Background(), `
		CREATE TABLE IF NOT EXISTS payments (
			id VARCHAR(36) PRIMARY KEY,
			amount NUMERIC(10, 2) NOT NULL,
			card_number VARCHAR(19) NOT NULL,
			status VARCHAR(20) NOT NULL,
			external_id VARCHAR(50),
			created_at TIMESTAMP NOT NULL
		);
	`); err != nil {
		log.Fatalf("Erro ao criar schema do banco: %v", err)
	}

	// 3. Configuração do Redis (Cache de Idempotência)
	redisURL := "redis://localhost:6379"
	if envRedis := os.Getenv("REDIS_URL"); envRedis != "" {
		redisURL = envRedis
	}

	redisOpts, err := goredis.ParseURL(redisURL)
	if err != nil {
		log.Fatalf("Erro ao fazer parse da URL do Redis: %v", err)
	}

	redisClient := goredis.NewClient(redisOpts)
	defer redisClient.Close()

	idempotencyCache := cache.NewRedisIdempotencyCache(redisClient)

	// 4. Injeção de Dependências Manual (Clean Architecture)
	repo := repository.NewPgxPaymentRepository(pool)

	mockAPIUrl := "http://localhost:8080/process-payment"
	if envMock := os.Getenv("MOCK_API_URL"); envMock != "" {
		mockAPIUrl = envMock
	}
	extGateway := gateway.NewHttpExternalGateway(mockAPIUrl)

	interactor := usecase.NewProcessPaymentInteractor(repo, extGateway)
	paymentController := controller.NewPaymentController(interactor, idempotencyCache)

	// 5. Configuração do Roteador (Gin)
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(prometheusMiddleware()) // Métricas HTTP simétricas ao Spring Boot Actuator

	// Endpoint de Pagamentos
	r.POST("/payments", paymentController.CreatePayment)

	// Endpoint Swagger
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	// Endpoint Health Check — verifica conectividade real com o banco
	r.GET("/health", func(c *gin.Context) {
		if err := pool.Ping(c.Request.Context()); err != nil {
			c.JSON(503, gin.H{"status": "DOWN", "error": err.Error()})
			return
		}
		c.JSON(200, gin.H{"status": "UP"})
	})

	// Endpoint Prometheus
	r.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// 6. Iniciando o servidor na porta 8082 (Java está na 8081)
	port := "8082"
	if envPort := os.Getenv("PORT"); envPort != "" {
		port = envPort
	}

	log.Printf("Iniciando backend Go (Goroutines) na porta %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Erro ao iniciar o servidor: %v", err)
	}
}
