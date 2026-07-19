# Refactor Notes — Toward `platform_core`

This chapter seeds a long-term layout for the evolving AI platform.

## Mapping prior chapters → core

| Prior chapter | Concept | Future / current home |
|---------------|---------|------------------------|
| 001 | `Settings`, logging bootstrap | `platform_core.config`, process logging in CLI |
| 002 | Stack registry / layer map | Keep as architecture atlas; core implements seams the atlas describes |
| 004 | Git validators | Future `platform_core.devtools` (leave in chapter-004 until shared need) |
| 005 | `HttpClient`, retry, rate limit | Transport for future adapters; pure retry decisions mirrored in `policies.py` |
| 006 | Async HTTP | Async variants of adapters later; ports can stay sync or grow async ports carefully |

## Dependency rule

```text
platform_core.domain
platform_core.ports
platform_core.services      # depends on ports only
platform_core.adapters.*   # implements ports; may use httpx later
platform_core.factories    # composition root
```

Adapters depend **inward**. Domain never imports httpx/vendor SDKs.

## Promotion playbook

1. When Chapter 8 needs a real provider, implement `adapters/openai.py` as `LLMPort`.
2. Wire it in `build_llm()` only.
3. Keep `CompleteText` unchanged.
4. Add contract tests shared by mock + real adapters (mock transport).

## Non-goals for Chapter 7

- Full agent loop
- Production database
- Framework integrations

Those arrive later **on top of** these ports.
