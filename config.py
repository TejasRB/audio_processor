import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("API_KEY_OPENAI")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# TTS Configuration
DEFAULT_VOICE = "eleven_monolingual_v1"  # For ElevenLabs
STREAM_CHUNK_SIZE = 1024  # Audio streaming chunk size

# Audio optimizations
AUDIO_CONFIG = {
    "input_device": "CABLE Input",  # VB-Cable virtual device
    "output_device": "CABLE Output",
    "chunk_size": 512,
    "sample_rate": 24000,
    "dtype": "int16"
}

# LLM streaming config
STREAMING_CONFIG = {
    "max_buffer_size": 15,  # Words
    "punctuation_trigger": ['.', '?', '!', ',', ';'],
    "min_chunk_size": 3     # Words
}
