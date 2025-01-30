from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import pymongo
import google.generativeai as genai
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, PhotoSize
from PIL import Image, UnidentifiedImageError
import mimetypes
import pytesseract
import io
import fitz
from config import BOT_TOKEN, MONGO_URI, DB_NAME, GEMINI_API_KEY
import requests
import nltk
from textblob import TextBlob

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]
chats_collection = db["chats"]  # AI chat history
file_analysis_collection = db["file_analysis"]  # File metadata storage

nltk.download('punkt_tab')


def analyze_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    
    if polarity > 0:
        return "positive"
    elif polarity < 0:
        return "negative"
    else:
        return "neutral"


# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # Updated to latest model

# Handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    username = update.message.chat.username

    # Check if user exists
    user = users_collection.find_one({"chat_id": chat_id})

    if not user:
        # Save user details without phone number
        users_collection.insert_one({
            "chat_id": chat_id,
            "first_name": first_name,
            "username": username,
            "phone_number": None
        })

        # Ask user for phone number
        keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text("Please share your phone number to complete registration.", reply_markup=reply_markup)
    
    else:
        await update.message.reply_text(f"Hello again, {first_name}! You're already registered.")

# Handle Phone Number Collection
async def collect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact = update.message.contact
    chat_id = update.message.chat_id

    if contact and contact.user_id == update.message.from_user.id:  # Ensure it's the user's own number
        phone_number = contact.phone_number

        # Update user in MongoDB
        users_collection.update_one({"chat_id": chat_id}, {"$set": {"phone_number": phone_number}})

        await update.message.reply_text("✅ Registration complete! Thank you.")
    else:
        await update.message.reply_text("⚠️ Please share your own phone number.")

# Handle AI Chat using Gemini
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    chat_id = update.message.chat_id
    sentiment = analyze_sentiment(user_input)

    await update.message.reply_text(f"🤖Thinking...")
    await update.message.reply_text(f"🤖 Analyzing sentiment: {sentiment.capitalize()}...")

    try:
        # Call Gemini AI API
        response = model.generate_content(user_input)
        bot_response = response.text if response.text else "⚠️ Sorry, I couldn't understand that."

        # Store chat history in MongoDB
         # Modify response based on sentiment
        if sentiment == "negative":
            bot_response = "😞 I'm here for you. " + bot_response
        elif sentiment == "positive":
            bot_response = "😊 That sounds great! " + bot_response
        
        
        chats_collection.insert_one({
            "chat_id": chat_id,
            "user_input": user_input,
            "bot_response": bot_response,
            "sentiment": sentiment
        })

        # Send response to user
        await update.message.reply_text(bot_response)

    except Exception as e:
        print("Error:", str(e))
        await update.message.reply_text("❌ AI service is currently unavailable. Please try again later.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Handle both documents and photos in Telegram
    file = update.message.document or (update.message.photo[-1] if update.message.photo else None)
    chat_id = update.message.chat_id

    if not file:
        await update.message.reply_text("⚠️ No valid file received. Please send an image or document.")
        return

    file_id = file.file_id
    file_name = file.file_name if hasattr(file, "file_name") else "image.jpg"

    # Get File from Telegram Server
    file_info = await context.bot.get_file(file_id)
    file_path = f"downloads/{file_name}"

    os.makedirs("downloads", exist_ok=True)
    await file_info.download_to_drive(file_path)

    await update.message.reply_text("🔍 Analyzing the file...")

    try:
        analysis_result = ""

        # Check if the file is an image (whether sent as document or photo)
        if isinstance(file, PhotoSize) or file.mime_type.startswith("image/"):
            with open(file_path, "rb") as f:
                img = Image.open(io.BytesIO(f.read()))  # Convert bytes to PIL Image
            
            # Use Tesseract OCR to extract text from the image
            extracted_text = pytesseract.image_to_string(img)

            if extracted_text.strip() == "":
                analysis_result = "⚠️ No text found in the image."
            else:
                # Send extracted text to Gemini's text model for analysis
                response = model.generate_content(extracted_text)
                analysis_result = response.text if hasattr(response, "text") else "⚠️ Could not analyze the image."

        # Check if the file is a text document (PDF, TXT, etc.)
        elif file.mime_type == "application/pdf":
            with fitz.open(file_path) as doc:
                text = "\n".join([page.get_text("text") for page in doc])

            response = model.generate_content(text)
            analysis_result = response.text if hasattr(response, "text") else "⚠️ Could not analyze the document."

        elif file.mime_type == "text/plain":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            response = model.generate_content(text)
            analysis_result = response.text if hasattr(response, "text") else "⚠️ Could not analyze the document."

        # Store metadata in MongoDB
        file_analysis_collection.insert_one({
            "chat_id": chat_id,
            "file_name": file_name,
            "analysis": analysis_result
        })

        await update.message.reply_text(f"📄 **File:** {file_name}\n\n📝 **Analysis:** {analysis_result}")

    except Exception as e:
        print("Error:", str(e))
        await update.message.reply_text("❌ Error processing the file. Please try again later.")

    # Cleanup: Remove downloaded file
    os.remove(file_path)
    

# Web search function using Google's Custom Search JSON API
def perform_web_search(query: str):
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={CX}"
    response = requests.get(search_url)
    if response.status_code == 200:
        search_results = response.json().get("items", [])
        return [(result["title"], result["link"]) for result in search_results]
    else:
        return None

# Handle /websearch command
async def websearch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔍 Please enter your search query:")

# Handle user input for search query
async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_query = update.message.text
    chat_id = update.message.chat_id

    await update.message.reply_text("🔍 Searching the web...")

    # Perform web search
    search_results = perform_web_search(user_query)

    if not search_results:
        await update.message.reply_text("❌ No results found. Please try again later.")
        return

    # Summarize search results with AI
    search_summary = "\n".join([f"**{title}**: {link}" for title, link in search_results])
    summary_response = model.generate_content(f"Summarize these search results: {search_summary}")
    summary_text = summary_response.text if hasattr(summary_response, "text") else "⚠️ Could not summarize the search results."

    # Send summary back to the user
    await update.message.reply_text(f"🔍 **Search Results Summary**:\n\n{summary_text}")

# Start the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("websearch", websearch))

    app.add_handler(MessageHandler(filters.CONTACT, collect_phone))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # AI Chat
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file))  # File Analysis

    print("Bot is running...")
    app.run_polling()
