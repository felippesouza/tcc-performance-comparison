FROM golang:1.25-alpine AS builder

# Configura o proxy do Go para evitar problemas de rede
ENV GOPROXY=https://proxy.golang.org,direct

WORKDIR /app

# Copia os arquivos de dependência primeiro para aproveitar o cache do Docker
COPY go.mod go.sum ./
RUN go mod download

# Copia o código e faz o build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/main .

# Porta padrão do mock
EXPOSE 8080

CMD ["./main"]
