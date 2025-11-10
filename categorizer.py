import logging
import json
from typing import List, Dict
import ollama

from models import EmailMessage, Bucket, CategorizedEmail
from config import OllamaConfig

logger = logging.getLogger(__name__)


class EmailCategorizer:
    
    def __init__(self, config: OllamaConfig):
        self.config = config
        self._validate_ollama()
    
    def _validate_ollama(self):
        try:
            #check ollama access
            models = ollama.list()
            logger.info(f"Connected to Ollama at {self.config.host}")
            
            #check model availability
            model_names = [m['name'] for m in models.get('models', [])]
            if not any(self.config.model in name for name in model_names):
                logger.warning(f"Model {self.config.model} not found. Available: {model_names}")
                logger.info(f"Run: ollama pull {self.config.model}")
                
        except Exception as e:
            logger.error(f"Ollama validation failed: {str(e)}")
            raise RuntimeError(
                f"Cannot connect to Ollama. Ensure it's running at {self.config.host} "
                f"and model '{self.config.model}' is pulled."
            )
    
    def _build_categorization_prompt(self, email: EmailMessage, buckets: List[Bucket]) -> str:
        bucket_descriptions = "\n".join([
            f"{i+1}. {bucket.title}: {bucket.prompt}"
            for i, bucket in enumerate(buckets)
        ])
        
        prompt = f"""You are an email categorization and summarization assistant. Analyze the following email and categorize it into the most appropriate bucket.

EMAIL DETAILS:
Subject: {email.subject}
From: {email.sender}
Content: {email.snippet}

AVAILABLE BUCKETS:
{bucket_descriptions}
{len(buckets) + 1}. uncategorized: Emails that don't fit any specific category

INSTRUCTIONS:
- Analyze the email content carefully
- Summarize the email in a sentence or two
- Select the MOST appropriate bucket (only one)
- Return ONLY a JSON object with this exact format:
{{"bucket_number": <number>,"summary": <summary>, "confidence": <0.0-1.0>}}

Response:"""
        
        return prompt
    
    def _parse_llm_response(self, response: str, buckets_len: int) -> Dict:
        try:
            #extract JSON 
            response = response.strip()
            
            #json objects search
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")
            
            json_str = response[start_idx:end_idx]
            result = json.loads(json_str)
            
            #validate fields
            if 'bucket_number' not in result:
                raise ValueError("Missing 'bucket_number' in response")
            
            if 'summary' not in result:
                raise ValueError("Missing 'summary' in response")
            
            #normalize confidence
            if 'confidence' not in result:
                result['confidence'] = 0.5
            result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return {'bucket_number': buckets_len + 1, 'confidence': 0.0, 'reason': 'Parse error'}
        except Exception as e:
            logger.error(f"Response parsing error: {str(e)}")
            return {'bucket_number': buckets_len + 1, 'confidence': 0.0, 'reason': 'Unknown error'}
    
    def categorize_email(self, email: EmailMessage, buckets: List[Bucket]) -> CategorizedEmail:
        if not buckets:
            #if no buckets available, mark as uncategorized
            return CategorizedEmail(
                email=email,
                bucket_id="uncategorized",
                bucket_title="Uncategorized",
                confidence=1.0
            )
        
        try:
            prompt = self._build_categorization_prompt(email, buckets)
            
            #llm call
            response = ollama.chat(
                model=self.config.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': self.config.temperature,
                }
            )

            print(response)
            
            #parse
            llm_output = response['message']['content']
            parsed = self._parse_llm_response(llm_output, len(buckets))
            
            bucket_number = parsed['bucket_number']
            
            if bucket_number <= len(buckets):
                selected_bucket = buckets[bucket_number - 1]
                bucket_id = selected_bucket.id
                bucket_title = selected_bucket.title
            else:
                bucket_id = "uncategorized"
                bucket_title = "Uncategorized"
            
            logger.debug(f"Categorized '{email.subject}' -> {bucket_title} (confidence: {parsed['confidence']:.2f})")
            
            return CategorizedEmail(
                email=email,
                bucket_id=bucket_id,
                bucket_title=bucket_title,
                summary=parsed['summary'],
                confidence=parsed['confidence']
            )
            
        except Exception as e:
            logger.error(f"Categorization error for email '{email.subject}': {str(e)}")
            #uncategorized fallback
            return CategorizedEmail(
                email=email,
                bucket_id="uncategorized",
                bucket_title="Uncategorized",
                summary=None,
                confidence=0.0
            )
    
    # def categorize_batch(self, emails: List[EmailMessage], 
    #                     buckets: List[Bucket]) -> List[CategorizedEmail]:
    #     categorized = []
        
    #     for i, email in enumerate(emails):
    #         logger.info(f"Categorizing email {i+1}/{len(emails)}: {email.subject}")
    #         categorized_email = self.categorize_email(email, buckets)
    #         categorized.append(categorized_email)
        
    #     logger.info(f"Categorized {len(categorized)} emails")
    #     return categorized