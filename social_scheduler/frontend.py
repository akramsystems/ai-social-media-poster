import gradio as gr
import os
import random
from datetime import datetime
from pathlib import Path
from PIL import Image
import io

from .config import Config
from .image_generator import ImageGenerator
from .caption_generator import CaptionGenerator
from .instagram_poster import InstagramPoster
from .content_fetcher import ContentItem, ContentFetcher


def generate_sample_content():
    """Generate sample content to auto-populate the form"""
    config = Config.from_env()
    
    # Try to fetch real content from RSS feeds first
    try:
        fetcher = ContentFetcher(config.rss_feeds)
        content_items = fetcher.fetch_content(config.content_topics, 1)
        if content_items:
            item = content_items[0]
            return {
                "title": item.title,
                "description": item.description,
                "image_prompt": f"Create a visually appealing Instagram image for: {item.title}",
                "tone": "professional"
            }
    except Exception as e:
        print(f"Error fetching sample content: {e}")
    
    # Fallback to pre-defined sample content
    sample_titles = [
        "10 Tech Trends That Will Shape 2024",
        "The Future of AI in Healthcare",
        "How Sustainable Practices are Transforming Business",
        "Digital Marketing Strategies for Small Businesses",
        "The Rise of Remote Work: Benefits and Challenges"
    ]
    
    sample_descriptions = [
        "Exploring the innovative technologies that will define the upcoming year and how they'll impact various industries.",
        "An in-depth look at how artificial intelligence is revolutionizing healthcare delivery, diagnosis, and patient care.",
        "Examining how companies are adopting sustainable practices to reduce environmental impact while improving their bottom line.",
        "Practical digital marketing strategies that small businesses can implement to increase visibility and drive growth.",
        "Analyzing the ongoing shift to remote work arrangements and its effects on productivity, company culture, and work-life balance."
    ]
    
    # Choose random samples
    idx = random.randint(0, len(sample_titles) - 1)
    
    return {
        "title": sample_titles[idx],
        "description": sample_descriptions[idx],
        "image_prompt": f"Create a visually appealing Instagram image for: {sample_titles[idx]}",
        "tone": random.choice(["professional", "casual", "inspirational"])
    }


def create_and_post_content(title, description, prompt, custom_image=None, tone="professional", post_now=True):
    """Process the inputs and create a post"""
    config = Config.from_env()
    
    # Create ContentItem
    content_item = ContentItem(
        title=title,
        description=description,
        link="",
        source="Gradio Frontend",
        published=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Generate image or use custom upload
    image_path = None
    if custom_image is not None:
        # Save the uploaded image
        images_dir = Path("./images_generated")
        images_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = str(images_dir / f"{timestamp}_uploaded.png")
        Image.open(custom_image).save(image_path)
    else:
        # Generate image with DALL-E
        image_generator = ImageGenerator(config.openai_api_key)
        image_prompt = prompt or f"Create a visually appealing social media image representing: {title}"
        image_path = image_generator.generate_image(image_prompt)
    
    if not image_path:
        return "Failed to generate or process image.", None
    
    # Generate caption
    caption_generator = CaptionGenerator(config.openai_api_key)
    caption = caption_generator.generate_caption(content_item, tone)
    
    # If post_now, post to Instagram
    result_message = ""
    if post_now:
        poster = InstagramPoster(config.instagram_username, config.instagram_password)
        if not poster.login():
            return "Failed to login to Instagram.", image_path
        
        result = poster.post_content(image_path, caption)
        if result:
            result_message = f"Posted successfully to Instagram! Media ID: {result}"
        else:
            result_message = "Failed to post to Instagram."
    else:
        result_message = "Image and caption generated but not posted."
    
    return f"{result_message}\n\nGenerated caption:\n{caption}", image_path


def populate_fields():
    """Function to populate the form fields with sample data"""
    sample = generate_sample_content()
    return [
        sample["title"],
        sample["description"],
        sample["image_prompt"],
        None,  # custom image stays empty
        sample["tone"],
        True,  # post_now checkbox
    ]


def launch_frontend():
    """Launch the Gradio frontend"""
    with gr.Blocks(theme=gr.themes.Soft(), title="Social Scheduler") as app:
        gr.Markdown("# 📱 Social Scheduler")
        gr.Markdown("Generate and post content to Instagram with AI assistance")
        
        with gr.Row():
            with gr.Column():
                # Add auto-populate button at the top
                auto_populate = gr.Button("✨ Auto-Populate Fields", variant="secondary")
                
                title = gr.Textbox(label="Post Title", placeholder="Enter the main title for your post")
                description = gr.Textbox(label="Description", placeholder="Enter more details about your post", lines=3)
                image_prompt = gr.Textbox(
                    label="Image Generation Prompt (Optional)", 
                    placeholder="Enter a prompt for DALL-E or leave blank to generate from title",
                    lines=2
                )
                custom_image = gr.Image(
                    label="Or Upload Your Own Image (Optional)", 
                    type="filepath"
                )
                
                tone_options = ["professional", "casual", "humorous", "inspirational", "educational"]
                tone = gr.Dropdown(label="Caption Tone", choices=tone_options, value="professional")
                
                post_now = gr.Checkbox(label="Post to Instagram immediately", value=True)
                
                create_button = gr.Button("Create Post", variant="primary")
            
            with gr.Column():
                output = gr.Textbox(label="Result", lines=8)
                output_image = gr.Image(label="Generated or Uploaded Image")
        
        # Connect the auto-populate button
        auto_populate.click(
            fn=populate_fields,
            inputs=[],
            outputs=[title, description, image_prompt, custom_image, tone, post_now]
        )
        
        # Connect the create post button
        create_button.click(
            fn=create_and_post_content,
            inputs=[title, description, image_prompt, custom_image, tone, post_now],
            outputs=[output, output_image]
        )
    
    app.launch(share=True)


if __name__ == "__main__":
    launch_frontend() 