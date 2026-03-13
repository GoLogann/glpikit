"""Pydantic schemas for agent tool inputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTicketInput(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3)
    category_id: int | None = None
    requester_email: str | None = None
    urgency: int | None = None
    impact: int | None = None
    priority: int | None = None


class SearchTicketInput(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=100)


class AddFollowupInput(BaseModel):
    ticket_id: int
    content: str = Field(min_length=1)


class GetTicketInput(BaseModel):
    ticket_id: int = Field(gt=0)


class UpdateTicketInput(BaseModel):
    ticket_id: int = Field(gt=0)
    title: str | None = None
    description: str | None = None
    urgency: int | None = None
    impact: int | None = None
    priority: int | None = None
    category_id: int | None = None


class SearchUserInput(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=100)


class GetEntityInput(BaseModel):
    entity_id: int = Field(gt=0)
