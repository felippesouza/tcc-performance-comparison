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
import java.util.Optional;

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
        // Arrange
        var request = new Payment(null, new BigDecimal("100.00"), "1234-5678", null, null, null);
        var externalResponse = new ExternalGateway.PaymentResponse("ext_123", true);

        when(externalGateway.process(any())).thenReturn(externalResponse);
        when(repository.save(any())).thenAnswer(i -> i.getArguments()[0]);

        // Act
        Payment result = interactor.execute(request);

        // Assert
        assertNotNull(result.id());
        assertEquals("APPROVED", result.status());
        assertEquals("ext_123", result.externalId());

        // Verificando se salvou duas vezes (PENDING e depois APPROVED)
        verify(repository, times(2)).save(any());
        
        // Capturando o segundo save para validar o status final
        ArgumentCaptor<Payment> paymentCaptor = ArgumentCaptor.forClass(Payment.class);
        verify(repository, times(2)).save(paymentCaptor.capture());
        
        assertEquals("PENDING", paymentCaptor.getAllValues().get(0).status());
        assertEquals("APPROVED", paymentCaptor.getAllValues().get(1).status());
    }

    @Test
    void shouldProcessPaymentWithRejection() {
        // Arrange
        var request = new Payment(null, new BigDecimal("100.00"), "1234-5678", null, null, null);
        var externalResponse = new ExternalGateway.PaymentResponse("ext_456", false);

        when(externalGateway.process(any())).thenReturn(externalResponse);
        when(repository.save(any())).thenAnswer(i -> i.getArguments()[0]);

        // Act
        Payment result = interactor.execute(request);

        // Assert
        assertEquals("REJECTED", result.status());
        assertEquals("ext_456", result.externalId());
    }

    @Test
    void shouldThrowExceptionWhenInitialSaveFails_AndNotCallGateway() {
        // Arrange
        var request = new Payment(null, new BigDecimal("100.00"), "1234-5678", null, null, null);
        
        when(repository.save(any())).thenThrow(new RuntimeException("Database error"));

        // Act & Assert
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            interactor.execute(request);
        });

        assertEquals("Database error", exception.getMessage());
        
        // Garante que se o banco falhou, NÃO cobramos o cartão do cliente na API externa
        verify(externalGateway, never()).process(any());
    }

    @Test
    void shouldPropagateExceptionWhenGatewayFails_AndKeepStatusPending() {
        // Arrange
        var request = new Payment(null, new BigDecimal("100.00"), "1234-5678", null, null, null);
        
        // Simula sucesso no primeiro save (PENDING) e falha no gateway
        when(repository.save(any())).thenAnswer(i -> i.getArguments()[0]);
        when(externalGateway.process(any())).thenThrow(new RuntimeException("Gateway Timeout"));

        // Act & Assert
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            interactor.execute(request);
        });

        assertEquals("Gateway Timeout", exception.getMessage());

        // Garante que o repositório foi chamado apenas 1 vez (para o PENDING) e não atualizou para aprovado/rejeitado
        verify(repository, times(1)).save(any());
    }
}
