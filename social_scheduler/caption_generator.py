from openai import OpenAI
from typing import List, Dict, Any
from .content_fetcher import ContentItem

class CaptionGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def generate_caption(self, content_item: ContentItem, tone: str, include_hashtags: bool = True) -> str:
        """Generate a caption for social media based on the content item"""
        try:
            prompt = self._create_caption_prompt(content_item, tone, include_hashtags)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional social media content creator. Your task is to create engaging, concise captions for Instagram posts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating caption: {e}")
            return f"Check out this interesting content: {content_item.title} {content_item.link}"
    
    def _create_caption_prompt(self, content_item: ContentItem, tone: str, include_hashtags: bool) -> str:
        """Create a prompt for the caption generation"""
        prompt = f"""
        Create an engaging Instagram caption for the following content:
        
        Title: {content_item.title}
        Description: {content_item.description}
        Source: {content_item.source}
        
        The caption should:
        - Be in a {tone} tone
        - Be concise (max 150 words)
        - Include a call to action
        - Reference the original source
        """
        
        if include_hashtags:
            prompt += "\n- Include 3-5 relevant hashtags at the end"
            
        return prompt 