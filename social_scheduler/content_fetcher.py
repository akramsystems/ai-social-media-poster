import feedparser
from typing import List, Dict, Any
import random
from dataclasses import dataclass
import time  # Add this import for sleep functionality

@dataclass
class ContentItem:
    title: str
    description: str
    link: str
    source: str
    published: str

class ContentFetcher:
    def __init__(self, rss_feeds: List[str], request_delay: float = 1.0):
        self.rss_feeds = rss_feeds
        self.request_delay = request_delay  # Delay between requests in seconds
    
    def fetch_content(self, topics: List[str] = None, limit: int = 5) -> List[ContentItem]:
        """Fetch content from RSS feeds, optionally filtered by topics"""
        all_items = []
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                source_name = feed.feed.title if hasattr(feed.feed, 'title') else feed_url
                
                for entry in feed.entries:
                    item = ContentItem(
                        title=entry.title,
                        description=self._clean_description(entry.description) if hasattr(entry, 'description') else "",
                        link=entry.link,
                        source=source_name,
                        published=entry.published if hasattr(entry, 'published') else ""
                    )
                    
                    # Filter by topics if provided
                    if topics:
                        if any(topic.lower() in item.title.lower() or 
                               topic.lower() in item.description.lower() 
                               for topic in topics):
                            all_items.append(item)
                    else:
                        all_items.append(item)
            except Exception as e:
                print(f"Error fetching feed {feed_url}: {e}")
            
            # Add sleep between requests to avoid rate limiting
            time.sleep(self.request_delay)
        
        # Return random selection if we have more than the limit
        if len(all_items) > limit:
            return random.sample(all_items, limit)
        return all_items
    
    def _clean_description(self, html_content: str) -> str:
        """Remove HTML tags from description"""
        # Simple HTML tag removal - in a real app, use a proper HTML parser
        import re
        clean_text = re.sub(r'<.*?>', '', html_content)
        return clean_text 