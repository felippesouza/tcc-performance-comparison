// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.adapter.controller;

import com.tcc.gateway.adapter.cache.IdempotencyCache;
import com.tcc.gateway.adapter.controller.dto.PaymentRequest;
import com.tcc.gateway.adapter.controller.dto.PaymentResponse;
import com.tcc.gateway.adapter.mapper.PaymentRestMapper;
import com.tcc.gateway.usecase.ProcessPaymentUseCase;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/payments")
public class PaymentController implements PaymentControllerDocs {

    private final ProcessPaymentUseCase processPaymentUseCase;
    private final PaymentRestMapper mapper;
    private final IdempotencyCache idempotencyCache;

    public PaymentController(
            ProcessPaymentUseCase processPaymentUseCase,
            PaymentRestMapper mapper,
            IdempotencyCache idempotencyCache) {
        this.processPaymentUseCase = processPaymentUseCase;
        this.mapper = mapper;
        this.idempotencyCache = idempotencyCache;
    }

    @Override
    @PostMapping
    public ResponseEntity<PaymentResponse> create(
            @RequestHeader(value = "X-Idempotency-Key", required = false) String idempotencyKey,
            @Valid @RequestBody PaymentRequest request) {

        // 1. Verificação de idempotência: se a chave já foi processada, retorna o resultado cacheado.
        // Evita cobrar o cliente duas vezes em caso de retry/timeout de rede.
        if (idempotencyKey != null) {
            var cached = idempotencyCache.get(idempotencyKey);
            if (cached.isPresent()) {
                return ResponseEntity.status(HttpStatus.CREATED).body(cached.get());
            }
        }

        // 2. Processar o pagamento (Virtual Threads gerenciam o bloqueio de I/O)
        var payment = mapper.toDomain(request);
        var processed = processPaymentUseCase.execute(payment);
        var response = mapper.toResponse(processed);

        // 3. Armazena no Redis para futuros retries com a mesma chave de idempotência
        if (idempotencyKey != null) {
            idempotencyCache.set(idempotencyKey, response);
        }

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
