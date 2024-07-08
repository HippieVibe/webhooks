import hashlib
import hmac
import os
import shutil
import zipfile
from tempfile import TemporaryDirectory

import requests
from flask import Flask, abort, request
from flask.typing import ResponseReturnValue

app = Flask(__name__)

HTTP_TIMEOUT = 30
HTML_FOLDER_ROOT = os.environ["HTML_FOLDER_ROOT"]
WEBHOOK_ENDPOINT = os.environ["WEBHOOK_ENDPOINT"]
GITHUB_WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]
GITHUB_ACCESS_TOKEN = os.environ["GITHUB_ACCESS_TOKEN"]


@app.route(WEBHOOK_ENDPOINT, methods=["POST"])
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
        abort(400, "invalid signature")

    # The signature was fine, let's parse the data
    request_data = request.get_json()

    if request_data["action"] != "completed":
        return "not interested in this event"

    workflow = request_data["workflow_run"]

    if workflow["conclusion"] != "success":
        return "only interested in successful workflows"

    branch = workflow["head_branch"]
    artifacts_url = workflow["artifacts_url"]
    target_path = f"{HTML_FOLDER_ROOT}/{branch}"

    resp = requests.get(artifacts_url, timeout=HTTP_TIMEOUT)

    archive_download_url = None
    for artifact in resp.json()["artifacts"]:
        if artifact["name"] == "generated_html":
            archive_download_url = artifact["archive_download_url"]
            break

    if archive_download_url is None:
        abort(400, "generated HTML artifact not found")

    with TemporaryDirectory() as tmp_dir:
        generated_html_zip_path = f"{tmp_dir}/generated_html.zip"

        with requests.get(
            archive_download_url,
            headers={"Authorization": f"Bearer {GITHUB_ACCESS_TOKEN}"},
            timeout=HTTP_TIMEOUT,
            stream=True,
        ) as zip_stream:
            zip_stream.raise_for_status()

            with open(generated_html_zip_path, "wb") as zip_file:
                for chunk in zip_stream.iter_content(chunk_size=8192):
                    zip_file.write(chunk)

            with zipfile.ZipFile(generated_html_zip_path, "r") as zip_ref:
                if os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                zip_ref.extractall(target_path)

    return "done"


if __name__ == "__main__":
    app.run()
