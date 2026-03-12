// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.usecase;

import com.tcc.gateway.domain.ExternalGateway;
import com.tcc.gateway.domain.Payment;
import com.tcc.gateway.domain.PaymentRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ProcessPaymentInteractorTest {

    @Mock
    private PaymentRepository repository;

    @Mock
    private ExternalGateway externalGateway;

    private ProcessPaymentInteractor interactor;

    @BeforeEach
    void setUp() {
        interactor = new ProcessPaymentInteractor(repository, externalGateway);
    }

    @Test
    void shouldProcessPaymentWithSuccess() {
        var request = new Payment(null, new BigDecimal("100.00"), "1234567890123", null, null, null);
        var externalResponse = new ExternalGateway.PaymentResponse("ext_123", true);

        when(externalGateway.process(any())).thenReturn(externalResponse);
        when(repository.save(any())).thenAnswer(i -> i.getArguments()[0]);

        Payment result = interactor.execute(request);

        assertNotNull(result.id());
        assertEquals("APPROVED", result.status());
        assertEquals("ext_123", result.externalId());

        ArgumentCaptor<Payment> captor = ArgumentCaptor.forClass(Payment.class);
        verify(repository, times(2)).save(captor.capture());
        assertEquals("PENDING",  captor.getAllValues().get(0).status());
        assertEquals("APPROVED", captor.getAllValues().get(1).status());
    }

    @Test
    void shouldProcessPaymentWithRejection() {
        var request = new Payment(null, new BigDecimal("100.00"), "1234567890123", null, null, null);
        var externalResponse = new ExternalGateway.PaymentResponse("ext_456", false);

        when(externalGateway.process(any())).thenReturn(externalResponse);
        when(repository.save(any())).thenAnswer(i -> i.getArguments()[0]);

        Payment result = interactor.execute(request);

        assertEquals("REJECTED", result.status());
        assertEquals("ext_456", result.externalId());
    }

    @Test
    void shouldThrowExceptionWhenInitialSaveFails_AndNotCallGateway() {
        var request = new Payment(null, new BigDecimal("100.00"), "1234567890123", null, null, null);

        when(repository.save(any())).thenThrow(new RuntimeException("Database error"));

        RuntimeException ex = assertThrows(RuntimeException.class, () -> interactor.execute(request));
        assertEquals("Database error", ex.getMessage());
        verify(externalGateway, never()).process(any());
    }

    @Test
    void shouldPropagateExceptionWhenGatewayFails_AndKeepStatusPending() {
        var request = new Payment(null, new BigDecimal("100.00"), "1234567890123", null, null, null);

        when(repository.save(any())).thenAnswer(i -> i.getArguments()[0]);
        when(externalGateway.process(any())).thenThrow(new RuntimeException("Gateway Timeout"));

        RuntimeException ex = assertThrows(RuntimeException.class, () -> interactor.execute(request));
        assertEquals("Gateway Timeout", ex.getMessage());
        verify(repository, times(1)).save(any());
    }
}
