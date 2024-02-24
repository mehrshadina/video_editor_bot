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
default_watermark_text = ''

app = Client("video_processing_bot", api_id=API_KEY, api_hash=API_HASH, bot_token=BOT_TOKEN)
GET_VIDEO, ADD_WATERMARK, GET_WATERMARK_TEXT, TRIM_VIDEO, GET_TRIM_TIME = range(5)


def read_and_update_default_watermark(new_text=None):
    file_path = 'watermark.txt'

    # Read the current default watermark text
    try:
        with open(file_path, 'r') as file:
            current_text = file.readline().strip()
    except FileNotFoundError:
        current_text = ""

    default_watermark_text = current_text
    # Update the default watermark text if a new text is provided
    if new_text:
        with open(file_path, 'w') as file:
            file.write(new_text)
        return f"Default watermark text updated to: {new_text}"
        default_watermark_text = new_text


@app.on_message(filters.command(["start"]))
def start(_, update):
    update.reply_text("🎞 Hi!\nTo send a video and apply changes, use the /process_video command.")

@app.on_message(filters.command(["process_video"]))
def process_video(_, update):
    update.reply_text("Please send your video. 🎬")

@app.on_message(filters.video & filters.private)
def get_video(_, update):
    chat_id = update.chat.id
    video_path = f"{VIDEO_FOLDER}/{chat_id}_video.mp4"
    video_is_downloading = update.reply_text("Video is downloading...")
    update.download(file_name=video_path)

    if chat_id not in chat_data:
        chat_data[chat_id] = {}

    chat_data[chat_id].update({"video_path": video_path,"action": set()})
    
    keyboard = [
        ["/add_watermark💱", "/trim_video✂️"],
        ["/process_and_send🎞"]
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    video_is_downloading.edit_text("Video downloaded. ✅")
    update.reply_text("Now you can make various changes: 👇", reply_markup=keyboard_markup)
    chat_data[chat_id]['action'] = 0

@app.on_message(filters.command(["admin", "Back"]))
def add_watermark(_, update):
    chat_id = update.chat.id

    if chat_id not in chat_data:
        chat_data[chat_id] = {}

    keyboard = [
        ["/set_default_watermark_text🔖"], 
        ['/set_font_size🈶', '/set_font_color™️'],
        ['/set_x↔️', '/set_y↕️'],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("You are now in admin menue. 👤\nUse the buttons bellow to configure default settings. 👇", reply_markup=keyboard_markup)



@app.on_message(filters.command(["set_default_watermark_text🔖"]))
def set_default_watermark(_, update):
    chat_id = update.chat.id
    # Your logic to set default watermark text goes here
    keyboard = [
        ["/Back"],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("Enter watermark text:", reply_markup=keyboard_markup)
    chat_data[chat_id]['state'] = 'set_default_watermark'

@app.on_message(filters.create(lambda filter, client, update: chat_data.get(update.chat.id, {}).get('state', 0) == 'set_default_watermark'))
def set_default_watermark_message(_, update):
    chat_id = update.chat.id
    text = update.text

    re.sub(r'text=.*:', f'text={text}:', default_watermark_text)
    read_and_update_default_watermark(default_watermark_text)


    keyboard = [
        ["/set_default_watermark_text🔖"], 
        ['/set_font_size🈶', '/set_font_color™️'],
        ['/set_x↔️', '/set_y↕️'],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("Default watermark text has been set successfully. ✅", reply_markup=keyboard_markup)



@app.on_message(filters.command(["set_font_size🈶"]))
def set_font_size(_, update):
    chat_id = update.chat.id
    keyboard = [
        ["/Back"],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text('Enter Font size in this format (ex. 26) [default 26]:', reply_markup=keyboard_markup)
    chat_data[chat_id]['state'] = 'set_font_size'

@app.on_message(filters.create(lambda filter, client, update: chat_data.get(update.chat.id, {}).get('state', 0) == 'set_font_size'))
def set_font_size_message(_, update):
    chat_id = update.chat.id
    new_sentence = update.text
    re.sub(r'fontsize=.*:', f'fontsize={new_sentence}:', default_watermark_text)
    read_and_update_default_watermark(default_watermark_text)
    # Your logic to set font size goes here
    keyboard = [
        ["/set_default_watermark_text🔖"], 
        ['/set_font_size🈶', '/set_font_color™️'],
        ['/set_x↔️', '/set_y↕️'],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("Font size has been set successfully. ✅", reply_markup=keyboard_markup)



@app.on_message(filters.command(["set_font_color™️"]))
def set_font_color(_, update):
    chat_id = update.chat.id
    keyboard = [
        ["/Back"],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text('Enter Font size in this format (ex. black):\n colors: red, greeb, black, blue, white', reply_markup=keyboard_markup)
    chat_data[chat_id]['state'] = 'set_font_color'

@app.on_message(filters.create(lambda filter, client, update: chat_data.get(update.chat.id, {}).get('state', 0) == 'set_font_color'))
def set_font_color_message(_, update):
    chat_id = update.chat.id
    new_sentence = update.text
    re.sub(r'fontcolor=.*:', f'fontcolor={new_sentence}:', default_watermark_text)
    read_and_update_default_watermark(default_watermark_text)
    # Your logic to set font color goes here
    keyboard = [
        ["/set_default_watermark_text🔖"], 
        ['/set_font_size🈶', '/set_font_color™️'],
        ['/set_x↔️', '/set_y↕️'],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("Font color has been set successfully. ✅", reply_markup=keyboard_markup)



@app.on_message(filters.command(["/set_x↔️"]))
def set_x_coordinate(_, update):
    chat_id = update.chat.id
    keyboard = [
        ["/Back"],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text('Enter Font size in this format (ex. 20):', reply_markup=keyboard_markup)
    chat_data[chat_id]['state'] = 'set_x_coordinate'

@app.on_message(filters.create(lambda filter, client, update: chat_data.get(update.chat.id, {}).get('state', 0) == 'set_x_coordinate'))
def set_x_coordinate_message(_, update):
    chat_id = update.chat.id
    new_sentence = update.text
    re.sub(r'w-text_w-.*)', f'w-text_w-={new_sentence})', default_watermark_text)
    read_and_update_default_watermark(default_watermark_text)
    # Your logic to set X coordinate goes here
    keyboard = [
        ["/set_default_watermark_text🔖"], 
        ['/set_font_size🈶', '/set_font_color™️'],
        ['/set_x↔️', '/set_y↕️'],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("X coordinate has been set successfully. ✅", reply_markup=keyboard_markup)



@app.on_message(filters.command(["/set_y↕️"]))
def set_y_coordinate(_, update):
    chat_id = update.chat.id
    keyboard = [
        ["/Back"],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text('Enter Font size in this format (ex. 20):', reply_markup=keyboard_markup)
    chat_data[chat_id]['state'] = 'set_y_coordinate'

@app.on_message(filters.create(lambda filter, client, update: chat_data.get(update.chat.id, {}).get('state', 0) == 'set_y_coordinate'))
def set_y_coordinate_message(_, update):
    chat_id = update.chat.id
    new_sentence = update.text
    re.sub(r'h-text_h-=.*)', f'h-text_h-={new_sentence})', default_watermark_text)
    read_and_update_default_watermark(default_watermark_text)
    # Your logic to set Y coordinate goes here
    keyboard = [
        ["/set_default_watermark_text🔖"], 
        ['/set_font_size🈶', '/set_font_color™️'],
        ['/set_x↔️', '/set_y↕️'],
    ]
    keyboard_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True, one_time_keyboard=True)
    update.reply_text("Y coordinate has been set successfully. ✅", reply_markup=keyboard_markup)



@app.on_message(filters.command(["add_watermark💱"]))
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

    processing_message = update.reply_text("Watermark is processing...")
    add_watermark_with_ffmpeg(video_path, watermark_path, watermark_text)
    processing_message.edit_text("Watermark added with the specified text. You can now make other changes or send the video.")

    chat_data[chat_id]['action'] = 1

@app.on_message(filters.command(["trim_video✂️"]))
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

@app.on_message(filters.command(["process_and_send🎞"]))
def process_and_send(_, update):
    chat_id = update.chat.id
    video_path = chat_data[chat_id]["video_path"]
    video_processing = update.reply_text("Video is proccessing.")
    
    if chat_data[chat_id]['action'] == 0 :
        update.reply_text("No changes applied. Please start again.")
        return

    app.send_video(chat_id=chat_id, video=video_path)

    video_processing.delete()
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
        # Adding text watermark
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', default_watermark_text,
            '-c:a', 'copy',
            output_path
        ]
        

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
    read_and_update_default_watermark()
    app.run()
