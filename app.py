import asyncio
import pyaudio
import sounddevice as sd
import numpy as np
import wave
import tempfile
import os
from RealtimeTTS import TextToAudioStream, ElevenlabsEngine
from config import ELEVENLABS_API_KEY, OPENAI_API_KEY
from ssml_generator import SSMLGenerator
from openai import OpenAI, AsyncOpenAI
import sounddevice as sd
import time

# Initialize the OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)
async_openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
ssml_generator = SSMLGenerator()

# Configure TTS engine
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY is not set. Please provide a valid API key.")

output_device = "CABLE Output"  # VB-Cable virtual device
tts_engine = ElevenlabsEngine(
    api_key=ELEVENLABS_API_KEY,
    voice="21m00Tcm4TlvDq8ikWAM",
    model="eleven_turbo_v2",  # Optimized model
)

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_data = []

    def __enter__(self):
        self.start_recording()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_recording()
        
    def callback(self, indata, frames, time, status):
        if self.recording:
            self.audio_data.append(indata.copy())
    
    def start_recording(self):
        self.recording = True
        self.audio_data = []
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self.callback
        )
        self.stream.start()
    
    def stop_recording(self):
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        self.recording = False
        return self.get_audio_data()
    
    def get_audio_data(self):
        if not self.audio_data:
            return None
        return np.concatenate(self.audio_data, axis=0)
    
    def save_to_wav(self, filename):
        audio_data = self.get_audio_data()
        if audio_data is not None:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            return True
        return False

async def transcribe_audio(audio_file):
    """Transcribe audio using Whisper API"""
    try:
        with open(audio_file, "rb") as file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=file
            )
        return transcript.text
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""

async def generate_response_stream(prompt, timeout=30):
    """Generate streaming response with timeout and error handling"""
    try:
        # Create a task for the streaming response
        response = await asyncio.wait_for(
            async_openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=150
            ),
            timeout=timeout
        )
        
        buffer = ""
        try:
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except asyncio.CancelledError:
            # Handle cancellation properly
            print("\nStreaming was cancelled - cleaning up resources")
            # Allow the exception to propagate after cleanup
            raise
        except Exception as e:
            print(f"\nError during streaming: {e}")
            
    except asyncio.TimeoutError:
        print(f"\nRequest timed out after {timeout} seconds")
    except Exception as e:
        print(f"\nError creating stream: {e}")

async def main():
    print("Initializing voice assistant...")
    
    # Initialize audio stream
    audio_stream = TextToAudioStream(
    tts_engine,
    log_characters=True  # Help with debugging
)
    
    # Create recorder
    recorder = AudioRecorder(sample_rate=16000, channels=1)
    
    try:
        while True:
            print("\nPress Enter to start speaking...")
            input()
            
            # Record audio
            with recorder:
                input("Recording... (Press Enter to stop)")
                
            # Transcribe
            audio_file = os.path.join(tempfile.gettempdir(), "recording.wav")
            recorder.save_to_wav(audio_file)
            transcript = await transcribe_audio(audio_file)
            if not transcript:
                print("No transcript detected. Please try again.")
                continue
                
            print(f"You said: {transcript}")
            
            # Process response
            print("AI: ", end="", flush=True)
            
            buffer = ""
            try:
                # Use a timeout for the entire streaming operation
                async for token in generate_response_stream(transcript):
                    print(token, end="", flush=True)
                    buffer += token
                    
                    # Process in chunks at natural breaks
                    if len(buffer) > 20 and any(p in token for p in ['.', '?', '!', ',', ';']):
                        ssml = ssml_generator.generate_ssml(buffer)
                        audio_stream.feed(ssml)
                        buffer = ""  # Clear buffer after processing
                
                # Process any remaining text
                if buffer:
                    ssml = ssml_generator.generate_ssml(buffer)
                    audio_stream.feed(ssml)
                
                # Small delay to ensure all audio is processed
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                print("\nResponse generation cancelled")
                # Properly handle remaining buffer if cancelled
                if buffer:
                    try:
                        ssml = ssml_generator.generate_ssml(buffer)
                        audio_stream.feed(ssml)
                    except:
                        pass
                raise  # Re-raise to propagate to the main loop
                
    except KeyboardInterrupt:
        print("\nExiting voice assistant...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        # Ensure proper cleanup
        print("Cleaning up resources...")
        # Wait a moment for any pending operations
        await asyncio.sleep(1)

    # Add this to your main function
    try:
        # Test audio output directly
        import pyttsx3
        test_engine = pyttsx3.init()
        test_engine.say("Testing audio output")
        test_engine.runAndWait()
        print("Basic audio test completed")
    except Exception as e:
        print(f"Audio test failed: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"\nProgram terminated due to error: {e}")
