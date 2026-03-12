// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package domain

import (
	"context"
	"fmt"
	"time"
)

// DomainError representa erros de regra de negócio (equivalente ao DomainException do Java).
// Permite que o controller distinga 400 (Bad Request) de 500 (Internal Server Error).
type DomainError struct {
	Message string
}

func (e *DomainError) Error() string {
	return e.Message
}

// NewDomainError cria um erro de domínio formatado.
func NewDomainError(format string, args ...any) *DomainError {
	return &DomainError{Message: fmt.Sprintf(format, args...)}
}

// Payment representa a entidade central do domínio de negócio.
//
// Nota sobre o tipo monetário (float64 vs BigDecimal):
// O Java usa BigDecimal para precisão decimal exata. Go não tem um tipo decimal nativo;
// em produção, usaríamos github.com/shopspring/decimal. Para este TCC, float64 é uma
// simplificação consciente: a precisão monetária é mantida pelo PostgreSQL (NUMERIC 10,2)
// e o foco da comparação é o modelo de concorrência, não aritmética de ponto flutuante.
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

// Validate verifica as invariantes do domínio na criação da entidade Payment.
// Simétrico ao compact constructor do record Payment.java no backend Java.
// Retorna DomainError (→ HTTP 400) para dados inválidos de negócio.
func (p Payment) Validate() error {
	if p.Amount <= 0 {
		return NewDomainError("o valor do pagamento deve ser maior que zero")
	}
	if len(p.CardNumber) < 13 || len(p.CardNumber) > 19 {
		return NewDomainError("o número do cartão deve ter entre 13 e 19 caracteres")
	}
	return nil
}

// PaymentRepository define o contrato para persistência.
type PaymentRepository interface {
	Save(ctx context.Context, payment Payment) (Payment, error)
	FindByID(ctx context.Context, id string) (*Payment, error)
}

// PaymentResponse representa o retorno da adquirente externa.
type PaymentResponse struct {
	ExternalID string
	Approved   bool
}

// ExternalGateway define o contrato para comunicação HTTP com o serviço de Mock.
type ExternalGateway interface {
	Process(ctx context.Context, payment Payment) (PaymentResponse, error)
}
