# Python HTTP Track - Distributed Services Lab

## Architecture

This lab implements a **3-service chain** with **distributed request tracing**:

```
Client → Service C (8082) → Service B (8081) → Service A (8080)
              │                    │                  │
              └────────────────────┴──────────────────┘
                    X-Correlation-ID propagated
```

### Key Features
- **Service Chain**: Three independent services communicating via HTTP
- **Request Tracing**: Correlation IDs (`X-Correlation-ID`) propagate through the entire chain
- **Failure Handling**: Each service handles downstream failures gracefully
- **Structured Logging**: All logs include correlation ID for distributed debugging

## How to Run Locally

### 1. Clone and Setup (one-time)
```bash
git clone https://github.com/dhruv12304/273_Lab1.git
cd 273_Lab1
python3 -m venv venv
source venv/bin/activate
pip install flask requests
```

### 2. Start Service A (Terminal 1)
```bash
source venv/bin/activate
python service-a/app.py
```
Service A runs on http://127.0.0.1:8080 - Echo API (end of chain)

![Service A Running](Screenshots/Service_A_running.png)

### 3. Start Service B (Terminal 2)
```bash
source venv/bin/activate
python service-b/app.py
```
Service B runs on http://127.0.0.1:8081 - Middleware (calls Service A)

![Service B Running](Screenshots/Service_B_running.png)

### 4. Start Service C (Terminal 3)
```bash
source venv/bin/activate
python service-c/app.py
```
Service C runs on http://127.0.0.1:8082 - Entry point (calls Service B)

![Service C Running](Screenshots/Service_C_running.png)

### 5. Test the Full Chain
```bash
curl "http://127.0.0.1:8082/process?msg=hello"
```

### 6. Test with Custom Correlation ID
```bash
curl -H "X-Correlation-ID: my-trace-123" "http://127.0.0.1:8082/process?msg=hello"
```

---

## Request Tracing with Correlation IDs

Each request through the service chain is tracked with a unique `X-Correlation-ID`:

1. **Generation**: Service C generates a UUID if no correlation ID is provided
2. **Propagation**: The ID is passed via HTTP header to each downstream service
3. **Logging**: Every service logs the correlation ID for distributed debugging

### Benefits of Correlation IDs

| Benefit | Description |
|---------|-------------|
| **End-to-End Tracing** | Track a single request as it flows through all three services |
| **Faster Debugging** | When an error occurs, search logs by correlation ID to see the complete request journey |
| **Performance Analysis** | Measure latency at each service hop for the same request |
| **Root Cause Analysis** | Quickly identify which service in the chain caused a failure |

### Custom Correlation ID Use Cases

Using a custom correlation ID (via `X-Correlation-ID` header) is useful when:

- **External System Integration**: Pass an ID from an upstream system (e.g., frontend transaction ID) to trace requests across system boundaries
- **Testing & QA**: Use predictable IDs like `my-trace-123` to easily find specific test requests in logs
- **Customer Support**: Generate a ticket-based ID to trace a specific customer's request through the system
- **Load Testing**: Tag requests with batch IDs to analyze performance of specific test runs

---

## Test Results

### Success Case: Auto-Generated Correlation ID

When no correlation ID is provided, Service C generates a UUID automatically.

**Curl Response:**

![Curl Response - Auto Generated ID](Screenshots/Curl_test_response_without_correlationID.png)

**Service Logs (note the same correlation ID `75e743ab-699d-41c4-b136-02f62797a8df` across all services):**

| Service | Log |
|---------|-----|
| Service C | ![Service C Log](Screenshots/Curl_test_Service_C_log_without_custom_correlationID.png) |
| Service B | ![Service B Log](Screenshots/Curl_test_Service_B_log_without_custom_correlationID.png) |
| Service A | ![Service A Log](Screenshots/Curl_test_Service_A_log_without_custom_correlationID.png) |

---

### Success Case: Custom Correlation ID

When a custom correlation ID is provided via the `X-Correlation-ID` header, it propagates through all services.

```bash
curl -H "X-Correlation-ID: my-trace-123" "http://127.0.0.1:8082/process?msg=hello"
```

**Curl Response:**

![Curl Response - Custom ID](Screenshots/Curl_test_response_with_custom_correlationID.png)

**Service Logs (note the custom correlation ID `my-trace-123` across all services):**

| Service | Log |
|---------|-----|
| Service C | ![Service C Log - Custom ID](Screenshots/Curl_test_Service_C_log_with_custom_correlationID.png) |
| Service B | ![Service B Log - Custom ID](Screenshots/Curl_test_Service_B_log_with_custom_correlationID.png) |
| Service A | ![Service A Log - Custom ID](Screenshots/Curl_test_Service_A_log_with_custom_correlationID.png) |

---

### Failure Case: Service A Stopped (Auto-Generated ID)

Stop Service A (Ctrl+C), then rerun the curl command:

![Service A Stopped](Screenshots/Service_A_stopped.png)

**Error Response (HTTP 503):**

![Error Response](Screenshots/Curl_test_response_after_Service_A_stopped.png)

**Service Logs showing error propagation:**

| Service | Log |
|---------|-----|
| Service C | ![Service C Error Log](Screenshots/Service_C_logs_after_Service_A_down.png) |
| Service B | ![Service B Error Log](Screenshots/Service_B_logs_after_Service_A_down.png) |

---

### Failure Case: Service A Stopped (Custom ID)

Testing failure with a custom correlation ID makes it easy to trace the error path:

```bash
curl -H "X-Correlation-ID: my-trace-12304" "http://127.0.0.1:8082/process?msg=hello"
```

**Error Response:**

![Error Response - Custom ID](Screenshots/Curl_test_response_withCustomID_after_Service_A_stopped.png)

**Service Logs (correlation ID `my-trace-12304` visible in error logs):**

| Service | Log |
|---------|-----|
| Service C | ![Service C Error Log - Custom ID](Screenshots/Service_C_logs_after_Service_A_down_withCustomID.png) |
| Service B | ![Service B Error Log - Custom ID](Screenshots/Service_B_logs_after_Service_A_down_withCustomID.png) |

---

## Failure Scenarios Explained

### What happens if Service A is down?

When Service A is stopped or unreachable:

1. **Service B** attempts to connect to Service A at `localhost:8080`
2. The connection is **refused** (Service A process not running)
3. Service B catches the `ConnectionError` exception
4. Service B logs the error with `status=error` and the correlation ID
5. Service B returns **HTTP 503** (Service Unavailable) with error details
6. **Service C** receives the 503 from Service B
7. Service C logs its own error and returns **HTTP 503** to the client

The client receives a clear error response indicating the downstream service is unavailable, while Service B and C remain healthy and can handle other requests.

### What happens on timeout?

Each service has a configured timeout to prevent cascading delays:

- **Service B**: 1 second timeout when calling Service A
- **Service C**: 2 second timeout when calling Service B

If Service A becomes slow (e.g., stuck in a long operation):

1. Service B waits up to **1 second** for a response
2. If no response, a `ReadTimeout` exception is raised
3. Service B logs the timeout error and returns **HTTP 503**
4. The request fails fast instead of hanging indefinitely

This prevents a slow downstream service from blocking all upstream services (cascading failure).

### How to debug using the logs?

The structured logs make debugging straightforward:

1. **Find the correlation ID** from the error response or client logs
2. **Search all service logs** for that correlation ID:
   ```bash
   grep "correlation_id=my-trace-123" service-*.log
   ```
3. **Trace the request path**:
   - Check Service C log: Did it receive the request?
   - Check Service B log: Did it forward to Service A? What error occurred?
   - Check Service A log: Did it receive the request? (If missing, Service A was down)

4. **Identify the failure point**:
   - If Service A has no log entry → Service A was down/unreachable
   - If Service B shows `status=error` → Problem between B and A
   - If latency is high before error → Timeout occurred

**Example debug flow:**
```
# Client gets error with correlation_id=abc-123
# Check Service C log:
2024-01-15 10:30:00 service=C correlation_id=abc-123 status=error  ← C received request, got error from B

# Check Service B log:
2024-01-15 10:30:00 service=B correlation_id=abc-123 status=error error="Connection refused"  ← B couldn't reach A

# Check Service A log:
(no entry for abc-123)  ← Confirms A was down
```

---

## What Makes This Distributed?

This system is distributed because it consists of **three independent processes** (Service A, B, and C) that communicate over the network using HTTP, rather than sharing memory or running in the same process.

### Key Distributed Systems Concepts Demonstrated:

1. **Service Chain Architecture**: Requests flow through multiple services (C → B → A), simulating real-world microservices
2. **Network Communication**: Services communicate via HTTP on separate ports
3. **Independent Failure Modes**: Each service can fail independently; upstream services handle downstream failures gracefully
4. **Distributed Request Tracing**: Correlation IDs allow tracking a single request across all services for debugging
5. **Timeout Handling**: Service B (1s timeout) and Service C (2s timeout) prevent cascading delays
6. **Fault Tolerance**: When any downstream service fails, upstream services return meaningful 503 errors while remaining healthy themselves
