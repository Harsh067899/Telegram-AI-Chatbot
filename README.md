# Telegram AI Chatbot

## Overview
This is an AI-powered Telegram chatbot that integrates user registration, AI chat, image/file analysis, and web search functionalities using Google Gemini API. It stores user data and chat history in MongoDB.

## Features

### 1. User Registration
- Saves `first_name`, `username`, and `chat_id` in MongoDB upon the first interaction.
- Requests the user's phone number using Telegram’s contact button and stores it in MongoDB.
- Sends a confirmation message after successful registration.

### 2. Gemini-Powered Chat
- Uses Google Gemini API (`google.generativeai`) to answer user queries.
- Stores the full chat history (user input + bot response) in MongoDB with timestamps.

### 3. Image/File Analysis
- Accepts images/files (JPG, PNG, PDF) from users.
- Uses Gemini AI to analyze and describe the content.
- Replies with the analysis and saves file metadata (filename, description) in MongoDB.

### 4. Web Search
- Users can enter `/websearch` to initiate a web search.
- The bot queries the web and provides an AI-generated summary of the top search results.
- Includes relevant web links for further reading.

## Bonus Features (Innovation)
- **Sentiment Analysis**: Detects user sentiment in chats and provides appropriate responses.
- **Auto-Translation**: Supports multilingual interactions using AI translation.
- **User Analytics Dashboard**: Displays user statistics, chat history trends, and file analysis logs.

## Tech Stack
- **Backend**: Python (Flask/FastAPI)
- **Database**: MongoDB
- **AI Model**: Google Gemini API
- **Messaging**: Telegram Bot API
- **Web Scraping**: AI-powered search agent

## Setup & Installation
### Prerequisites
- Python 3.8+
- MongoDB (local or cloud instance)
- Telegram Bot Token
- Google Gemini API Key

### Installation Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/telegram-ai-chatbot.git
   cd telegram-ai-chatbot
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```sh
   TELEGRAM_BOT_TOKEN=<your_bot_token>
   MONGO_URI=<your_mongo_uri>
   GEMINI_API_KEY=<your_gemini_api_key>
   ```
4. Run the bot:
   ```sh
   python bot.py
   ```

## Deployment
- Deploy on **Heroku**, **AWS Lambda**, or **Google Cloud Run**.
- Use **Docker** for containerized deployment.

## Usage
- Start the bot in Telegram using `/start`.
- Register and provide your contact number.
- Ask questions using natural language.
- Upload images/files for analysis.
- Perform web searches with `/websearch`.

## Demo
- **GitHub Repository**: [Your Repo Link]
- **Loom Video Demo**: [Your Loom Video Link]

## Contributions
Feel free to contribute by submitting pull requests.

## License
This project is licensed under the MIT License.

---
Developed by hARSH SAHu 🚀

