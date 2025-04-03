import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import google.generativeai as genai


app = Flask(__name__)

# Load environment variables
load_dotenv()

# Get API Key
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Make sure it's set in the .env file!")

# Function to extract YouTube Video ID
def get_video_id(url_link):
    """Extracts video ID from a YouTube URL."""
    if "watch?v=" in url_link:
        return url_link.split("watch?v=")[-1]
    elif "youtu.be/" in url_link:
        return url_link.split("youtu.be/")[-1]
    return None

# Function to fetch transcript with preferred languages
def get_transcript(video_id, languages=['en', 'nl']):
    """
    Fetches transcript for the given video ID in preferred languages.
    Default tries English, then Dutch.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return " ".join([line['text'] for line in transcript])
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"No transcript available: {e}")
        return None
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

# Function to generate response using Gemini AI
def generate_response(transcript_text, language='English'):
    """Generates a response using Gemini AI based on transcript."""
    if not transcript_text:
        return "No transcript available to generate response."

    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"Summarize or answer questions based on the following text in {language}:\n\n'{transcript_text}'"

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {e}"

# Main Execution
@app.route("/summarize", methods=["POST"])
def summarize_video():
    data = request.get_json()
    url = data.get("url")
    preferred_langs = data.get("languages", ['en', 'nl'])

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    video_id = get_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    transcript = get_transcript(video_id, languages=preferred_langs)
    if not transcript:
        return jsonify({"error": "No transcript available"}), 404

    lang_used = 'Dutch' if 'nl' in preferred_langs else 'English'
    summary = generate_response(transcript, language=lang_used)
    return jsonify({
        "video_id": video_id,
        "language": lang_used,
        "summary": summary
    })

# === Run the Flask App ===
if __name__ == "__main__":
    app.run(debug=True)