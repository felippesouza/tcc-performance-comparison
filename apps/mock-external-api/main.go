// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2025
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package main

import (
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

// newRand cria um gerador local por chamada para evitar contenção de mutex
// no rand global sob alta concorrência (200+ goroutines simultâneas no benchmark).
func newRand() *rand.Rand {
	return rand.New(rand.NewSource(time.Now().UnixNano()))
}

func main() {
	// gin.ReleaseMode + gin.New() remove o logger built-in do Gin.
	// Sob 200+ VUs o logger do gin.Default() gera I/O por request e pode se tornar
	// um gargalo no mock que distorce os resultados do benchmark.
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	minLat, _ := strconv.Atoi(os.Getenv("MIN_LATENCY_MS"))
	maxLat, _ := strconv.Atoi(os.Getenv("MAX_LATENCY_MS"))

	if minLat == 0 { minLat = 200 }
	if maxLat == 0 { maxLat = 500 }

	r.POST("/process-payment", func(c *gin.Context) {
		// Rand local por request: elimina contenção de mutex do rand global
		rng := newRand()
		latency := rng.Intn(maxLat-minLat) + minLat
		time.Sleep(time.Duration(latency) * time.Millisecond)

		// Simula aprovação (90% de sucesso)
		approved := rng.Float32() < 0.9

		c.JSON(http.StatusOK, gin.H{
			"status":      "processed",
			"latency_ms":  latency,
			"approved":    approved,
			"external_id": fmt.Sprintf("ext_%d", time.Now().UnixNano()),
		})
	})

	r.Run(":" + port)
}
