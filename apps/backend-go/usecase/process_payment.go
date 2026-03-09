package usecase

import (
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/tcc/backend-go/domain"
)

// ProcessPaymentUseCase define a interface de entrada para a orquestração do pagamento.
type ProcessPaymentUseCase interface {
	Execute(request domain.Payment) (*domain.Payment, error)
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
func (i *ProcessPaymentInteractor) Execute(request domain.Payment) (*domain.Payment, error) {
	// 1. Persistir pagamento inicial (PENDENTE)
	payment := domain.Payment{
		ID:         uuid.New().String(),
		Amount:     request.Amount,
		CardNumber: request.CardNumber,
		Status:     "PENDING",
		ExternalID: nil,
		CreatedAt:  time.Now(),
	}

	savedPayment, err := i.repository.Save(payment)
	if err != nil {
		return nil, errors.New("falha ao salvar o pagamento inicial: " + err.Error())
	}

	// 2. Chamar Gateway Externo (Aqui é onde as Goroutines brilham aguardando o I/O bloqueante)
	response, err := i.externalGateway.Process(savedPayment)
	if err != nil {
		// Retorna erro, mas o status no banco continua PENDING, mantendo a consistência.
		return nil, errors.New("timeout ou falha na adquirente externa: " + err.Error())
	}

	// 3. Atualizar status baseado na resposta externa
	finalStatus := "REJECTED"
	if response.Approved {
		finalStatus = "APPROVED"
	}

	extID := response.ExternalID
	updatedPayment := savedPayment.WithStatus(finalStatus, &extID)

	finalPayment, err := i.repository.Save(updatedPayment)
	if err != nil {
		return nil, errors.New("falha ao atualizar status final: " + err.Error())
	}

	return &finalPayment, nil
}
