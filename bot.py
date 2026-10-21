import os
import subprocess
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup taaki Render logs mein error dekh sakein
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Environment Variable se token secure tareeqe se read karna
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = "https://teraapi.synaxbots.workers.dev/?url="

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Salam Bhai!*\n\nMujhe TeraBox ka video link bhejo, main use bypass kar ke direct video file aapko send karunga. 🎬",
        parse_mode="Markdown"
    )

async def handle_terabox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN environment variable missing hai!")
        await update.message.reply_text("❌ Server config error: Bot token setup nahi hai.")
        return

    user_link = update.message.text.strip()
    chat_id = update.message.chat_id
    
    # Links validation
    if "terabox" not in user_link and "1024terabox" not in user_link:
        await update.message.reply_text("⚠️ Bhai, yeh valid TeraBox link nahi lag raha.")
        return
        
    status_msg = await update.message.reply_text("⏳ *Link bypass ho raha hai... Thoda intezar karein.*", parse_mode="Markdown")
    
    try:
        # Worker API hit karna
        api_url = f"{API_BASE_URL}{user_link}"
        response = requests.get(api_url).json()
        
        if not response.get("ok"):
            await status_msg.edit_text("❌ API se contact nahi ho saka ya link expire ho chuka hai.")
            return
            
        title = response.get("title", "video.mp4")
        if not title.endswith(".mp4"):
            title += ".mp4"
            
        stream_url = response.get("stream_url")
        size_str = response.get("size_str", "Unknown")
        
        if not stream_url:
            await status_msg.edit_text("❌ Is file ka streaming link available nahi hai.")
            return
            
        await status_msg.edit_text(f"📦 *File Found:* `{title}` ({size_str})\n📥 *Server par processing shuru ho gayi hai...*")
        
        # Temp filename generate karna conflict se bachne ke liye
        output_filename = f"video_{chat_id}.mp4"
        
        # FFmpeg optimization flags fast streaming aur copy ke liye
        ffmpeg_command = [
            'ffmpeg', '-y', 
            '-i', stream_url, 
            '-c', 'copy', 
            '-bsf:a', 'aac_adtstoasc', 
            '-movflags', 'faststart', 
            output_filename
        ]
        
        # Background mein convert run karna
        process = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            await status_msg.edit_text("❌ Video conversion (FFmpeg) block ho gayi.")
            return

        await status_msg.edit_text("⚡ *Telegram par upload ho raha hai...*")
        
        # Final video user ko bhejna
        with open(output_filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"✅ *TeraBox Downloader*\n\n📂 *Name:* `{title}`\n⚖️ *Size:* {size_str}",
                parse_mode="Markdown"
            )
            
        # Storage clear karna taaki Render container crash na ho
        if os.path.exists(output_filename):
            os.remove(output_filename)
        await status_msg.delete()
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text(f"⚠️ Error aaya hai bhai: `{str(e)}`", parse_mode="Markdown")

def main():
    if not BOT_TOKEN:
        print("CRITICAL ERROR: BOT_TOKEN Environment Variable set nahi hai!")
        return
        
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_terabox))
    print("Bot is up and running...")
    app.run_polling()

if __name__ == '__main__':
    main()
    