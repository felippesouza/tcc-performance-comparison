package main

import (
	"context"
	"log"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"

	"github.com/tcc/backend-go/adapter/gateway"
	"github.com/tcc/backend-go/adapter/http/controller"
	"github.com/tcc/backend-go/adapter/repository"
	"github.com/tcc/backend-go/usecase"

	// Necessário para a geração do Swagger
	_ "github.com/tcc/backend-go/docs"
)

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
	config.MaxConns = 50

	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		log.Fatalf("Erro ao conectar no banco de dados: %v", err)
	}
	defer pool.Close()

	// 2. Criação do schema (Apenas para TCC; em prod usaríamos o Flyway/Liquibase)
	_, _ = pool.Exec(context.Background(), `
		CREATE TABLE IF NOT EXISTS payments (
			id VARCHAR(36) PRIMARY KEY,
			amount NUMERIC(10, 2) NOT NULL,
			card_number VARCHAR(19) NOT NULL,
			status VARCHAR(20) NOT NULL,
			external_id VARCHAR(50),
			created_at TIMESTAMP NOT NULL
		);
	`)

	// 3. Injeção de Dependências Manual (Clean Architecture)
	repo := repository.NewPgxPaymentRepository(pool)
	
	mockAPIUrl := "http://localhost:8080/process-payment"
	if envMock := os.Getenv("MOCK_API_URL"); envMock != "" {
		mockAPIUrl = envMock
	}
	extGateway := gateway.NewHttpExternalGateway(mockAPIUrl)
	
	interactor := usecase.NewProcessPaymentInteractor(repo, extGateway)
	paymentController := controller.NewPaymentController(interactor)

	// 4. Configuração do Roteador (Gin)
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())

	// Endpoint de Pagamentos
	r.POST("/payments", paymentController.CreatePayment)

	// Endpoint Swagger
	r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	// Endpoint Health Check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "UP"})
	})

	// Endpoint Prometheus
	r.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// 5. Iniciando o servidor na porta 8082 (Java está na 8081)
	port := "8082"
	if envPort := os.Getenv("PORT"); envPort != "" {
		port = envPort
	}
	
	log.Printf("Iniciando backend Go (Goroutines) na porta %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Erro ao iniciar o servidor: %v", err)
	}
}
