import logging
import uuid
from datetime import datetime
from typing import List, Optional
import chromadb
from chromadb.config import Settings

from models import Bucket
from config import ChromaConfig

logger = logging.getLogger(__name__)


class BucketManager:
    def __init__(self, config: ChromaConfig):
        self.config = config
        self._client = None
        self._collection = None
        self._initialize()
    
    def _initialize(self):
        try:
            self._client = chromadb.PersistentClient(
                path=str(self.config.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"description": "Email categorization buckets"}
            )
            
            logger.info(f"Initialized ChromaDB collection: {self.config.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise RuntimeError(f"ChromaDB initialization failed: {str(e)}")
    
    def create_bucket(self, title: str, prompt: str) -> Bucket:

        bucket_id = str(uuid.uuid4())
        bucket = Bucket(
            id=bucket_id,
            title=title,
            prompt=prompt,
            created_at=datetime.now()
        )
        
        try:
            #store in db
            self._collection.add(
                ids=[bucket_id],
                documents=[prompt],  
                metadatas=[{
                    'title': title,
                    'created_at': bucket.created_at.isoformat()
                }]
            )
            
            logger.info(f"Created bucket: {title}")
            return bucket
            
        except Exception as e:
            logger.error(f"Failed to create bucket: {str(e)}")
            raise RuntimeError(f"Bucket creation failed: {str(e)}")
    
    def get_all_buckets(self) -> List[Bucket]:
        try:
            #items from collection
            results = self._collection.get()
            
            if not results['ids']:
                return []
            
            buckets = []
            for i, bucket_id in enumerate(results['ids']):
                bucket = Bucket(
                    id=bucket_id,
                    title=results['metadatas'][i]['title'],
                    prompt=results['documents'][i],
                    created_at=datetime.fromisoformat(results['metadatas'][i]['created_at'])
                )
                buckets.append(bucket)
            
            logger.info(f"Retrieved {len(buckets)} buckets")
            return buckets
            
        except Exception as e:
            logger.error(f"Failed to get buckets: {str(e)}")
            return []
    
    def get_bucket(self, bucket_id: str) -> Optional[Bucket]:
        try:
            results = self._collection.get(ids=[bucket_id])
            
            if not results['ids']:
                return None
            
            return Bucket(
                id=results['ids'][0],
                title=results['metadatas'][0]['title'],
                prompt=results['documents'][0],
                created_at=datetime.fromisoformat(results['metadatas'][0]['created_at'])
            )
            
        except Exception as e:
            logger.error(f"Failed to get bucket {bucket_id}: {str(e)}")
            return None
    
    def update_bucket(self, bucket_id: str, title: Optional[str] = None, 
                     prompt: Optional[str] = None) -> bool:
        try:
            bucket = self.get_bucket(bucket_id)
            if not bucket:
                return False
            
            new_title = title if title is not None else bucket.title
            new_prompt = prompt if prompt is not None else bucket.prompt
            
            #update 
            self._collection.update(
                ids=[bucket_id],
                documents=[new_prompt],
                metadatas=[{
                    'title': new_title,
                    'created_at': bucket.created_at.isoformat()
                }]
            )
            
            logger.info(f"Updated bucket: {bucket_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update bucket: {str(e)}")
            return False
    
    def delete_bucket(self, bucket_id: str) -> bool:
        try:
            self._collection.delete(ids=[bucket_id])
            logger.info(f"Deleted bucket: {bucket_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete bucket: {str(e)}")
            return False
    
    def get_bucket_count(self) -> int:
        try:
            results = self._collection.get()
            return len(results['ids'])
        except Exception as e:
            logger.error(f"Failed to get bucket count: {str(e)}")
            return 0