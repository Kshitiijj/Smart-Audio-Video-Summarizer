from flask import Flask, render_template, request, jsonify
from pydub import AudioSegment
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import os
import nltk
import subprocess
from yt_dlp import YoutubeDL
import whisper  # Use Whisper for speech recognition

# Ensure NLTK data is downloaded
nltk.download('punkt')
nltk.download('punkt_tab')

app = Flask(__name__)                   

# Function to convert MP3 to WAV
def convert_audio_to_wav(audio_path):
    if audio_path.endswith(".mp3"):
        sound = AudioSegment.from_mp3(audio_path)
        audio_path = audio_path.replace(".mp3", ".wav")
        sound.export(audio_path, format="wav")
    return audio_path

# Function to extract audio from video using ffmpeg
def extract_audio_from_video(video_path):
    audio_path = video_path.replace(".mp4", ".wav")
    command = f"ffmpeg -i {video_path} -q:a 0 -map a {audio_path} -y"
    subprocess.call(command, shell=True)
    return audio_path

# Function to download audio from YouTube using yt-dlp
def download_youtube_audio(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': 'temp_audio.%(ext)s',
    }
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=True)
        audio_path = ydl.prepare_filename(info_dict).replace(".webm", ".wav").replace(".mp4", ".wav")
    return audio_path

# Function to transcribe audio using Whisper
def transcribe_audio(audio_path):
    model = whisper.load_model("base")  # Use "base", "small", "medium", or "large"
    result = model.transcribe(audio_path)
    return result["text"]

# Function to clean text
def clean_text(text):
    fillers = ["uh", "um", "like", "you know", "so", "actually"]
    cleaned = re.sub(r'\b(' + '|'.join(fillers) + r')\b', '', text, flags=re.IGNORECASE)
    return cleaned

# Function to summarize text
def summarize_text(text, num_sentences=3):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, num_sentences)
    return " ".join(str(sentence) for sentence in summary)

# Function to extract keywords
def extract_keywords(text, num_keywords=5):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=num_keywords)
    tfidf_matrix = vectorizer.fit_transform([text])
    return vectorizer.get_feature_names_out()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'youtubeLink' in request.form and request.form['youtubeLink'].strip():
        youtube_url = request.form['youtubeLink']
        file_path = download_youtube_audio(youtube_url)
        text = transcribe_audio(file_path)
        os.remove(file_path)
    elif 'audioFile' in request.files:
        file = request.files['audioFile']
        if file.filename == '':
            return jsonify({"error": "No selected file"})
        
        file_path = f"temp_audio.{file.filename.split('.')[-1]}"
        file.save(file_path)

        if file_path.endswith(".mp4"):
            file_path = extract_audio_from_video(file_path)

        text = transcribe_audio(file_path)
        os.remove(file_path)
    else:
        return jsonify({"error": "No file or link provided"})

    if "Could not" in text:
        return jsonify({"error": text})
    
    cleaned_text = clean_text(text)
    summary = summarize_text(cleaned_text)
    keywords = extract_keywords(cleaned_text)

    return jsonify({
        "transcribedText": text,
        "summary": summary,
        "keywords": ", ".join(keywords)
    })

if __name__ == '__main__':
    app.run(debug=True)