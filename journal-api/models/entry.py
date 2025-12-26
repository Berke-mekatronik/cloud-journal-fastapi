from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import uuid4

class EntryCreate(BaseModel):
    """Model for creating a new journal entry (user input)."""
    work: str = Field(
        max_length=256,
        description="What did you work on today?",
        json_schema_extra={"example": "FastAPI test "}
    )
    struggle: str = Field(
        max_length=256,
        description="What's one thing you struggled with today?",
        json_schema_extra={"example": "Hard"}
    )
    intention: str = Field(
        max_length=256,
        description="What will you study/work on tomorrow?",
        json_schema_extra={"example": "Testing"}
    )

class EntryUpdate(BaseModel):
    work: Optional[str] = Field(None, max_length=256)
    struggle: Optional[str] = Field(None, max_length=256)
    intention: Optional[str] = Field(None, max_length=256)

class Entry(BaseModel):
    # TODO: Add field validation rules
    # TODO: Add data sanitization methods
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the entry (UUID)."
    )
    work: str = Field(
        ...,
        max_length=256,
        description="What did you work on today?"
    )
    struggle: str = Field(
        ...,
        max_length=256,
        description="What’s one thing you struggled with today?"
    )
    intention: str = Field(
        ...,
        max_length=256,
        description="What will you study/work on tomorrow?"
    )
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the entry was created."
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the entry was last updated."
    )

    # TODO: Add schema versioning
    schema_version: str = Field(
        default="1.0",
        description="Version of the schema used to store this entry."
    )

    # TODO: Add custom validators
    @validator("work", "struggle", "intention")
    def no_prohibited_words(cls, value):
        prohibited = ["badword", "hack", "xxx"]
        if any(p in value.lower() for p in prohibited):
            raise ValueError("Inappropriate language is not allowed.")
        return value.strip()
