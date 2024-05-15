from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Optional

from flask import abort
from marshmallow import EXCLUDE
from marshmallow_dataclass import class_schema


@dataclass
class Webhook:
    message: 'Message'
    rule: 'Rule'
    Timestamp: str

    @classmethod
    def from_json(cls, json: Optional[dict]) -> 'Webhook':
        try:
            webhook_schema = WebhookSchema()
            return webhook_schema.load(json, unknown=EXCLUDE)
        except Exception as ex:
            abort(HTTPStatus.BAD_REQUEST, str(ex))


@dataclass
class Message:
    object_id: str
    ref: str
    object_type: str
    transaction: 'Transaction'
    state: dict[str, 'Attribute']
    subscription_id: int
    message_id: str
    project: 'Project'
    id: str
    detail_link: str
    message_version: int
    changes: dict[str, 'Change']
    action: str


@dataclass
class Transaction:
    trace_id: str
    timestamp: int
    user: 'User'
    message_id: str
    parent_span_id: str
    span_id: str
    message_lag: int


@dataclass
class User:
    uuid: str
    username: str
    email: str


@dataclass
class Attribute:
    value: Any
    type: str
    name: str
    display_name: str
    ref: Optional[str]


@dataclass
class Project:
    uuid: str
    name: str


@dataclass
class Change:
    value: Optional[Any]
    old_value: Optional[Any]
    added: Optional[list['Object']]
    removed: Optional[list['Object']]
    type: str
    name: str
    display_name: str
    ref: Optional[str]


@dataclass
class Object:
    name: str
    formatted_id: Optional[str]
    ref: Optional[str]
    detail_link: Optional[str]
    id: str
    object_type: str


@dataclass
class Rule:
    LastUpdateDate: str
    Expressions: list['Expression']
    SubscriptionID: int
    LastWebhookResponseTime: Optional[int]
    ObjectTypes: list[str]
    LastSuccess: Optional[str]
    LastStatus: Optional[int]
    OwnerID: str
    FireCount: Optional[int]
    TargetUrl: str
    CreatedBy: Optional[str]
    Disabled: bool
    ErrorCount: Optional[int]
    Name: str
    LastFailure: Optional[str]
    AppName: str
    ObjectUUID: str
    CreationDate: str
    AppUrl: str
    _objectVersion: Optional[int]
    _type: Optional[str]


@dataclass
class Expression:
    AttributeID: Optional[str]
    AttributeName: Optional[str]
    Operator: str
    Value: Any


WebhookSchema = class_schema(Webhook)
MessageSchema = class_schema(Message)
TransactionSchema = class_schema(Transaction)
UserSchema = class_schema(User)
AttributeSchema = class_schema(Attribute)
ProjectSchema = class_schema(Project)
ChangeSchema = class_schema(Change)
ObjectSchema = class_schema(Object)
RuleSchema = class_schema(Rule)
ExpressionSchema = class_schema(Expression)
