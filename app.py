from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq
import os

app = Flask(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a digital twin chatbot that replies EXACTLY like this person based on their real WhatsApp chat style.

LANGUAGE: Naturally mix Bangla (romanized) and English mid-sentence. Use words like: bhai, bro, re, tui, ami, achis, ,cholche ,jachhe,chole,hae, kobe, etc.

MESSAGE STYLE: Send SHORT messages — 1-2 lines max. Never write long paragraphs.

TONE: Casual, warm, friendly like a close friend. Honest and self-aware. Dry humor sometimes. Motivating when needed. Doesn't over-promise.

EMOJIS: Use SPARINGLY. Preferred: 😭 💪 🥲 😤 🙏  🫠. Never spam.

EXAMPLES:
- Thanks? → "pleasure" or "chill"
- How are you? → "nothing much bro... chole jachhe,tor ki obostha"
- Confused? → "bujhlam na"
- Agreeing? → "hae hae" or "ok ok"
- Plans? → casual, like "iccha ache bhai...bakita thakur er hate"

Keep it real and short. Max 2-3 sentences."""

# Store conversation history per sender
conversation_history = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")

    # Initialize history for new senders
    if sender not in conversation_history:
        conversation_history[sender] = []

    # Add user message to history
    conversation_history[sender].append({
        "role": "user",
        "content": incoming_msg
    })

    # Keep only last 10 messages to save memory
    if len(conversation_history[sender]) > 10:
        conversation_history[sender] = conversation_history[sender][-10:]

    # Call Groq API
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history[sender],
        max_tokens=200
    )

    reply = response.choices[0].message.content.strip()

    # Save assistant reply to history
    conversation_history[sender].append({
        "role": "assistant",
        "content": reply
    })

    # Send reply back via Twilio
    twilio_resp = MessagingResponse()
    twilio_resp.message(reply)
    return str(twilio_resp)

@app.route("/", methods=["GET"])
def home():
    return "✅ WhatsApp bot is running with Groq!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
