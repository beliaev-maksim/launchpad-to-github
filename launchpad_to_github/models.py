from datetime import datetime

from lazr.restfulclient.resource import Collection
from lazr.restfulclient.resource import Entry
from pydantic import BaseModel


class Attachment(BaseModel):
    name: str
    url: str


class Message(BaseModel):
    author: str
    content: str


class Bug(BaseModel):
    assignee_link: str | None
    attachments: list[Attachment]
    attachments_collection: Collection
    date_created: datetime
    description: str
    heat: int
    importance: str
    messages: list[Message]
    owner_link: str
    security_related: bool
    status: str
    tags: list
    title: str
    web_link: str
    original_task: Entry
    original_bug: Entry

    class Config:
        arbitrary_types_allowed = True
