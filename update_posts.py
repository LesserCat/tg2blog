import os
import json
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

bot = Bot(token=BOT_TOKEN)

async def get_latest_posts():
    # 从 Telegram 获取最新消息
    updates = await bot.get_updates(offset=-1, limit=100)
    posts = []
    for update in updates:
        message = update.channel_post
        if message and str(message.chat.id) == CHANNEL_ID:
            post = {
                'id': message.message_id,
                'date': message.date.isoformat(),
                'text': message.text or '',
                'images': []
            }
            if message.photo:
                photo = message.photo[-1]
                file = await bot.get_file(photo.file_id)
                image_path = f'media/{message.message_id}.jpg'
                await file.download_to_drive(image_path)
                post['images'].append({
                    'width': photo.width,
                    'height': photo.height,
                    'url': image_path,
                    'size': os.path.getsize(image_path)
                })
            posts.append(post)
    return posts

def update_posts_file(new_posts):
    if os.path.exists('posts.json'):
        with open('posts.json', 'r') as f:
            existing_posts = json.load(f)
    else:
        existing_posts = []

    # 合并新旧帖子并去重
    all_posts = existing_posts + new_posts
    unique_posts = {post['id']: post for post in all_posts}.values()
    sorted_posts = sorted(unique_posts, key=lambda x: x['date'])

    with open('posts.json', 'w') as f:
        json.dump(sorted_posts, f, indent=2)

async def main():
    new_posts = await get_latest_posts()
    update_posts_file(new_posts)

if __name__ == '__main__':
    asyncio.run(main())
