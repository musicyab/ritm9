from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from mutagen.id3 import ID3, TIT2, TPE1, TALB
from mutagen.mp3 import MP3
from pydub import AudioSegment
from io import BytesIO
import os
import schedule
import time
from threading import Thread

TOKEN = "7636768416:AAGE-QJYZt_1tW6z6kM_XDfh0eA-RNM4FWs"
CHANNEL_ID = "https://t.me/+YbRc9-onuvNiYTM8"  # شناسه کانال
scheduled_posts = []

def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! فایل موسیقی رو ارسال کن.")

def edit_id3_tags(file_path, title, artist, album):
    audio = MP3(file_path, ID3=ID3)
    audio["TIT2"] = TIT2(encoding=3, text=title)
    audio["TPE1"] = TPE1(encoding=3, text=artist)
    audio["TALB"] = TALB(encoding=3, text=album)
    audio.save()

def create_sample(file_path):
    audio = AudioSegment.from_file(file_path)
    sample = audio[:30000]  # 30 ثانیه
    sample_path = "sample.mp3"
    sample.export(sample_path, format="mp3")
    return sample_path

def handle_audio(update: Update, context: CallbackContext):
    file = update.message.audio.get_file()
    file_path = "temp.mp3"
    file.download(file_path)

    update.message.reply_text("لطفاً عنوان، هنرمند و آلبوم رو به ترتیب ارسال کن، هر کدوم رو با Enter جدا کن.")

    def process_tags(update: Update, context: CallbackContext):
        user_input = update.message.text.split("\n")
        if len(user_input) < 3:
            update.message.reply_text("لطفاً اطلاعات کامل رو ارسال کن!")
            return

        title, artist, album = user_input
        edit_id3_tags(file_path, title, artist, album)

        sample_path = create_sample(file_path)
        update.message.reply_text("فایل ویرایش شد. لطفاً زمان ارسال به کانال (به فرمت HH:MM) رو ارسال کن.")

        def schedule_post(update: Update, context: CallbackContext):
            time_str = update.message.text
            try:
                hour, minute = map(int, time_str.split(":"))
                schedule_time = f"{hour:02}:{minute:02}"

                def post_to_channel():
                    bot = Bot(token=TOKEN)
                    with open(sample_path, "rb") as sample_file:
                        bot.send_audio(chat_id=CHANNEL_ID, audio=sample_file, caption=f"{title} - {artist}")

                schedule.every().day.at(schedule_time).do(post_to_channel)
                scheduled_posts.append(post_to_channel)

                update.message.reply_text(f"فایل در ساعت {schedule_time} به کانال ارسال خواهد شد.")
            except Exception as e:
                update.message.reply_text("فرمت زمان اشتباه است. لطفاً دوباره ارسال کن.")

        context.bot.add_handler(MessageHandler(Filters.text & ~Filters.command, schedule_post))
        context.bot.remove_handler(MessageHandler(Filters.text & ~Filters.command, process_tags))

    context.bot.add_handler(MessageHandler(Filters.text & ~Filters.command, process_tags))

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.audio, handle_audio))

    Thread(target=run_schedule).start()
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
