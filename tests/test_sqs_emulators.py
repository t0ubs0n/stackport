"""Opt-in SQS round trips against running emulators, never real AWS.

Set STACKPORT_TEST_SQS_ENDPOINTS to a JSON object mapping emulator names to
HTTP endpoint URLs. Each case creates and deletes its own temporary queue.
"""

import json
import os
import time
import uuid
from urllib.parse import urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.aws_client import get_client
from backend.routes.common import EndpointInfo, get_endpoint_info
from backend.routes.sqs import router


ENDPOINTS = json.loads(os.environ.get("STACKPORT_TEST_SQS_ENDPOINTS", "{}"))


@pytest.mark.skipif(not ENDPOINTS, reason="Set STACKPORT_TEST_SQS_ENDPOINTS to run emulator checks")
@pytest.mark.parametrize("emulator,endpoint", list(ENDPOINTS.items()))
@pytest.mark.parametrize("fifo", [False, True], ids=["standard", "fifo"])
def test_message_attributes_round_trip(emulator, endpoint, fifo):
    parsed = urlparse(endpoint)
    assert parsed.scheme in {"http", "https"} and parsed.hostname
    assert not parsed.hostname.endswith(".amazonaws.com"), "Only emulator endpoints are allowed"
    ep = EndpointInfo(
        url=endpoint,
        region="us-east-1",
        auth_type="credentials",
        auth_access_key_id="test",
        auth_secret_access_key="test",
    )
    sqs = get_client("sqs", **ep.client_kwargs())
    name = f"stackport-attributes-{uuid.uuid4().hex}" + (".fifo" if fifo else "")
    queue_url = sqs.create_queue(
        QueueName=name,
        Attributes={"FifoQueue": "true", "ContentBasedDeduplication": "true"} if fifo else {},
    )["QueueUrl"]
    app = FastAPI()
    app.include_router(router, prefix="/api/sqs")
    app.dependency_overrides[get_endpoint_info] = lambda: ep
    attributes = {
        "source": {"dataType": "String", "stringValue": "stackport"},
        "count": {"dataType": "Number", "stringValue": "42"},
        "payload": {"dataType": "Binary", "binaryValue": "AP+A"},
        "customString": {"dataType": "String.source", "stringValue": "console"},
        "customNumber": {"dataType": "Number.int", "stringValue": "7"},
        "customBinary": {"dataType": "Binary.raw", "binaryValue": "aGVsbG8="},
        **{f"extra{i}": {"dataType": "String", "stringValue": str(i)} for i in range(4)},
    }
    try:
        with TestClient(app) as client:
            request = {"messageBody": "attribute round trip", "messageAttributes": attributes}
            if fifo:
                request["messageGroupId"] = "compatibility"
                request["messageDeduplicationId"] = uuid.uuid4().hex
            sent = client.post(f"/api/sqs/queues/{name}/messages", json=request)
            assert sent.status_code == 200, f"{emulator}: {sent.text}"
            messages = []
            for _ in range(20):
                received = client.get(f"/api/sqs/queues/{name}/messages")
                assert received.status_code == 200, f"{emulator}: {received.text}"
                messages = received.json()["messages"]
                if messages:
                    break
                time.sleep(0.25)
            assert len(messages) == 1, f"{emulator}: message not received"
            assert messages[0]["body"] == request["messageBody"]
            assert messages[0]["messageId"] == sent.json()["messageId"]
            assert messages[0]["messageAttributes"] == {
                key: {
                    "DataType": value["dataType"],
                    **({"BinaryValue": value["binaryValue"]} if "binaryValue" in value
                       else {"StringValue": value["stringValue"]}),
                }
                for key, value in attributes.items()
            }, f"{emulator}: attributes changed during round trip"
    finally:
        sqs.delete_queue(QueueUrl=queue_url)
