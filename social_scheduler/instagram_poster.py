import os
from instagrapi import Client
from typing import Optional
import time

class InstagramPoster:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.client = Client()
        self.is_logged_in = False
    
    def login(self) -> bool:
        """Login to Instagram"""
        try:
            self.client.login(self.username, self.password)
            self.is_logged_in = True
            return True
        except Exception as e:
            print(f"Instagram login failed: {e}")
            return False
    
    def post_content(self, image_path: str, caption: str) -> Optional[str]:
        """Post content to Instagram"""
        if not self.is_logged_in and not self.login():
            return None
        
        try:
            # Upload photo with caption
            media = self.client.photo_upload(
                image_path,
                caption=caption
            )
            
            # Return the media ID
            return media.id
        except Exception as e:
            print(f"Error posting to Instagram: {e}")
            return None 