"""Pydantic schemas for SQS API requests."""

import base64
import binascii
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class RedrivePolicy(BaseModel):
    """Redrive policy referencing an existing dead-letter queue."""

    dead_letter_target_arn: str = Field(alias="deadLetterTargetArn")
    max_receive_count: int = Field(alias="maxReceiveCount", ge=1)

    model_config = {"populate_by_name": True}


class CreateQueueRequest(BaseModel):
    queue_name: str = Field(alias="queueName", min_length=1)
    queue_type: Literal["Standard", "FIFO"] = Field("Standard", alias="queueType")
    content_based_deduplication: bool = Field(False, alias="contentBasedDeduplication")
    visibility_timeout: int | None = Field(None, alias="visibilityTimeout", ge=0, le=43200)
    message_retention_period: int | None = Field(None, alias="messageRetentionPeriod")
    delay_seconds: int | None = Field(None, alias="delaySeconds", ge=0, le=900)
    maximum_message_size: int | None = Field(None, alias="maximumMessageSize")
    receive_message_wait_time: int | None = Field(None, alias="receiveMessageWaitTime", ge=0, le=20)
    dlq_enabled: bool = Field(False, alias="dlqEnabled")
    max_receive_count: int = Field(5, alias="maxReceiveCount", ge=1)
    redrive_policy: RedrivePolicy | None = Field(None, alias="redrivePolicy")
    kms_master_key_id: str | None = Field(None, alias="kmsMasterKeyId")
    sqs_managed_sse_enabled: bool = Field(True, alias="sqsManagedSseEnabled")
    tags: dict[str, str] | None = None

    model_config = {"populate_by_name": True}


class MessageAttribute(BaseModel):
    data_type: str = Field("String", alias="dataType", max_length=256, pattern=r"^(String|Number|Binary)(\..+)?$")
    string_value: str | None = Field(None, alias="stringValue", min_length=1)
    binary_value: str | None = Field(None, alias="binaryValue", min_length=1)

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_value(self) -> "MessageAttribute":
        base_type = self.data_type.split(".", 1)[0]
        if base_type == "Binary":
            if self.binary_value is None or self.string_value is not None:
                raise ValueError("Binary attributes require binaryValue, not stringValue")
            try:
                base64.b64decode(self.binary_value, validate=True)
            except (ValueError, binascii.Error):
                raise ValueError("binaryValue must be valid Base64") from None
        else:
            if self.string_value is None or self.binary_value is not None:
                raise ValueError("String and Number attributes require stringValue, not binaryValue")
            if base_type == "Number" and not re.fullmatch(
                r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", self.string_value
            ):
                raise ValueError("Number attributes require a numeric value")
        return self


class SendMessageRequest(BaseModel):
    message_body: str = Field(alias="messageBody", min_length=1)
    delay_seconds: int | None = Field(None, alias="delaySeconds", ge=0, le=900)
    message_attributes: dict[str, MessageAttribute] | None = Field(None, alias="messageAttributes", max_length=10)
    message_deduplication_id: str | None = Field(None, alias="messageDeduplicationId")
    message_group_id: str | None = Field(None, alias="messageGroupId")

    model_config = {"populate_by_name": True}

    @field_validator("message_attributes")
    @classmethod
    def validate_attribute_names(cls, attributes: dict[str, MessageAttribute] | None) -> dict[str, MessageAttribute] | None:
        for name in attributes or {}:
            if (
                not re.fullmatch(r"[a-zA-Z0-9_.-]{1,256}", name)
                or name.lower().startswith(("aws.", "amazon."))
                or name.startswith(".")
                or name.endswith(".")
                or ".." in name
            ):
                raise ValueError(f"Invalid message attribute name: {name}")
        return attributes


class BatchSendEntry(BaseModel):
    id: str = Field(min_length=1)
    message_body: str = Field(alias="messageBody", min_length=1)
    delay_seconds: int | None = Field(None, alias="delaySeconds", ge=0, le=900)
    message_deduplication_id: str | None = Field(None, alias="messageDeduplicationId")
    message_group_id: str | None = Field(None, alias="messageGroupId")

    model_config = {"populate_by_name": True}


class BatchSendRequest(BaseModel):
    entries: list[BatchSendEntry] = Field(min_length=1, max_length=10)


class BatchDeleteRequest(BaseModel):
    receipt_handles: list[str] = Field(alias="receiptHandles", min_length=1, max_length=10)

    model_config = {"populate_by_name": True}


class UpdateAttributesRequest(BaseModel):
    visibility_timeout: int | None = Field(None, alias="visibilityTimeout", ge=0, le=43200)
    message_retention_period: int | None = Field(None, alias="messageRetentionPeriod")
    delay_seconds: int | None = Field(None, alias="delaySeconds", ge=0, le=900)
    maximum_message_size: int | None = Field(None, alias="maximumMessageSize")
    receive_message_wait_time: int | None = Field(None, alias="receiveMessageWaitTime", ge=0, le=20)

    model_config = {"populate_by_name": True}


class UpdateRedrivePolicyRequest(BaseModel):
    dead_letter_target_arn: str = Field(alias="deadLetterTargetArn", min_length=1)
    max_receive_count: int = Field(alias="maxReceiveCount", ge=1)

    model_config = {"populate_by_name": True}
