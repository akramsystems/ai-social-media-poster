import click
import os
import json
from pathlib import Path
from datetime import datetime
import time

from .config import Config
from .content_fetcher import ContentFetcher
from .image_generator import ImageGenerator
from .caption_generator import CaptionGenerator
from .instagram_poster import InstagramPoster
from .scheduler import Scheduler

@click.group()
@click.pass_context
def cli(ctx):
    """Social Scheduler - AI-powered social media content scheduler"""
    # Load configuration
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config.from_env()

@cli.command()
@click.option('--topics', '-t', help='Comma-separated list of topics to filter content')
@click.option('--limit', '-l', default=5, help='Number of content items to fetch')
@click.pass_context
def fetch_content(ctx, topics, limit):
    """Fetch content from configured RSS feeds"""
    config = ctx.obj['config']
    
    topics_list = topics.split(',') if topics else config.content_topics
    
    fetcher = ContentFetcher(config.rss_feeds)
    content_items = fetcher.fetch_content(topics_list, limit)
    
    click.echo(f"Found {len(content_items)} content items:")
    for i, item in enumerate(content_items, 1):
        click.echo(f"\n{i}. {item.title}")
        click.echo(f"   Source: {item.source}")
        click.echo(f"   Link: {item.link}")
        click.echo(f"   Published: {item.published}")

@cli.command()
@click.option('--prompt', '-p', required=True, help='Prompt for image generation')
@click.pass_context
def generate_image(ctx, prompt):
    """Generate an image using DALL-E"""
    config = ctx.obj['config']
    
    generator = ImageGenerator(config.openai_api_key)
    image_path = generator.generate_image(prompt)
    
    if image_path:
        click.echo(f"Image generated successfully and saved to: {image_path}")
    else:
        click.echo("Failed to generate image")

@cli.command()
@click.option('--title', required=True, help='Content title')
@click.option('--description', help='Content description')
@click.option('--link', help='Content link')
@click.option('--source', default='Manual Entry', help='Content source')
@click.option('--tone', help='Caption tone (professional, casual, humorous)')
@click.pass_context
def generate_caption(ctx, title, description, link, source, tone):
    """Generate a caption using OpenAI"""
    config = ctx.obj['config']
    
    from .content_fetcher import ContentItem
    content_item = ContentItem(
        title=title,
        description=description or "",
        link=link or "",
        source=source,
        published=datetime.now().strftime("%Y-%m-%d")
    )
    
    generator = CaptionGenerator(config.openai_api_key)
    caption = generator.generate_caption(content_item, tone or config.content_tone)
    
    click.echo("\nGenerated Caption:")
    click.echo("=================")
    click.echo(caption)

@cli.command()
@click.option('--rss-index', '-r', type=int, help='Index of RSS item to use (from fetch-content)')
@click.option('--time', '-t', help='Posting time (HH:MM format)')
@click.option('--post-now', '-n', is_flag=True, help='Post immediately instead of scheduling')
@click.pass_context
def create_post(ctx, rss_index, time, post_now):
    """Create and schedule a post from RSS content"""
    config = ctx.obj['config']
    
    # Fetch content
    fetcher = ContentFetcher(config.rss_feeds)
    content_items = fetcher.fetch_content(config.content_topics, 1)
    
    if rss_index is not None:
        if 1 <= rss_index <= len(content_items):
            content_item = content_items[rss_index - 1]
        else:
            click.echo(f"Invalid index. Please choose between 1 and {len(content_items)}")
            return
    else:
        # Display content items for selection
        click.echo("Available content items:")
        for i, item in enumerate(content_items, 1):
            click.echo(f"{i}. {item.title} (from {item.source})")
        
        selected = click.prompt("Select content item (number)", type=int)
        if 1 <= selected <= len(content_items):
            content_item = content_items[selected - 1]
        else:
            click.echo("Invalid selection")
            return
    
    # Generate image
    click.echo("\nGenerating image...")
    image_generator = ImageGenerator(config.openai_api_key)
    prompt = image_generator.create_prompt_from_content(content_item)
    image_path = image_generator.generate_image(prompt)
    
    if not image_path:
        click.echo("Failed to generate image. Aborting.")
        return
    
    click.echo(f"Image generated: {image_path}")
    
    # Generate caption
    click.echo("\nGenerating caption...")
    caption_generator = CaptionGenerator(config.openai_api_key)
    caption = caption_generator.generate_caption(content_item, config.content_tone)
    
    click.echo("\nGenerated Caption:")
    click.echo("=================")
    click.echo(caption)
    
    # If post_now flag is set, post immediately
    if post_now:
        click.echo("\nPosting to Instagram...")
        poster = InstagramPoster(config.instagram_username, config.instagram_password)
        
        if not poster.login():
            click.echo("Failed to login to Instagram. Aborting.")
            return
        
        result = poster.post_content(image_path, caption)
        
        if result:
            click.echo(f"Posted successfully to Instagram! Media ID: {result}")
        else:
            click.echo("Failed to post to Instagram.")
    else:
        # Schedule the post
        scheduler = Scheduler(config)
        post_data = {
            "content_item": {
                "title": content_item.title,
                "description": content_item.description,
                "link": content_item.link,
                "source": content_item.source,
                "published": content_item.published
            },
            "image_path": image_path,
            "caption": caption,
            "scheduled_time": time or config.posting_time,
            "created_at": datetime.now().isoformat()
        }
        
        post_id = scheduler.schedule_post(post_data, time)
        click.echo(f"\nPost scheduled successfully! Post ID: {post_id}")

@cli.command()
@click.pass_context
def list_scheduled(ctx):
    """List all scheduled posts"""
    config = ctx.obj['config']
    scheduler = Scheduler(config)
    
    posts = scheduler.get_scheduled_posts()
    
    if not posts:
        click.echo("No scheduled posts found.")
        return
    
    click.echo(f"Found {len(posts)} scheduled posts:")
    for post in posts:
        click.echo(f"\nID: {post['id']}")
        click.echo(f"Title: {post['content_item']['title']}")
        click.echo(f"Scheduled for: {post['scheduled_time']}")
        click.echo(f"Created at: {post['created_at']}")

@cli.command()
@click.argument('post_id')
@click.pass_context
def post_now(ctx, post_id):
    """Post a scheduled item immediately"""
    config = ctx.obj['config']
    scheduler = Scheduler(config)
    
    # Find the post
    posts = scheduler.get_scheduled_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        click.echo(f"Post with ID {post_id} not found.")
        return
    
    # Post to Instagram
    click.echo("Posting to Instagram...")
    poster = InstagramPoster(config.instagram_username, config.instagram_password)
    breakpoint()
    
    if not poster.login():
        click.echo("Failed to login to Instagram. Aborting.")
        return
    
    result = poster.post_content(post['image_path'], post['caption'])
    
    if result:
        click.echo(f"Posted successfully to Instagram! Media ID: {result}")
        # Delete the scheduled post
        scheduler.delete_scheduled_post(post_id)
    else:
        click.echo("Failed to post to Instagram.")

@cli.command()
@click.argument('post_id')
@click.pass_context
def delete_post(ctx, post_id):
    """Delete a scheduled post"""
    config = ctx.obj['config']
    scheduler = Scheduler(config)
    
    if scheduler.delete_scheduled_post(post_id):
        click.echo(f"Post {post_id} deleted successfully.")
    else:
        click.echo(f"Post {post_id} not found.")

if __name__ == '__main__':
    cli(obj={}) 