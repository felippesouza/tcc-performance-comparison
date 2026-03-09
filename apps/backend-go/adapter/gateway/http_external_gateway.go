package gateway

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"time"

	"github.com/tcc/backend-go/domain"
)

// HttpExternalGateway é a implementação para chamadas REST.
type HttpExternalGateway struct {
	client *http.Client
	url    string
}

// NewHttpExternalGateway constrói o gateway com um cliente HTTP configurado com timeout.
func NewHttpExternalGateway(url string) *HttpExternalGateway {
	return &HttpExternalGateway{
		client: &http.Client{
			Timeout: 5 * time.Second, // Timeout alinhado com boas práticas para evitar travamento infinito
		},
		url: url,
	}
}

// Process realiza a requisição POST para a API externa (simulada).
// Em Go, essa chamada é "bloqueante" apenas na Goroutine atual. A thread do SO é liberada.
func (h *HttpExternalGateway) Process(payment domain.Payment) (domain.PaymentResponse, error) {
	// Serialização do payload
	payload, err := json.Marshal(payment)
	if err != nil {
		return domain.PaymentResponse{}, err
	}

	// Execução da requisição
	resp, err := h.client.Post(h.url, "application/json", bytes.NewBuffer(payload))
	if err != nil {
		return domain.PaymentResponse{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return domain.PaymentResponse{}, errors.New("adquirente retornou status inválido")
	}

	// Desserialização da resposta (Note como no Go nós mapeamos o JSON diretamente para uma struct intermediária)
	var extResponse struct {
		ExternalID string `json:"external_id"`
		Approved   bool   `json:"approved"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&extResponse); err != nil {
		return domain.PaymentResponse{}, err
	}

	return domain.PaymentResponse{
		ExternalID: extResponse.ExternalID,
		Approved:   extResponse.Approved,
	}, nil
}
