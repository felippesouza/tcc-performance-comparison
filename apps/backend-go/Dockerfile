# Stage 1: Build
FROM golang:1.25-alpine AS builder

# Variáveis de ambiente para build otimizado no Go
ENV GO111MODULE=on \
    CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64

WORKDIR /app

# Copia e baixa dependências primeiro
COPY go.mod go.sum ./
RUN go mod download

# Copia o código fonte e faz o build
COPY . .
RUN go build -o backend-go main.go

# Stage 2: Runtime (Imagem minúscula)
FROM alpine:latest

WORKDIR /root/
# Copia o binário compilado do estágio anterior
COPY --from=builder /app/backend-go .

EXPOSE 8082

CMD ["./backend-go"]