from RealtimeTTS import SystemEngine, TextToAudioStream
engine = SystemEngine()
stream = TextToAudioStream(engine)
stream.feed("Test audio")
stream.play()
