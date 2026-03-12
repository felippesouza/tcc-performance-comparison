// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
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
