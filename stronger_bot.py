from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup
from functools import wraps
from pydub import AudioSegment
import subprocess
import os
import cv2
import re

API_KEY = 2215758
API_HASH = 'e18c19197e887478b8a77ae46f160847'
BOT_TOKEN = '6616025586:AAGivVAjd2ZhWk0KYHATKeMCSiEUCEPiZYc'
VIDEO_FOLDER = 'videos'
chat_data = {}

app = Client("video_processing_bot", api_id=API_KEY, api_hash=API_HASH, bot_token=BOT_TOKEN)
GET_VIDEO, ADD_WATERMARK, GET_WATERMARK_TEXT, TRIM_VIDEO, GET_TRIM_TIME = range(5)


@app.on_message(filters.command(["start"]))
def start(_, update):
    update.reply_text("Hi! To send a video and apply changes, use the /process_video command.")

@app.on_message(filters.command(["process_video"]))
def process_video(_, update):
    update.reply_text("Please send your video.")

@app.on_message(filters.video & filters.private)
def get_video(_, update):
    chat_id = update.chat.id
    video_path = f"{VIDEO_FOLDER}/{chat_id}_video.mp4"
    update.reply_text("Video is downloading...")
    update.download(file_name=video_path)

    if chat_id not in chat_data:
        chat_data[chat_id] = {}

    chat_data[chat_id].update({"video_path": video_path,"action": set()})
    
    keyboard = [
        ["/add_watermark", "/trim_video"],
        ["/process_and_send"]
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("Video downloaded.\nNow you can make various changes:", reply_markup=keyboard_markup)
    chat_data[chat_id]['action'] = 0

@app.on_message(filters.command(["admin"]))
def add_watermark(_, update):
    keyboard = [
        ["set_default_watermark_text🔖"],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("Video downloaded.\nNow you can make various changes:", reply_markup=keyboard_markup)

@app.on_message(filters.command(["set_default_watermark_text🔖"]))
def add_watermark(_, update):
    keyboard = [
        ["/set_text", "/"],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("Video downloaded.\nNow you can make various changes:", reply_markup=keyboard_markup)

@app.on_message(filters.command(["add_watermark"]))
def add_watermark(_, update):
    chat_id = update.chat.id
    chat_data[chat_id].update({"state": 2})
    update.reply_text("Please enter your watermark text.")

@app.on_message(filters.create(lambda filter, client, update: chat_data.get(update.chat.id, {}).get('state', 0) == 2))
def get_watermark_text(_, update):
    chat_id = update.chat.id
    video_path = chat_data[chat_id]["video_path"]
    chat_data[chat_id].update({"state": 5})
    watermark_text = update.text
    watermark_path = None # its a image

    update.reply_text("Watermark added with the specified text. You can now make other changes or send the video.")
    add_watermark_with_ffmpeg(video_path, watermark_path, watermark_text)
    chat_data[chat_id]['action'] = 1

@app.on_message(filters.command(["trim_video"]))
def trim_video(_, update):
    chat_id = update.chat.id
    chat_data[chat_id].update({"state": 4})
    update.reply_text("Please enter the start and end times in the 'MM:SS MM:SS' format (e.g., 00:01:30 00:05:30):")

@app.on_message(filters.create(lambda filter, client, update: chat_data.get(update.chat.id, {}).get('state', 0) == 4))
def get_trim_time(_, update):
    chat_id = update.chat.id
    video_path = chat_data[chat_id]["video_path"]
    chat_data[chat_id].update({"state": 5})
    time_input = update.text
    match = re.match(r'(?P<start_time>\d+:\d+:\d+) (?P<end_time>\d+:\d+:\d+)', time_input)

    if match:
        start_time = match['start_time']
        end_time = match['end_time']
        
        update.reply_text("Video successfully trimmed. You can now make other changes or send the video.")
        trim_video_with_ffmpeg(video_path, start_time, end_time)
        chat_data[chat_id]['action'] = 1
    else:
        update.reply_text('Incorrect input format. Please enter the time in "MM:SS" format.')

@app.on_message(filters.command(["process_and_send"]))
def process_and_send(_, update):
    chat_id = update.chat.id
    video_path = chat_data[chat_id]["video_path"]
    update.reply_text("Video is proccessing.")
    
    if chat_data[chat_id]['action'] == 0 :
        update.reply_text("No changes applied. Please start again.")
        return

    app.send_video(chat_id=chat_id, video=video_path)

    reply_markup = ReplyKeyboardRemove()
    update.reply_text("Video successfully processed and sent.", reply_markup=reply_markup)
    os.remove(video_path)

def add_watermark_with_ffmpeg(video_path, watermark_path=None, text=None):
    output_path = video_path.replace('_video.mp4', '_out_video.mp4')

    if watermark_path:
        # Adding image watermark
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', watermark_path,
            '-filter_complex', 'overlay=W-w-10:H-h-10',
            '-c:a', 'copy',
            output_path
        ]
    elif text:
        # Adding text watermark
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', f'drawtext=text={text}:fontsize=24:fontcolor=white:x=(w-text_w-30):y=(h-text_h-30)',
            '-c:a', 'copy',
            output_path
        ]
    else:
        raise ValueError("Either watermark_path or text must be provided.")

    subprocess.run(ffmpeg_cmd)
    os.rename(output_path, video_path)

def trim_video_with_ffmpeg(video_path, start_time, end_time):
    output_path = video_path.replace('_video.mp4', '_out_video.mp4')

    ffmpeg_cmd = [
        'ffmpeg',
        '-i', video_path,
        '-ss', start_time,
        '-to', end_time,
        '-c:v', 'copy',
        output_path
    ]

    subprocess.run(ffmpeg_cmd)
    os.rename(output_path, video_path)

if __name__ == "__main__":
    app.run()
