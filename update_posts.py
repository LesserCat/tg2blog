import os
import json
import asyncio
from telegram import Bot
from telegram.error import BadRequest

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

DATA_DIR = 'data/tg'
IMAGE_DIR = 'static/img/tg'
POSTS_FILE = f'{DATA_DIR}/posts.json'

async def get_channel_messages(bot, last_message_id):
    messages = []
    current_id = last_message_id + 1
    while True:
        try:
            message = await bot.get_chat(CHANNEL_ID).get_member(BOT_TOKEN).chat.get_messages(current_id)
            if message:
                messages.append(message)
                current_id += 1
            else:
                break
        except BadRequest:
            break
    return messages

async def process_messages(bot, messages):
    posts = []
    for message in messages:
        text = message.text or message.caption or ''
        
        post = {
            'id': message.message_id,
            'date': message.date.isoformat(),
            'text': text,
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
    new_messages = await get_channel_messages(bot, last_message_id)
    new_posts = await process_messages(bot, new_messages)

    all_posts = existing_posts + new_posts
    all_posts.sort(key=lambda x: x['id'], reverse=True)

    save_posts(all_posts)
    print(f"保存了 {len(new_posts)} 条新消息。总共有 {len(all_posts)} 条消息。")

if __name__ == '__main__':
    asyncio.run(main())
