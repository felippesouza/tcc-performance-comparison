// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/tcc/backend-go/domain"
)

// ProcessPaymentUseCase define a interface de entrada para a orquestração do pagamento.
type ProcessPaymentUseCase interface {
	Execute(ctx context.Context, request domain.Payment) (*domain.Payment, error)
}

// ProcessPaymentInteractor é a implementação da regra de negócio.
type ProcessPaymentInteractor struct {
	repository      domain.PaymentRepository
	externalGateway domain.ExternalGateway
}

// NewProcessPaymentInteractor atua como o "construtor" para injeção de dependências.
func NewProcessPaymentInteractor(repo domain.PaymentRepository, gateway domain.ExternalGateway) *ProcessPaymentInteractor {
	return &ProcessPaymentInteractor{
		repository:      repo,
		externalGateway: gateway,
	}
}

// Execute realiza a orquestração do fluxo de pagamento.
func (i *ProcessPaymentInteractor) Execute(ctx context.Context, request domain.Payment) (*domain.Payment, error) {
	// 0. Validação de domínio: invariantes da entidade antes de qualquer I/O.
	// Simétrico ao compact constructor do Payment.java — garante que regras de negócio
	// são aplicadas independente da camada HTTP.
	if err := request.Validate(); err != nil {
		return nil, err
	}

	// 1. Persistir pagamento inicial (PENDENTE)
	payment := domain.Payment{
		ID:         uuid.New().String(),
		Amount:     request.Amount,
		CardNumber: request.CardNumber,
		Status:     "PENDING",
		ExternalID: nil,
		CreatedAt:  time.Now(),
	}

	savedPayment, err := i.repository.Save(ctx, payment)
	if err != nil {
		return nil, fmt.Errorf("falha ao salvar o pagamento inicial: %w", err)
	}

	// 2. Chamar Gateway Externo (O ctx propagado garante que se a req HTTP cair, isso aqui aborta)
	response, err := i.externalGateway.Process(ctx, savedPayment)
	if err != nil {
		// Retorna erro, mas o status no banco continua PENDING, mantendo a consistência.
		return nil, fmt.Errorf("timeout ou falha na adquirente externa: %w", err)
	}

	// 3. Atualizar status baseado na resposta externa
	finalStatus := "REJECTED"
	if response.Approved {
		finalStatus = "APPROVED"
	}

	extID := response.ExternalID
	updatedPayment := savedPayment.WithStatus(finalStatus, &extID)

	finalPayment, err := i.repository.Save(ctx, updatedPayment)
	if err != nil {
		return nil, fmt.Errorf("falha ao atualizar status final: %w", err)
	}

	return &finalPayment, nil
}
