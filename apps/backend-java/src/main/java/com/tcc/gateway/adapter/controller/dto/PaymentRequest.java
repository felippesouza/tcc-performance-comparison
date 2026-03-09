package com.tcc.gateway.adapter.controller.dto;

import java.math.BigDecimal;

public record PaymentRequest(BigDecimal amount, String cardNumber) {}
