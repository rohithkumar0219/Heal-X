# Multimodal AI Healthcare Assistant 🏥

A full-stack AI-powered healthcare assistant that combines text, image, and voice inputs to provide educational health information.

## ⚠️ Important Disclaimer

**This system is for educational purposes only and is NOT a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.**

## 🌟 Features

- **Text Queries**: Ask health-related questions in natural language
- **Image Analysis**: Upload medical images for AI-powered analysis
- **Voice Input**: Record voice queries for hands-free interaction
- **Multimodal Fusion**: Combine text, image, and voice for comprehensive analysis
- **Text-to-Speech**: Listen to AI responses
- **Modern UI**: Clean, professional interface inspired by contemporary AI assistants

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI (Python)
- **AI Models**:
  - GPT-4 Turbo for medical query processing
  - GPT-4 Vision for medical image analysis
  - Whisper for speech-to-text
  - gTTS for text-to-speech

### Frontend
- HTML5, CSS3, JavaScript (Vanilla)
- Responsive design
- Modern medical-themed UI

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Modern web browser with microphone support

## 🚀 Setup Instructions

### 1. Clone or Navigate to Project Directory

```bash
cd d:\heal_x
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-api-key-here
```

### 6. Run the Application

```bash
cd backend
python main.py
```

The application will start at `http://localhost:8000`

## 📡 API Endpoints

### Health Check
```
GET /api/health
```

### Text Query
```
POST /api/query
Content-Type: application/json

{
  "query": "What are the symptoms of flu?",
  "include_audio": false
}
```

### Image Analysis
```
POST /api/analyze-image
Content-Type: multipart/form-data

image: <file>
query: "What could this rash be?"
include_audio: false
```

### Voice Query
```
POST /api/voice-query
Content-Type: multipart/form-data

audio: <file>
include_audio: true
```

### Multimodal Query
```
POST /api/multimodal-query
Content-Type: multipart/form-data

query: "I have a headache"
image: <file>
audio: <file>
include_audio: false
```

### Get Audio Response
```
GET /api/audio/{filename}
```

## 🧪 Testing

### Test Text Query
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are symptoms of common cold?", "include_audio": false}'
```

### Test Image Analysis
```bash
curl -X POST http://localhost:8000/api/analyze-image \
  -F "image=@path/to/image.jpg" \
  -F "query=What could this be?" \
  -F "include_audio=false"
```

## 📁 Project Structure

```
heal_x/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── routes/
│   │   └── health_routes.py    # API endpoints
│   ├── services/
│   │   ├── llm_service.py      # LLM integration
│   │   ├── vision_service.py   # Image analysis
│   │   ├── speech_service.py   # Speech-to-text
│   │   └── tts_service.py      # Text-to-speech
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   ├── utils/
│   │   ├── logger.py           # Logging utility
│   │   └── file_handler.py     # File management
│   └── static/
│       └── audio/              # Generated audio files
├── frontend/
│   ├── index.html              # Main UI
│   ├── styles.css              # Styling
│   └── script.js               # Frontend logic
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
└── README.md                   # This file
```

## 🔒 Security Features

- File type validation
- File size limits
- Secure file handling
- CORS configuration
- Input sanitization
- Temporary file cleanup

## 🎨 UI Features

- Modern, clean design
- Responsive layout
- Loading states
- Error handling
- Audio visualization
- Image preview
- Prominent medical disclaimer

## 🛠️ Development

### API Documentation

Access interactive API documentation:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### Logs

Application logs are stored in the `logs/` directory.

## 📝 License

This project is for educational purposes only.

## 🤝 Contributing

This is a demonstration project. For production use, additional security measures, error handling, and medical compliance features would be required.

## ⚡ Performance Notes

- Image preprocessing reduces API costs
- Temporary file cleanup prevents disk bloat
- Async operations for better performance
- Structured logging for debugging

## 🔮 Future Enhancements

- User authentication
- Conversation history
- Multiple language support
- Advanced medical image analysis
- Integration with health databases
- Appointment scheduling
- Symptom tracking

## 📞 Support

For issues or questions, please refer to the API documentation or check the application logs.

---

**Remember**: This is an educational tool. Always consult healthcare professionals for medical advice.
