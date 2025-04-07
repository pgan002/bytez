from typing import Literal

from pydantic import BaseModel, validator, Field, ValidationError


class ContentBlock(BaseModel):
    type: Literal[
        'paragraph', 'image', 'table', 'formula', 'code', 'reference',
        'header', 'footer', 'print_notice', 'toc', 'authors'
    ]
    content: str = ''
    caption: str | None = None  # For image/table/code


class DocumentSection(BaseModel):
    type: Literal['section']
    title: str
    level: int = Field(ge=1, le=4)
    content: list[ContentBlock]
    sections: list['DocumentSection'] = Field(default_factory=list)
    continued: bool = False


class StructuredDocument(BaseModel):
    title: str
    sections: list[DocumentSection]

    @validator('sections')
    def check_continuations(cls, v):
        for i, section in enumerate(v):
            if i == 0 and section.continued:
                raise ValidationError('First section cannot be continuation')
        return v
