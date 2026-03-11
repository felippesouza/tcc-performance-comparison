package com.tcc.gateway.adapter.cache;

import java.util.Optional;

public interface IdempotencyCache {
    Optional<String> get(String key);
    void put(String key, String value);
}
