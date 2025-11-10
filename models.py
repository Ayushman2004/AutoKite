from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BucketCategory(str, Enum):
    UNCATEGORIZED = "uncategorized"
    

@dataclass
class EmailMessage:
    uid: str
    subject: str
    sender: str
    date: datetime
    body: str
    snippet: str  
    
    def __post_init__(self):
        if not self.snippet and self.body:
            self.snippet = self.body[:200].strip() + ('...' if len(self.body) > 200 else '')
    
    def to_dict(self) -> dict:
        return {
            'uid': self.uid,
            'subject': self.subject,
            'sender': self.sender,
            'date': self.date.isoformat(),
            'body': self.body,
            'snippet': self.snippet
        }


@dataclass
class Bucket:
    id: str
    title: str
    prompt: str
    created_at: datetime
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'prompt': self.prompt,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Bucket':
        return cls(
            id=data['id'],
            title=data['title'],
            prompt=data['prompt'],
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class CategorizedEmail:
    email: EmailMessage
    bucket_id: str
    bucket_title: str
    summary: str
    confidence: float 
    
    def to_dict(self) -> dict:
        return {
            'email': self.email.to_dict(),
            'bucket_id': self.bucket_id,
            'bucket_title': self.bucket_title,
            'summary': self.summary,
            'confidence': self.confidence
        }