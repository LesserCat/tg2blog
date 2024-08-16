import os
import json
import asyncio
from telegram import Bot

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

DATA_DIR = 'data/tg'
IMAGE_DIR = 'static/img/tg'
POSTS_FILE = f'{DATA_DIR}/posts.json'

async def get_channel_messages(bot):
    messages = []
    offset_id = 0
    while True:
        new_messages = await bot.get_chat_history(chat_id=CHANNEL_ID, limit=100, offset_id=offset_id)
        if not new_messages:
            break
        messages.extend(new_messages)
        offset_id = messages[-1].id - 1
    return messages

async def process_messages(bot, messages):
    posts = []
    for message in messages:
        post = {
            'id': message.id,
            'date': message.date.isoformat(),
            'text': message.text or '',
            'images': []
        }

        if message.photo:
            photo = message.photo[-1]
            file = await bot.get_file(photo.file_id)
            image_path = f'{IMAGE_DIR}/{message.id}.jpg'
            await file.download_to_drive(image_path)
            post['images'].append({
                'width': photo.width,
                'height': photo.height,
                'url': f'/img/tg/{message.id}.jpg'
            })

        posts.append(post)

    return posts

def save_posts(posts):
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

async def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    bot = Bot(token=BOT_TOKEN)
    messages = await get_channel_messages(bot)
    posts = await process_messages(bot, messages)
    save_posts(posts)

if __name__ == '__main__':
    asyncio.run(main())
