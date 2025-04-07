from typing import Literal

from pydantic import BaseModel, validator, Field, ValidationError


class ContentBlock(BaseModel):
    type: Literal[
        'paragraph', 'image', 'table', 'formula', 'code', 'reference',
        'header', 'footer', 'print_notice', 'toc', 'authors'
    ]
    content: str = ''
    caption: str | None = None  # For image/table/code
    error: str | None = None


class DocumentSection(BaseModel):
    heading: str
    level: int = Field(ge=1, le=4)
    content: list[ContentBlock] | None
    sections: list['DocumentSection'] | None = Field(default_factory=list)
    continued: bool | None = None
    error: str | None = None

class StructuredDocument(BaseModel):
    title: str
    sections: list[DocumentSection]
    error: str | None = None

    @validator('sections')
    def check_continuations(cls, v):
        for i, section in enumerate(v):
            if i == 0 and section.continued:
                raise ValidationError('First section cannot be continuation')
        return v
