package com.tcc.gateway.adapter.controller;

import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.usecase.ProcessPaymentUseCase;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.math.BigDecimal;

@RestController
@RequestMapping("/payments")
@RequiredArgsConstructor
public class PaymentController {

    private final ProcessPaymentUseCase processPaymentUseCase;

    @PostMapping
    public ResponseEntity<PaymentResponse> create(@RequestBody PaymentRequest request) {
        var payment = new Payment(null, request.amount(), request.cardNumber(), null, null, null);
        var processed = processPaymentUseCase.execute(payment);
        
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(new PaymentResponse(processed.id(), processed.status(), processed.externalId()));
    }

    record PaymentRequest(BigDecimal amount, String cardNumber) {}
    record PaymentResponse(String id, String status, String externalId) {}
}
