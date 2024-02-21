from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from pydub import AudioSegment
from pydub.generators import WhiteNoise
import subprocess
import os
import cv2
import re

TOKEN = '6616025586:AAGivVAjd2ZhWk0KYHATKeMCSiEUCEPiZYc'
VIDEO_FOLDER = 'videos'

def start(update, context):
    update.message.reply_text("Hi! To send a video and apply changes, use the /process_video command.")

def process_video(update, context):
    context.user_data['action'] = set()
    update.message.reply_text("Please send your video.")
    return "get_video"

def get_video(update, context):
    chat_id = update.message.chat_id
    video_file = context.bot.get_file(update.message.video.file_id)
    video_path = os.path.join(VIDEO_FOLDER, f"{chat_id}_video.mp4")
    video_file.download(video_path)
    context.user_data['video_path'] = video_path

    keyboard = [
        ['/add_watermark', '/trim_video'],
        ['/process_and_send']
    ]
    reply_markup = {'keyboard': keyboard, 'resize_keyboard': True, 'one_time_keyboard': True}
    update.message.reply_text("Now you can make various changes:", reply_markup=reply_markup)
    return "options"

def add_watermark(update, context):
    context.user_data['action'].add('add_watermark')
    update.message.reply_text("Please enter your watermark text.")
    return "get_watermark_text"

def get_watermark_text(update, context):
    context.user_data['watermark_text'] = update.message.text
    update.message.reply_text("Watermark added with the specified text. You can now make other changes or send the video.")
    return "options"

def trim_video(update, context):
    context.user_data['action'].add('trim_video')
    update.message.reply_text("Please enter the start and end times in the 'MM:SS MM:SS' format (e.g., 01:30 05:30):")
    return "get_trim_time"

def get_trim_time(update, context):
    time_input = update.message.text
    match = re.match(r'(?P<start_minutes>\d+):(?P<start_seconds>\d+) (?P<end_minutes>\d+):(?P<end_seconds>\d+)', time_input)

    if match:
        minutes = int(match.group('start_minutes'))
        seconds = int(match.group('start_seconds'))
        start_time = minutes * 60 + seconds

        minutes = int(match.group('end_minutes'))
        seconds = int(match.group('end_seconds'))
        end_time = minutes * 60 + seconds

        #video_path = context.user_data['video_path']
        #trim_video_with_opencv(video_path, start_time, context)
        context.user_data['trim_start_time'] = start_time
        context.user_data['trim_end_time'] =  end_time

        update.message.reply_text("Video successfully trimmed. You can now make other changes or send the video.")
        return "options"# FFmpeg command to mux the video with the extracted audio
   
    else:
        update.message.reply_text('Incorrect input format. Please enter the time in "MM:SS" format.')
        return "get_trim_time"

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
    font_scale = 1
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
        cv2.putText(frame, watermark_text, (10, height - 10), font, font_scale, font_color, font_thickness, cv2.LINE_AA)

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

def process_and_send(update, context):
    video_path = context.user_data['video_path']
    action = context.user_data.get('action')
    watermark_text = context.user_data.get('watermark_text', '')
    start_time = context.user_data.get('trim_start_time', '')
    end_time = context.user_data.get('trim_end_time', '')

    if 'add_watermark' in action:
        add_watermark_with_opencv(video_path, watermark_text)

    if 'trim_video' in action:
        trim_video_with_opencv(video_path, start_time, end_time)

    #print(action)
    if 'add_watermark' not in action and 'trim_video' not in action:
        update.message.reply_text("No changes applied. Please start again.")
        return ConversationHandler.END

    #output_path = video_path.replace('_input_video.mp4', '_processed_video.mp4')
    #video.write_videofile(output_path, codec='libx264', audio_codec='aac')

    context.bot.send_video(chat_id=update.message.chat_id, video=open(video_path, 'rb'))

    reply_markup = ReplyKeyboardRemove()
    update.message.reply_text("Video successfully processed and sent.", reply_markup=reply_markup)
    return ConversationHandler.END


def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('process_video', process_video)],
        states={
            "get_video": [MessageHandler(Filters.video, get_video)],
            "options": [
                CommandHandler('process_and_send', process_and_send),
                CommandHandler("add_watermark", add_watermark),
                CommandHandler("trim_video", trim_video)
            ],
            "get_watermark_text": [MessageHandler(Filters.text & ~Filters.command, get_watermark_text)],
            "trim_video": [MessageHandler(Filters.command, trim_video)],
            "get_trim_time": [MessageHandler(Filters.text & ~Filters.command, get_trim_time)],
            #"process_and_send": [MessageHandler(Filters.text & ~Filters.command, process_and_send)],
        },
        fallbacks=[]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
