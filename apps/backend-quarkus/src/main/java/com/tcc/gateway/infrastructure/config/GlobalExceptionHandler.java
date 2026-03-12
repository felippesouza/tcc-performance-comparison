// ============================================================
// TCC — Comparação de Performance: Java 25 vs Go 1.25 vs Quarkus Native
// Autor:       Felippe Gustavo de Souza e Silva
// Instituição: USP ESALQ — Engenharia de Software
// Orientador:  Prof. Marcos Jardel Henriques
// Ano:         2026
// Repositório: https://github.com/felippesouza/tcc-performance-comparison
// ============================================================
package com.tcc.gateway.infrastructure.config;

import com.tcc.gateway.domain.DomainException;
import io.quarkus.runtime.annotations.RegisterForReflection;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;
import org.jboss.logging.Logger;

import java.time.Instant;

@Provider
public class GlobalExceptionHandler implements ExceptionMapper<Exception> {

    private static final Logger LOG = Logger.getLogger(GlobalExceptionHandler.class);

    @RegisterForReflection
    public record ErrorResponse(String message, String timestamp) {}

    @Override
    public Response toResponse(Exception exception) {
        if (exception instanceof DomainException de) {
            return Response.status(Response.Status.BAD_REQUEST)
                .entity(new ErrorResponse(de.getMessage(), Instant.now().toString()))
                .build();
        }
        LOG.errorf(exception, "Unexpected error: %s", exception.getMessage());
        return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
            .entity(new ErrorResponse("Internal server error", Instant.now().toString()))
            .build();
    }
}
