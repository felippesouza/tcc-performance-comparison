# Stage 1: Build
FROM golang:1.25-alpine AS builder

# Variáveis de ambiente para build otimizado no Go
# GOFLAGS=-mod=mod permite que o build atualize go.sum automaticamente se ausente
ENV GO111MODULE=on \
    CGO_ENABLED=0 \
    GOOS=linux \
    GOARCH=amd64 \
    GOFLAGS=-mod=mod

WORKDIR /app

# Copia go.mod e resolve/baixa dependências (go.sum é gerado automaticamente)
COPY go.mod ./
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
