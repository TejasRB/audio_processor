import re
import html

class SSMLGenerator:
    def __init__(self):
        self.buffer = ""
        
    def add_text(self, text):
        """Add text to the SSML buffer"""
        self.buffer += html.escape(text)
        
    def generate_ssml(self, text=None):
        """Generate SSML with natural speech patterns"""
        if text:
            self.add_text(text)
            
        # Apply SSML transformations
        text = self.buffer
        
        # Add pauses at punctuation
        text = text.replace('. ', '. <break time="300ms"/>')
        text = text.replace('? ', '? <break time="400ms"/>')
        text = text.replace('! ', '! <break time="400ms"/>')
        text = text.replace(', ', ', <break time="200ms"/>')
        
        # Add emphasis to important phrases (simplified)
        text = re.sub(r'\*([^*]+)\*', r'<emphasis level="moderate">\1</emphasis>', text)
        
        # Add occasional breathing for naturalness
        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts">
                <voice name="en-US-JennyNeural">
                    <prosody rate="0%" pitch="0%">
                        <mstts:express-as style="chat">
                            {text}
                        </mstts:express-as>
                    </prosody>
                </voice>
               </speak>"""
        
        # Reset buffer after generation
        self.buffer = ""
        return ssml
