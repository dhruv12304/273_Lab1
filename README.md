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

## What Makes This Distributed?

This system is distributed because it consists of **three independent processes** (Service A, B, and C) that communicate over the network using HTTP, rather than sharing memory or running in the same process.

### Key Distributed Systems Concepts Demonstrated:

1. **Service Chain Architecture**: Requests flow through multiple services (C → B → A), simulating real-world microservices
2. **Network Communication**: Services communicate via HTTP on separate ports
3. **Independent Failure Modes**: Each service can fail independently; upstream services handle downstream failures gracefully
4. **Distributed Request Tracing**: Correlation IDs allow tracking a single request across all services for debugging
5. **Timeout Handling**: Service B (1s timeout) and Service C (2s timeout) prevent cascading delays
6. **Fault Tolerance**: When any downstream service fails, upstream services return meaningful 503 errors while remaining healthy themselves
