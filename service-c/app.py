from flask import Flask, request, jsonify
import time
import logging
import requests
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = Flask(__name__)

SERVICE_B = "http://127.0.0.1:8081"
CORRELATION_HEADER = "X-Correlation-ID"

def get_or_create_correlation_id():
    """Get correlation ID from header or generate a new one."""
    return request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))

@app.get("/health")
def health():
    return jsonify(status="ok")

@app.get("/process")
def process():
    """
    Entry point for the service chain.
    Service C -> Service B -> Service A
    Generates correlation ID and propagates through the chain.
    """
    start = time.time()
    correlation_id = get_or_create_correlation_id()
    msg = request.args.get("msg", "")
    headers = {CORRELATION_HEADER: correlation_id}

    try:
        r = requests.get(f"{SERVICE_B}/call-echo", params={"msg": msg}, headers=headers, timeout=2.0)
        r.raise_for_status()
        data = r.json()
        logging.info(f'service=C endpoint=/process correlation_id={correlation_id} status=ok latency_ms={int((time.time()-start)*1000)}')
        return jsonify(service_c="ok", downstream=data, correlation_id=correlation_id)
    except Exception as e:
        logging.info(f'service=C endpoint=/process correlation_id={correlation_id} status=error error="{str(e)}" latency_ms={int((time.time()-start)*1000)}')
        return jsonify(service_c="ok", downstream="unavailable", error=str(e), correlation_id=correlation_id), 503

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8082)
