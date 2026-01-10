# services/social_tools.py
from facebook_scraper import get_profile
import instaloader
import subprocess
import json
import re
import tempfile
from utils.helpers import retry_on_exception
import snscrape.modules.twitter as sntwitter

def get_facebook_metrics(fb_url_or_name):
    """
    Uses facebook_scraper.get_profile (works for many public pages). Returns dict with follower_count, likes_count, posts_count...
    """
    try:
        # facebook_scraper accepts page name or url
        p = get_profile(fb_url_or_name, cookies=None)
        # p is a dict-like object
        return {"page": fb_url_or_name, "followers": p.get("followers"), "likes": p.get("likes"), "about": p.get("about"), "posts_sample": p.get("posts", [])[:3]}
    except Exception as e:
        return {"error": str(e)}

def get_instagram_profile_metrics(insta_url_or_name):
    """
    Uses instaloader programmatically to fetch profile metadata. Returns followers, posts count, last_post_date (iso) if possible.
    """
    try:
        L = instaloader.Instaloader()
        profile_name = insta_url_or_name.rstrip("/").split("/")[-1]
        profile = instaloader.Profile.from_username(L.context, profile_name)
        last_post = None
        posts = profile.get_posts()
        last = None
        for p in posts:
            last = p
            break
        if last:
            last_post = last.date_utc.isoformat()
        return {"username": profile_name, "followers": profile.followers, "posts": profile.mediacount, "last_post": last_post}
    except Exception as e:
        return {"error": str(e)}

def get_twitter_metrics(username_or_url, max_tweets=30):
    """
    Uses snscrape to fetch basic metrics for a user: follower count isn't returned directly by snscrape's scraper
    but we can fetch recent tweets and compute engagement sample.
    """
    try:
        # get username
        uname = username_or_url.rstrip("/").split("/")[-1]
        tweets = []
        for i, t in enumerate(sntwitter.TwitterUserScraper(uname).get_items()):
            if i >= max_tweets:
                break
            tweets.append({"date": t.date.isoformat(), "content": t.content, "likeCount": t.likeCount, "retweetCount": t.retweetCount})
        # compute avg likes
        if tweets:
            avg_likes = sum([t["likeCount"] for t in tweets]) / len(tweets)
        else:
            avg_likes = 0
        return {"username": uname, "sample_tweets": tweets, "avg_likes": avg_likes}
    except Exception as e:
        return {"error": str(e)}
