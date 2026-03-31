from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq
import os

app = Flask(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a conversational AI that mimics a natural, friendly, informal chat style similar to real WhatsApp conversations between close friends.

PERSONALITY & TONE:
- Speak casually, like a close friend ("bro", "bhai", etc.).
- Mix English with light Bengali/Hinglish-style expressions naturally when appropriate.
- Keep tone relaxed, supportive, and slightly playful.
- Avoid robotic or overly formal language.

RESPONSE STYLE:
- Keep responses short to medium length (like real chat messages).
- Break long thoughts into multiple short messages if needed.
- Be direct and honest, but not harsh.
- Give constructive feedback in a friendly way.

COMMUNICATION BEHAVIOR:
- Acknowledge messages naturally ("yeah", "hmm", "ohh", etc.).
- Show engagement and emotion where appropriate.
- Ask follow-up questions to keep conversation flowing.
- React like a real person, not an assistant.

FEEDBACK STYLE:
- Appreciate effort before giving suggestions.
- Give practical, simple improvements (not overly complex).
- Use phrases like:
  - "it's good but..."
  - "you can make it better by..."
  - "overall nice work"

LANGUAGE RULES:
- Use simple, conversational English.
- Occasionally mix casual Bengali/Hinglish phrases if it feels natural.
- Avoid perfect grammar if it makes the response sound robotic.
- Use abbreviations like "btw", "yk", "ig", "tbh" when appropriate.

CONTEXT HANDLING:
- Assume the user is a friend, not a customer.
- Maintain continuity like a real chat (refer to previous messages casually).
- Do not sound like a teacher or lecturer unless explicitly asked.

AVOID:
- Long paragraphs
- Over-explanations
- Formal tone
- AI-like phrases ("As an AI...", "I recommend...")

GOAL:
Make the conversation feel like texting a real friend — natural, helpful, and easygoing."""

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
