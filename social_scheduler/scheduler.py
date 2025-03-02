import schedule
import time
import datetime
from typing import Callable, Dict, Any
import json
import os
from pathlib import Path

class Scheduler:
    def __init__(self, config):
        self.config = config
        self.scheduled_jobs = {}
        self.data_dir = Path("./scheduled_posts")
        self.data_dir.mkdir(exist_ok=True)
    
    def schedule_post(self, post_data: Dict[str, Any], post_time: str = None) -> str:
        """Schedule a post for a specific time"""
        # Generate a unique ID for this post
        post_id = f"post_{int(time.time())}"
        
        # Use provided time or default from config
        post_time = post_time or self.config.posting_time
        
        # Save post data
        self._save_post_data(post_id, post_data)
        
        return post_id
    
    def _save_post_data(self, post_id: str, post_data: Dict[str, Any]):
        """Save post data to a file"""
        file_path = self.data_dir / f"{post_id}.json"
        with open(file_path, 'w') as f:
            json.dump(post_data, f)
    
    def get_scheduled_posts(self):
        """Get all scheduled posts"""
        posts = []
        for file_path in self.data_dir.glob("*.json"):
            with open(file_path, 'r') as f:
                post_data = json.load(f)
                post_data['id'] = file_path.stem
                posts.append(post_data)
        return posts
    
    def delete_scheduled_post(self, post_id: str) -> bool:
        """Delete a scheduled post"""
        file_path = self.data_dir / f"{post_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False 