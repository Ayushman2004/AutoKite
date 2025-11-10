import logging
from typing import List
from datetime import datetime
from imap_tools import MailBox, AND
from bs4 import BeautifulSoup

from models import EmailMessage
from config import EmailConfig

logger = logging.getLogger(__name__)


class EmailClient:
    
    def __init__(self, config: EmailConfig):
        self.config = config
        self._mailbox = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def connect(self):
        try:
            self._mailbox = MailBox(self.config.imap_server)
            self._mailbox.login(self.config.email, self.config.password)
            logger.info(f"Connected to {self.config.email}")
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            raise ConnectionError(f"Cannot connect to Gmail: {str(e)}")
    
    def disconnect(self):
        if self._mailbox:
            try:
                self._mailbox.logout()
                logger.info("Disconnected from Gmail")
            except Exception as e:
                logger.warning(f"Error during disconnect: {str(e)}")
    
    @staticmethod
    def _clean_html(html_content: str) -> str:
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def fetch_unread_emails(self, limit: int = 50) -> List[EmailMessage]:
        if not self._mailbox:
            raise RuntimeError("Not connected to email server")
        
        emails = []
        
        try:
            #fetch unread mails
            messages = self._mailbox.fetch(
                criteria=AND(seen=False),
                mark_seen=False,  
                limit=limit,
                reverse=True  
            )
            
            for msg in messages:
                try:
                    body = msg.text or self._clean_html(msg.html) or ""
                    
                    email = EmailMessage(
                        uid=msg.uid,
                        subject=msg.subject or "(No Subject)",
                        sender=msg.from_ or "Unknown",
                        date=msg.date or datetime.now(),
                        body=body,
                        snippet=""  
                    )
                    
                    emails.append(email)
                    
                except Exception as e:
                    logger.warning(f"Error parsing email {msg.uid}: {str(e)}")
                    continue
            
            logger.info(f"Fetched {len(emails)} unread emails")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise RuntimeError(f"Failed to fetch emails: {str(e)}")
    
    def get_unread_count(self) -> int:
        if not self._mailbox:
            raise RuntimeError("Not connected to email server")
        
        try:
            messages = self._mailbox.fetch(
                criteria=AND(seen=False),
                mark_seen=False
            )
            return len(list(messages))
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0