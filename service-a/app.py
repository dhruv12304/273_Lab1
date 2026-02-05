from flask import Flask, request, jsonify
import time
import logging
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = Flask(__name__)

CORRELATION_HEADER = "X-Correlation-ID"

def get_correlation_id():
    return request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))

@app.get("/health")
def health():
    return jsonify(status="ok")

@app.get("/echo")
def echo():
    start = time.time()
    correlation_id = get_correlation_id()
    msg = request.args.get("msg", "")
    resp = {"echo": msg, "correlation_id": correlation_id}
    logging.info(f'service=A endpoint=/echo correlation_id={correlation_id} status=ok latency_ms={int((time.time()-start)*1000)}')
    return jsonify(resp)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
