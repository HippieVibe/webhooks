import hashlib
import hmac
import os

from flask import Flask, abort, request
from flask.typing import ResponseReturnValue

app = Flask(__name__)

GITHUB_WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]


@app.route("/webhook", methods=["POST"])
def github_webhook() -> ResponseReturnValue:
    # Extract signature header
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature or not signature.startswith("sha256="):
        abort(400, "X-Hub-Signature-256 required")

    # Create local hash of payload
    digest = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        request.data,
        hashlib.sha256,
    ).hexdigest()

    # Verify signature
    if not hmac.compare_digest(signature, "sha256=" + digest):
        abort(400, "Invalid signature")

    # The signature was fine, let's parse the data
    request_data = request.get_json()

    print(request_data)

    return "done"


if __name__ == "__main__":
    app.run()
