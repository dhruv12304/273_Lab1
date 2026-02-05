from flask import Flask, request, jsonify
import time
import logging
import requests
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = Flask(__name__)

SERVICE_A = "http://127.0.0.1:8080"
CORRELATION_HEADER = "X-Correlation-ID"

def get_correlation_id():
    return request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))

@app.get("/health")
def health():
    return jsonify(status="ok")

@app.get("/call-echo")
def call_echo():
    start = time.time()
    correlation_id = get_correlation_id()
    msg = request.args.get("msg", "")
    headers = {CORRELATION_HEADER: correlation_id}
    try:
        r = requests.get(f"{SERVICE_A}/echo", params={"msg": msg}, headers=headers, timeout=1.0)
        r.raise_for_status()
        data = r.json()
        logging.info(f'service=B endpoint=/call-echo correlation_id={correlation_id} status=ok latency_ms={int((time.time()-start)*1000)}')
        return jsonify(service_b="ok", service_a=data, correlation_id=correlation_id)
    except Exception as e:
        logging.info(f'service=B endpoint=/call-echo correlation_id={correlation_id} status=error error="{str(e)}" latency_ms={int((time.time()-start)*1000)}')
        return jsonify(service_b="ok", service_a="unavailable", error=str(e), correlation_id=correlation_id), 503

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081)
