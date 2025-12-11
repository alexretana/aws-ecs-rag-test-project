import json
import boto3
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()


class BedrockGenerator:
    """Generate responses using AWS Bedrock Llama 3."""
    
    def __init__(self):
        settings = get_settings()
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region
        )
        self.model_id = settings.llm_model_id
    
    def _build_prompt(self, query: str, context_chunks: list) -> str:
        """Build prompt with retrieved context."""
        context = "\n\n".join([
            f"Document {i+1}:\n{chunk['content']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant. Answer the user's question based on the provided context. 
If the context doesn't contain enough information to answer the question, say so.
Be concise and accurate in your responses.
Only use information from the provided context.

Context:
{context}
<|eot_id|><|start_header_id|>user<|end_header_id|>

{query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        return prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, query: str, context_chunks: list) -> str:
        """Generate response using retrieved context."""
        if not context_chunks:
            return "I couldn't find any relevant information to answer your question."
        
        prompt = self._build_prompt(query, context_chunks)
        
        try:
            logger.info("Generating response", query=query[:50], context_chunks=len(context_chunks))
            
            body = json.dumps({
                "prompt": prompt,
                "max_gen_len": 512,
                "temperature": 0.7,
                "top_p": 0.9,
            })
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            generated_text = response_body.get("generation", "")
            
            logger.info("Generated response", response_length=len(generated_text))
            return generated_text.strip()
            
        except Exception as e:
            logger.error("Failed to generate response", error=str(e), query=query[:50])
            raise
    
    def generate_with_streaming(self, query: str, context_chunks: list):
        """Generate response with streaming (for future implementation)."""
        # This would be implemented for real-time streaming responses
        # For now, delegate to non-streaming method
        return self.generate(query, context_chunks)
    
    def _extract_citations(self, response: str, context_chunks: list) -> list:
        """Extract citations from generated response (placeholder for future enhancement)."""
        # This would analyze the response to find which chunks were cited
        # For now, return empty list
        return []