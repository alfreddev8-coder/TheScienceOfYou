# TheScienceOfYou Automation 🧬

Automated YouTube Shorts and Long-form content generation for the health science niche.

## 🚀 Features
- **AI Content**: Viral health science scripts via Groq (Llama 3.3).
- **Voiceover**: High-quality TTS via `edge-tts` with speed optimization.
- **Visuals**: Satisfying background footage from curated TikTok accounts and Pexels.
- **Assembly**: Fully automated video editing with captions, music, and SFX.
- **Upload**: Automatic YouTube upload with SEO-optimized titles and descriptions.

## 🛠️ Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/alfreddev8-coder/TheScienceOfYou.git
   cd TheScienceOfYou
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Requires FFmpeg installed on your system.*

3. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_key
   PIXABAY_API_KEY=your_pixabay_key
   PEXELS_API_KEY=your_pexels_key
   YOUTUBE_TOKEN_JSON={"your_token_data": "..."}
   ```

4. **Initialize Topic Bank**:
   Run this once to pre-load 300 viral health topics:
   ```bash
   python generate_topics.py
   ```

## 🎥 Usage

### Create a single Short
```bash
python main.py short
```

### Create a specific playlist Short
```bash
python main.py short body_science
```

### Batch create Shorts for today
```bash
python main.py batch_shorts
```

## 📂 Project Structure
- `core/`: Content generation and sourcing logic.
- `audio/`: TTS, music, and SFX management.
- `video/`: Footage sourcing, assembly, and captioning.
- `upload/`: YouTube API integration and comment bot.
- `data/`: Used topics, videos, and music tracking.

## 🛡️ Production & GitHub Actions
This project is optimized for GitHub Actions:
- **No YouTube Download**: Avoids server IP blocks by using TikTok/Pexels for footage.
- **Robust Fallbacks**: Graceful degradation if APIs (Google Trends, Quora) fail.
- **Strict Word Count**: Scripts are enforced between 185-200 words for optimal Shorts duration.

## ⚖️ License
MIT
