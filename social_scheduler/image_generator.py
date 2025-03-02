import requests
from openai import OpenAI
from typing import Optional
import os
from pathlib import Path
from datetime import datetime

class ImageGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        # Create images directory if it doesn't exist
        self.images_dir = Path("./images_generated")
        self.images_dir.mkdir(exist_ok=True)
    
    def generate_image(self, prompt: str = "a white siamese cat", size: str = "1024x1024") -> Optional[str]:
        """
        Generate an image using DALL-E based on the prompt
        Returns the path to the saved image
        """
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            
            # Download the image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                # Create timestamped filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Create a sanitized version of the prompt for the filename
                prompt_slug = "".join(c if c.isalnum() else "_" for c in prompt[:30]).rstrip("_")
                filename = f"{timestamp}_{prompt_slug}.png"
                
                # Save to the images directory
                file_path = self.images_dir / filename
                with open(file_path, "wb") as f:
                    f.write(image_response.content)
                
                return str(file_path)
            else:
                print(f"Failed to download image: {image_response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    def create_prompt_from_content(self, content_item) -> str:
        """Create an image generation prompt based on content"""
        return f"Create a visually appealing social media image representing: {content_item.title}. The image should be professional, engaging, and suitable for Instagram." 