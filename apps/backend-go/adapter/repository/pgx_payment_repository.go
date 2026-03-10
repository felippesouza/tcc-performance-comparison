// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package repository

import (
	"context"
	"errors"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/tcc/backend-go/domain"
)

// PgxPaymentRepository é a implementação do PaymentRepository para PostgreSQL.
type PgxPaymentRepository struct {
	dbPool *pgxpool.Pool
}

// NewPgxPaymentRepository constrói o adaptador de banco de dados.
func NewPgxPaymentRepository(pool *pgxpool.Pool) *PgxPaymentRepository {
	return &PgxPaymentRepository{dbPool: pool}
}

// Save persiste ou atualiza a entidade de domínio no PostgreSQL.
func (r *PgxPaymentRepository) Save(ctx context.Context, payment domain.Payment) (domain.Payment, error) {
	query := `
		INSERT INTO payments (id, amount, card_number, status, external_id, created_at)
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (id) 
		DO UPDATE SET status = EXCLUDED.status, external_id = EXCLUDED.external_id
	`
	// Utiliza o contexto propagado da requisição HTTP
	_, err := r.dbPool.Exec(ctx, query,
		payment.ID, payment.Amount, payment.CardNumber, payment.Status, payment.ExternalID, payment.CreatedAt)

	if err != nil {
		return domain.Payment{}, err
	}

	return payment, nil
}

// FindByID busca a entidade no banco (para completar a interface, embora não usemos no Use Case agora).
func (r *PgxPaymentRepository) FindByID(ctx context.Context, id string) (*domain.Payment, error) {
	query := `SELECT id, amount, card_number, status, external_id, created_at FROM payments WHERE id = $1`
	
	var p domain.Payment
	err := r.dbPool.QueryRow(ctx, query, id).Scan(
		&p.ID, &p.Amount, &p.CardNumber, &p.Status, &p.ExternalID, &p.CreatedAt,
	)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, nil // Não encontrado
		}
		return nil, err
	}

	return &p, nil
}
