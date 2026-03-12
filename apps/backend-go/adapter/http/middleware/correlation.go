// ============================================================
// TCC — Comparacao de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituicao: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositorio: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package middleware

import (
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

const CorrelationIDHeader = "X-Correlation-ID"

// CorrelationID e um middleware Gin que propaga ou gera um X-Correlation-ID por requisicao.
// Armazena o ID no contexto Gin para acesso nas camadas inferiores.
// Equivalente arquitetural do CorrelationIdFilter (Jakarta Filter) do backend Java.
func CorrelationID() gin.HandlerFunc {
	return func(c *gin.Context) {
		correlationID := c.GetHeader(CorrelationIDHeader)
		if correlationID == "" {
			correlationID = uuid.New().String()
		}

		// Propaga no contexto Gin (acessivel via c.GetString) e no header de resposta
		c.Set(CorrelationIDHeader, correlationID)
		c.Header(CorrelationIDHeader, correlationID)

		c.Next()
	}
}
