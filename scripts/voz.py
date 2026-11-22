# Narrate one line with a Microsoft neural voice (edge-tts, free) and keep the time of every word for the captions.
# Writes <out>.mp3 and <out>.words.json ([{"text", "start", "end"}] in seconds).
# usage: python3 voz.py <es|en> <out_base> "<text>" [voice]
import asyncio, json, sys
import edge_tts

VOICES = {"es": "es-MX-JorgeNeural", "en": "en-US-BrianMultilingualNeural"}
RATE = {"es": "+6%", "en": "+4%"}  # a touch faster than default: shorts reward pace

async def main(lang, out, text, voice=None):
    com = edge_tts.Communicate(text, voice or VOICES[lang], rate=RATE[lang], boundary="WordBoundary")
    words = []
    with open(out + ".mp3", "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s = ch["offset"] / 1e7; words.append({"text": ch["text"], "start": s, "end": s + ch["duration"] / 1e7})
    if not words: sys.exit(f"edge-tts no devolvió tiempos de palabra para: {text[:60]}")
    json.dump(words, open(out + ".words.json", "w"), ensure_ascii=False)

if __name__ == "__main__":
    for attempt in range(3):  # the service drops a connection now and then
        try: asyncio.run(main(*sys.argv[1:5])); break
        except edge_tts.exceptions.NoAudioReceived:
            if attempt == 2: raise
