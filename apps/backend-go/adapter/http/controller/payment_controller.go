// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package controller

import (
	"errors"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/tcc/backend-go/adapter/cache"
	"github.com/tcc/backend-go/adapter/http/dto"
	"github.com/tcc/backend-go/adapter/mapper"
	"github.com/tcc/backend-go/domain"
	"github.com/tcc/backend-go/usecase"
)

// PaymentController é o handler HTTP para a rota de pagamentos.
type PaymentController struct {
	useCase     usecase.ProcessPaymentUseCase
	idempotency cache.IdempotencyCache
}

// NewPaymentController constrói o controller com injeção do Use Case e do cache de idempotência.
func NewPaymentController(uc usecase.ProcessPaymentUseCase, ic cache.IdempotencyCache) *PaymentController {
	return &PaymentController{useCase: uc, idempotency: ic}
}

// CreatePayment godoc
// @Summary Processar um novo pagamento
// @Description Recebe os dados do cartão, valida e consulta a adquirente externa. Suporta idempotência via header X-Idempotency-Key para evitar cobranças duplicadas em retries.
// @Tags Payment Gateway
// @Accept json
// @Produce json
// @Param X-Idempotency-Key header string false "Chave de idempotência para evitar cobranças duplicadas em retries"
// @Param request body dto.PaymentRequest true "Dados para criação de um novo pagamento"
// @Success 201 {object} dto.PaymentResponse "Pagamento processado com sucesso"
// @Failure 400 {object} map[string]string "Dados da requisição inválidos ou falha de negócio"
// @Failure 500 {object} map[string]string "Erro interno no servidor ou timeout da adquirente"
// @Router /payments [post]
func (c *PaymentController) CreatePayment(ctx *gin.Context) {
	var req dto.PaymentRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "dados inválidos: " + err.Error()})
		return
	}

	// 1. Verificação de idempotência: se a chave já foi processada, retorna o resultado cacheado.
	// Evita cobrar o cliente duas vezes em caso de retry/timeout de rede.
	idempotencyKey := ctx.GetHeader("X-Idempotency-Key")
	if idempotencyKey != "" {
		if cached, err := c.idempotency.Get(ctx.Request.Context(), idempotencyKey); err == nil && cached != nil {
			ctx.JSON(http.StatusCreated, cached)
			return
		} else if err != nil {
			// Redis indisponível: degradação graciosa — procede sem proteção de idempotência
			log.Printf("[WARN] Redis indisponível para leitura de idempotência: %v", err)
		}
	}

	// 2. Processar o pagamento propagando o contexto da requisição HTTP
	paymentDomain := mapper.ToDomain(req)
	processed, err := c.useCase.Execute(ctx.Request.Context(), paymentDomain)
	if err != nil {
		// DomainError → 400, erros de infraestrutura → 500
		var domainErr *domain.DomainError
		if errors.As(err, &domainErr) {
			ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	response := mapper.ToResponse(processed)

	// 3. Armazena no Redis para futuros retries com a mesma chave de idempotência
	if idempotencyKey != "" {
		if err := c.idempotency.Set(ctx.Request.Context(), idempotencyKey, response); err != nil {
			// Redis indisponível: pagamento já foi processado com sucesso, só loga o aviso
			log.Printf("[WARN] Falha ao salvar idempotência no Redis: %v", err)
		}
	}

	ctx.JSON(http.StatusCreated, response)
}
