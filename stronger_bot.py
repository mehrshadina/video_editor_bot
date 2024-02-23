from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardRemove
from pydub import AudioSegment
import subprocess
import os
import cv2
import re

API_KEY = 2215758
API_HASH = 'e18c19197e887478b8a77ae46f160847'
BOT_TOKEN = '6616025586:AAGivVAjd2ZhWk0KYHATKeMCSiEUCEPiZYc'
VIDEO_FOLDER = 'videos'

app = Client("video_processing_bot", api_id=API_KEY, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
    update.download(file_name=video_path)

    context = app.storage.setdefault(chat_id, {})
    context.update({"video_path": video_path, "action": set()})

    keyboard = [
        ["/add_watermark", "/trim_video"],
        ["/process_and_send"]
    ]
    update.reply_text("Now you can make various changes:", reply_markup=keyboard)

@app.on_message(filters.command(["add_watermark"]))
def add_watermark(_, update):
    update.reply_text("Please enter your watermark text.")

@app.on_message(filters.create(lambda _, __, message: message.text and not message.text.startswith('/')))
def get_watermark_text(_, update):
    chat_id = update.chat.id
    watermark_text = update.text

    app.session.get(chat_id)["watermark_text"] = watermark_text
    update.reply_text("Watermark added with the specified text. You can now make other changes or send the video.")

@app.on_message(filters.command(["trim_video"]))
def trim_video(_, update):
    update.reply_text("Please enter the start and end times in the 'MM:SS MM:SS' format (e.g., 01:30 05:30):")

@app.on_message(filters.create(lambda _, __, message: message.text and not message.text.startswith('/')))
def get_trim_time(_, update):
    chat_id = update.chat.id
    time_input = update.text
    match = re.match(r'(?P<start_minutes>\d+):(?P<start_seconds>\d+) (?P<end_minutes>\d+):(?P<end_seconds>\d+)', time_input)

    if match:
        minutes = int(match.group('start_minutes'))
        seconds = int(match.group('start_seconds'))
        start_time = minutes * 60 + seconds

        minutes = int(match.group('end_minutes'))
        seconds = int(match.group('end_seconds'))
        end_time = minutes * 60 + seconds

        app.session.get(chat_id)["trim_start_time"] = start_time
        app.session.get(chat_id)["trim_end_time"] = end_time

        update.reply_text("Video successfully trimmed. You can now make other changes or send the video.")
    else:
        update.reply_text('Incorrect input format. Please enter the time in "MM:SS" format.')

@app.on_message(filters.command(["process_and_send"]))
def process_and_send(_, update):
    chat_id = update.chat.id
    video_path = app.session.get(chat_id)["video_path"]
    action = app.session.get(chat_id).get("action")
    watermark_text = app.session.get(chat_id).get("watermark_text", "")
    start_time = app.session.get(chat_id).get("trim_start_time", "")
    end_time = app.session.get(chat_id).get("trim_end_time", "")

    if 'add_watermark' in action:
        add_watermark_with_opencv(video_path, watermark_text)

    if 'trim_video' in action:
        trim_video_with_opencv(video_path, start_time, end_time)

    if 'add_watermark' not in action and 'trim_video' not in action:
        update.reply_text("No changes applied. Please start again.")
        return

    app.send_video(chat_id=chat_id, video=video_path)

    reply_markup = ReplyKeyboardRemove()
    update.reply_text("Video successfully processed and sent.", reply_markup=reply_markup)

def add_watermark_with_opencv(video_path, watermark_text):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_path = video_path.replace('_video.mp4', '_out_video.mp4')
    audio_path = video_path.replace('_video.mp4', '_audio.mp3')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2
    font_thickness = 2
    font_color = (255, 255, 255)  # White color for the text

    # FFmpeg command to extract audio and concatenate with the video
    audio_extraction_cmd = [
        'ffmpeg',
        '-i', video_path,
        '-q:a', '0',
        '-map', 'a',
        audio_path
    ]
    subprocess.run(audio_extraction_cmd)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Add watermark text to the frame
        cv2.putText(frame, watermark_text, (20, height - 20), font, font_scale, font_color, font_thickness, cv2.LINE_AA)

        # Write the frame with watermark to the output video
        out.write(frame)

    cap.release()
    out.release()

    # FFmpeg command to mux the video with the extracted audio
    os.remove(video_path)
    audio_mux_cmd = [
        'ffmpeg',
        '-i', output_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-strict', 'experimental',
        video_path
    ]
    subprocess.run(audio_mux_cmd)

    os.remove(audio_path)
    os.remove(output_path)

def trim_video_with_opencv(video_path, start_time, end_time):
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_path = video_path.replace('_video.mp4', '_out_video.mp4')
    audio_path = video_path.replace('_video.mp4', '_audio.mp3')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    # FFmpeg command to extract audio and concatenate with the video
    audio_extraction_cmd = [
        'ffmpeg',
        '-i', video_path,
        '-ss', str(start_time),
        '-to', str(end_time),
        '-q:a', '0',
        '-map', 'a',
        audio_path
    ]
    subprocess.run(audio_extraction_cmd)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or cap.get(cv2.CAP_PROP_POS_FRAMES) > end_frame:
            break
        out.write(frame)

    cap.release()
    out.release()

    # FFmpeg command to mux the video with the extracted audio
    os.remove(video_path)
    audio_mux_cmd = [
        'ffmpeg',
        '-i', output_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-strict', 'experimental',
        video_path
    ]
    subprocess.run(audio_mux_cmd)

    os.remove(audio_path)
    os.remove(output_path)
    #context.user_data['video_path'] = video_path

if __name__ == "__main__":
    app.run()
