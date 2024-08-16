import os
import json
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

DATA_DIR = 'data/tg'
IMAGE_DIR = 'static/img/tg'
POSTS_FILE = f'{DATA_DIR}/posts.json'

async def get_new_messages(bot, last_message_id):
    messages = []
    offset = 0
    while True:
        updates = await bot.get_updates(offset=offset, limit=100)
        if not updates:
            break
        for update in updates:
            if update.channel_post and str(update.channel_post.chat.id) == CHANNEL_ID:
                if update.channel_post.message_id > last_message_id:
                    messages.append(update.channel_post)
            offset = update.update_id + 1
    return messages

async def process_messages(bot, messages):
    posts = []
    for message in messages:
        post = {
            'id': message.message_id,
            'date': message.date.isoformat(),
            'text': message.text or '',
            'images': []
        }

        if message.photo:
            photo = message.photo[-1]
            file = await bot.get_file(photo.file_id)
            image_path = f'{IMAGE_DIR}/{message.message_id}.jpg'
            await file.download_to_drive(image_path)
            post['images'].append({
                'width': photo.width,
                'height': photo.height,
                'url': f'/img/tg/{message.message_id}.jpg'
            })

        posts.append(post)

    return posts

def load_existing_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

async def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    existing_posts = load_existing_posts()
    last_message_id = max([post['id'] for post in existing_posts]) if existing_posts else 0

    bot = Bot(token=BOT_TOKEN)
    new_messages = await get_new_messages(bot, last_message_id)
    new_posts = await process_messages(bot, new_messages)

    all_posts = existing_posts + new_posts
    all_posts.sort(key=lambda x: x['id'], reverse=True)

    save_posts(all_posts)

if __name__ == '__main__':
    asyncio.run(main())
