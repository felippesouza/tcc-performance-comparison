package domain

import (
	"time"
)

// Payment representa a entidade central do domínio de negócio.
type Payment struct {
	ID         string
	Amount     float64
	CardNumber string
	Status     string
	ExternalID *string
	CreatedAt  time.Time
}

// WithStatus retorna uma nova instância de Payment com o status atualizado (Imutabilidade).
func (p Payment) WithStatus(status string, extID *string) Payment {
	return Payment{
		ID:         p.ID,
		Amount:     p.Amount,
		CardNumber: p.CardNumber,
		Status:     status,
		ExternalID: extID,
		CreatedAt:  p.CreatedAt,
	}
}

// PaymentRepository define o contrato para persistência.
type PaymentRepository interface {
	Save(payment Payment) (Payment, error)
	FindByID(id string) (*Payment, error)
}

// PaymentResponse representa o retorno da adquirente externa.
type PaymentResponse struct {
	ExternalID string
	Approved   bool
}

// ExternalGateway define o contrato para comunicação HTTP com o serviço de Mock.
type ExternalGateway interface {
	Process(payment Payment) (PaymentResponse, error)
}
