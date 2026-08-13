# Distributed-Rate-Limiter

A high-throughput, low-latency API Gateway rate limiter built with **FastAPI**, **Redis**, and **Lua**, fully containerized using **Docker Compose**. 

Implements the **Token Bucket Algorithm with Lazy Refill**, guaranteeing $O(1)$ memory complexity and thread-safe atomic execution under concurrent heavy traffic.

---

## 🏗️ Architecture & Request Flow

When an HTTP request hits the gateway, client identification, token calculation, and rate enforcement execute in sub-millisecond time:

```text
 Client (curl / App)
         │
         │  1. HTTP GET /api/v1/resource
         ▼
 ┌─────────────────────────────────────────────────────────┐
 │               FastAPI Gateway Container                 │
 │  • Extracts Client IP                                   │
 │  • Grabs System Epoch Timestamp                         │
 └───────────────────────────┬─────────────────────────────┘
                             │
                             │  2. EVALSHA (Atomic Lua Execution)
                             ▼
 ┌─────────────────────────────────────────────────────────┐
 │                     Redis Container                     │
 │  • Computes Lazy Token Refill based on elapsed time     │
 │  • Decrements Token (if available)                      │
 │  • Returns [Allowed (1/0), Remaining Tokens]            │
 └───────────────────────────┬─────────────────────────────┘
                             │
                             │  3. Returns HTTP Response
                             ▼
             ┌───────────────────────────────┐
             │ 200 OK (Access Granted)       │
             │   OR                          │
             │ 429 Too Many Requests         │
             └───────────────────────────────┘

Prerequisites and how to run:

1. Docker and Docker Compose installed.
2. Clone & Spin Up Stack with docker compose build and docker compose up
3. Test Rate Limiting via curl
curl -i http://127.0.0.1:8000/api/v1/resource
4. You will recieve either a HTTP 200 or 429