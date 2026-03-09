package com.tcc.gateway.adapter.controller;

import com.tcc.gateway.adapter.controller.dto.PaymentRequest;
import com.tcc.gateway.adapter.controller.dto.PaymentResponse;
import com.tcc.gateway.adapter.mapper.PaymentRestMapper;
import com.tcc.gateway.usecase.ProcessPaymentUseCase;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/payments")
public class PaymentController implements PaymentControllerDocs {

    private final ProcessPaymentUseCase processPaymentUseCase;
    private final PaymentRestMapper mapper;

    public PaymentController(ProcessPaymentUseCase processPaymentUseCase, PaymentRestMapper mapper) {
        this.processPaymentUseCase = processPaymentUseCase;
        this.mapper = mapper;
    }

    @Override
    @PostMapping
    public ResponseEntity<PaymentResponse> create(@Valid @RequestBody PaymentRequest request) {
        var payment = mapper.toDomain(request);
        var processed = processPaymentUseCase.execute(payment);
        
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(mapper.toResponse(processed));
    }
}
