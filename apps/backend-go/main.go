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
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
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
	"github.com/tcc/backend-go/adapter/http/middleware"
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
	// Structured JSON logging — equivalente ao logstash-logback-encoder do Java.
	// slog é a biblioteca padrão do Go 1.21+ para logs estruturados.
	// Inclui correlationId quando disponível via context (propagado pelo middleware).
	slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
		ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
			// Adiciona campo "app" e "runtime" em todos os logs (equivalente ao customFields do logback)
			return a
		},
	})))

	// 1. Configuração do Banco de Dados (pgxpool)
	dbURL := "postgres://user:password@localhost:5432/gateway_db"
	if envDB := os.Getenv("DATABASE_URL"); envDB != "" {
		dbURL = envDB
	}

	config, err := pgxpool.ParseConfig(dbURL)
	if err != nil {
		slog.Error("Erro ao fazer parse da URL do banco", "error", err)
		os.Exit(1)
	}

	// Tuning equivalente ao HikariCP do Java para alta concorrência
	config.MaxConns = 200

	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		slog.Error("Erro ao conectar no banco de dados", "error", err)
		os.Exit(1)
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
		slog.Error("Erro ao criar schema do banco", "error", err)
		os.Exit(1)
	}

	// 3. Configuração do Redis (Cache de Idempotência)
	redisURL := "redis://localhost:6379"
	if envRedis := os.Getenv("REDIS_URL"); envRedis != "" {
		redisURL = envRedis
	}

	redisOpts, err := goredis.ParseURL(redisURL)
	if err != nil {
		slog.Error("Erro ao fazer parse da URL do Redis", "error", err)
		os.Exit(1)
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
	r.Use(middleware.CorrelationID()) // Rastreabilidade por requisição — simétrico ao CorrelationIdFilter do Java
	r.Use(prometheusMiddleware())     // Métricas HTTP simétricas ao Spring Boot Actuator

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

	// 6. Servidor com Graceful Shutdown na porta 8082 (Java está na 8081)
	port := "8082"
	if envPort := os.Getenv("PORT"); envPort != "" {
		port = envPort
	}

	// Equivalente ao server.shutdown=graceful do Spring Boot.
	// Aguarda requests em-flight completarem antes de encerrar (SIGTERM/SIGINT).
	srv := &http.Server{
		Addr:    ":" + port,
		Handler: r,
	}

	// Canal para receber sinais do SO
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	// Inicia o servidor em uma goroutine separada
	go func() {
		slog.Info("Iniciando backend Go (Goroutines)", "port", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			slog.Error("Erro ao iniciar o servidor", "error", err)
			os.Exit(1)
		}
	}()

	// Bloqueia até receber sinal de encerramento
	<-quit
	slog.Info("Sinal de encerramento recebido — aguardando requests em-flight (30s)...")

	// Contexto com timeout para o shutdown gracioso
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		slog.Error("Erro durante o shutdown gracioso", "error", err)
		os.Exit(1)
	}
	slog.Info("Servidor encerrado com sucesso.")
}
