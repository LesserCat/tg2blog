import os
import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder
from telegram.constants import ParseMode
import emoji

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

DATA_DIR = 'data/tg'
IMAGE_DIR = 'static/img/tg'
POSTS_FILE = f'{DATA_DIR}/posts.json'

async def get_latest_posts(application):
    offset = 0
    posts = []
    deleted_ids = []
    while True:
        updates = await application.bot.get_updates(offset=offset, limit=100)
        if not updates:
            break
        for update in updates:
            if update.channel_post and str(update.channel_post.chat.id) == CHANNEL_ID:
                post = await process_message(application, update.channel_post)
                posts.append(post)
            elif update.edited_channel_post and str(update.edited_channel_post.chat.id) == CHANNEL_ID:
                post = await process_message(application, update.edited_channel_post)
                posts.append(post)
            elif update.channel_post is None and update.edited_channel_post is None:
                # This might be a deletion event
                deleted_ids.append(update.update_id)
            offset = update.update_id + 1
    return posts, deleted_ids

async def process_message(application, message):
    post = {
        'id': message.message_id,
        'date': message.date.isoformat(),
        'text': '',
        'images': []
    }

    if message.text:
        # 使用 encode 和 decode 来确保正确处理 Unicode 字符
        post['text'] = message.text.encode('utf-8').decode('utf-8')

    if message.photo:
        photo = message.photo[-1]
        file = await application.bot.get_file(photo.file_id)
        image_path = f'{IMAGE_DIR}/{message.message_id}.jpg'
        await file.download_to_drive(image_path)
        post['images'].append({
            'width': photo.width,
            'height': photo.height,
            'url': f'/img/tg/{message.message_id}.jpg',
            'size': os.path.getsize(image_path)
        })

    if message.sticker:
        file = await application.bot.get_file(message.sticker.file_id)
        sticker_path = f'{IMAGE_DIR}/{message.message_id}.webp'
        await file.download_to_drive(sticker_path)
        post['images'].append({
            'width': message.sticker.width,
            'height': message.sticker.height,
            'url': f'/img/tg/{message.message_id}.webp',
            'size': os.path.getsize(sticker_path)
        })

    return post

def update_posts_file(new_posts, deleted_ids):
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r', encoding='utf-8') as f:
            existing_posts = json.load(f)
    else:
        existing_posts = []

    # Remove deleted posts
    existing_posts = [post for post in existing_posts if post['id'] not in deleted_ids]

    # Delete associated image files
    for deleted_id in deleted_ids:
        jpg_path = f'{IMAGE_DIR}/{deleted_id}.jpg'
        webp_path = f'{IMAGE_DIR}/{deleted_id}.webp'
        if os.path.exists(jpg_path):
            os.remove(jpg_path)
        if os.path.exists(webp_path):
            os.remove(webp_path)

    all_posts = existing_posts + new_posts
    unique_posts = {post['id']: post for post in all_posts}.values()
    sorted_posts = sorted(unique_posts, key=lambda x: x['id'], reverse=True)

    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted_posts, f, ensure_ascii=False, indent=2)

async def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    new_posts, deleted_ids = await get_latest_posts(application)
    update_posts_file(new_posts, deleted_ids)

if __name__ == '__main__':
    asyncio.run(main())
