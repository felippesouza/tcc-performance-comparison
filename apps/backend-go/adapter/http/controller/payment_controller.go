package controller

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/tcc/backend-go/adapter/http/dto"
	"github.com/tcc/backend-go/adapter/mapper"
	"github.com/tcc/backend-go/usecase"
)

// PaymentController é o handler HTTP para a rota de pagamentos.
type PaymentController struct {
	useCase usecase.ProcessPaymentUseCase
}

// NewPaymentController constrói o controller com a injeção do Use Case.
func NewPaymentController(uc usecase.ProcessPaymentUseCase) *PaymentController {
	return &PaymentController{useCase: uc}
}

// CreatePayment godoc
// @Summary Processar um novo pagamento
// @Description Este endpoint recebe os dados de um cartão, valida a transação e consulta a adquirente externa.
// @Tags Payment Gateway
// @Accept json
// @Produce json
// @Param request body dto.PaymentRequest true "Dados para criação de um novo pagamento"
// @Success 201 {object} dto.PaymentResponse "Pagamento processado com sucesso"
// @Failure 400 {object} map[string]string "Dados da requisição inválidos ou falha de negócio"
// @Failure 500 {object} map[string]string "Erro interno no servidor ou timeout da adquirente"
// @Router /payments [post]
func (c *PaymentController) CreatePayment(ctx *gin.Context) {
	var req dto.PaymentRequest

	// BindJSON já realiza a validação baseada nas tags `binding` do DTO
	if err := ctx.ShouldBindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "dados inválidos: " + err.Error()})
		return
	}

	// Mapeamento e chamada ao Use Case propagando o contexto da requisição HTTP
	paymentDomain := mapper.ToDomain(req)
	
	processed, err := c.useCase.Execute(ctx.Request.Context(), paymentDomain)
	if err != nil {
		// Em um projeto real, você tiparia os erros de domínio para saber se é 400 ou 500.
		// Para o escopo do TCC, qualquer falha no fluxo de negócio/infra retornará 500.
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Resposta
	response := mapper.ToResponse(processed)
	ctx.JSON(http.StatusCreated, response)
}
