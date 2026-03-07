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

func main() {
	r := gin.Default()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	minLat, _ := strconv.Atoi(os.Getenv("MIN_LATENCY_MS"))
	maxLat, _ := strconv.Atoi(os.Getenv("MAX_LATENCY_MS"))

	if minLat == 0 { minLat = 200 }
	if maxLat == 0 { maxLat = 500 }

	r.POST("/process-payment", func(c *gin.Context) {
		// Simula latência variável
		latency := rand.Intn(maxLat-minLat) + minLat
		time.Sleep(time.Duration(latency) * time.Millisecond)

		// Simula aprovação (90% de sucesso)
		approved := rand.Float32() < 0.9

		c.JSON(http.StatusOK, gin.H{
			"status":      "processed",
			"latency_ms":  latency,
			"approved":    approved,
			"external_id": fmt.Sprintf("ext_%d", time.Now().UnixNano()),
		})
	})

	r.Run(":" + port)
}
