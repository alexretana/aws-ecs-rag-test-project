import json
import boto3
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()


class BedrockEmbeddings:
    """Generate embeddings using AWS Bedrock Titan."""
    
    def __init__(self):
        settings = get_settings()
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region
        )
        self.model_id = settings.embedding_model_id
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_text(self, text: str) -> list:
        """Generate embedding for a single text."""
        body = json.dumps({
            "inputText": text
        })
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])
            
            logger.debug("Generated embedding", text_length=len(text), embedding_dim=len(embedding))
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e), text_length=len(text))
            raise
    
    def embed_texts(self, texts: list) -> list:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
                logger.debug("Processed text", index=i, total=len(texts))
            except Exception as e:
                logger.error("Failed to embed text", index=i, error=str(e))
                # For batch processing, we might want to continue with other texts
                # or raise the exception depending on requirements
                raise
        
        logger.info("Generated embeddings", count=len(embeddings))
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model."""
        # Titan Text Embeddings v1 generates 1536-dimensional vectors
        return 1536