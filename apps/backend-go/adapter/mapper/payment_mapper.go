package mapper

import (
	"github.com/tcc/backend-go/adapter/http/dto"
	"github.com/tcc/backend-go/domain"
)

// ToDomain converte a requisição HTTP para o modelo de domínio puro.
func ToDomain(req dto.PaymentRequest) domain.Payment {
	return domain.Payment{
		Amount:     req.Amount,
		CardNumber: req.CardNumber,
	}
}

// ToResponse converte a resposta do domínio para o DTO de saída.
func ToResponse(payment *domain.Payment) dto.PaymentResponse {
	extID := ""
	if payment.ExternalID != nil {
		extID = *payment.ExternalID
	}
	return dto.PaymentResponse{
		ID:         payment.ID,
		Status:     payment.Status,
		ExternalID: extID,
	}
}
