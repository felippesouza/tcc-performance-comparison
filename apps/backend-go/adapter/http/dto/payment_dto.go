// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package dto

// PaymentRequest define a carga útil de entrada com tags de validação.
type PaymentRequest struct {
	Amount     float64 `json:"amount" binding:"required,gt=0"`
	CardNumber string  `json:"cardNumber" binding:"required,min=13,max=19"`
}

// PaymentResponse define a carga útil de saída.
type PaymentResponse struct {
	ID         string `json:"id"`
	Status     string `json:"status"`
	ExternalID string `json:"externalId,omitempty"`
}
