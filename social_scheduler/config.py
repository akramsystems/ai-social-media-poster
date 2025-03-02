from dataclasses import dataclass
from typing import List
import os
from dotenv import load_dotenv

load_dotenv(override=True)

@dataclass
class Config:
    # OpenAI API configuration
    openai_api_key: str
    
    # Instagram API configuration
    instagram_username: str
    instagram_password: str
    
    # RSS feed sources
    rss_feeds: List[str]
    
    # Scheduling configuration
    posting_frequency: str  # daily, weekly, etc.
    posting_time: str  # HH:MM format
    
    # Content preferences
    content_topics: List[str]
    content_tone: str  # professional, casual, humorous, etc.
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            instagram_username=os.getenv("INSTAGRAM_USERNAME"),
            instagram_password=os.getenv("INSTAGRAM_PASSWORD"),
            rss_feeds=os.getenv("RSS_FEEDS", "").split(","),
            posting_frequency=os.getenv("POSTING_FREQUENCY", "daily"),
            posting_time=os.getenv("POSTING_TIME", "09:00"),
            content_topics=os.getenv("CONTENT_TOPICS", "technology,business").split(","),
            content_tone=os.getenv("CONTENT_TONE", "professional"),
        ) 