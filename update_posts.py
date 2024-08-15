import os
import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder
from telegram.constants import ParseMode
import emoji

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

async def get_latest_posts(application):
    offset = 0
    posts = []
    while True:
        updates = await application.bot.get_updates(offset=offset, limit=100)
        if not updates:
            break
        for update in updates:
            if update.channel_post and str(update.channel_post.chat.id) == CHANNEL_ID:
                post = await process_message(application, update.channel_post)
                posts.append(post)
            offset = update.update_id + 1
    return posts

async def process_message(application, message):
    post = {
        'id': message.message_id,
        'date': message.date.isoformat(),
        'text': message.text or '',
        'images': []
    }

    # 处理文本中的表情
    if message.text:
        post['text'] = emoji.demojize(message.text)

    # 处理图片
    if message.photo:
        photo = message.photo[-1]
        file = await application.bot.get_file(photo.file_id)
        image_path = f'media/{message.message_id}.jpg'
        await file.download_to_drive(image_path)
        post['images'].append({
            'width': photo.width,
            'height': photo.height,
            'url': image_path,
            'size': os.path.getsize(image_path)
        })

    # 处理贴纸（包括动画贴纸）
    if message.sticker:
        file = await application.bot.get_file(message.sticker.file_id)
        sticker_path = f'media/{message.message_id}.webp'
        await file.download_to_drive(sticker_path)
        post['images'].append({
            'width': message.sticker.width,
            'height': message.sticker.height,
            'url': sticker_path,
            'size': os.path.getsize(sticker_path)
        })

    return post

def update_posts_file(new_posts):
    if os.path.exists('posts.json'):
        with open('posts.json', 'r') as f:
            existing_posts = json.load(f)
    else:
        existing_posts = []

    # 合并新旧帖子并去重
    all_posts = existing_posts + new_posts
    unique_posts = {post['id']: post for post in all_posts}.values()
    sorted_posts = sorted(unique_posts, key=lambda x: x['id'], reverse=True)

    with open('posts.json', 'w') as f:
        json.dump(sorted_posts, f, indent=2)

async def main():
    os.makedirs('media', exist_ok=True)
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    new_posts = await get_latest_posts(application)
    update_posts_file(new_posts)

if __name__ == '__main__':
    asyncio.run(main())
