import asyncio
import edge_tts

async def list_hindi_voices():
    voices = await edge_tts.list_voices()
    print(f"Total available voices: {len(voices)}")
    indian_voices = [v for v in voices if 'IN' in v['Locale'] or 'hi' in v['Locale'].lower()]
    print("\n--- Indian & Hindi Voices ---")
    for v in indian_voices:
        print(f"ID: {v['ShortName']:<30} Gender: {v['Gender']:<8} Locale: {v['Locale']:<10} Name: {v.get('FriendlyName', '')}")

    print("\n--- Generating Hindi Test Audio with hi-IN-SwaraNeural ---")
    test_text_hindi = "नमस्ते! मैं आपकी क्या सहायता कर सकती हूँ? हमारे व्हाट्सएप ऑटोमेशन समाधानों में आपका स्वागत है।"
    communicate = edge_tts.Communicate(test_text_hindi, voice="hi-IN-SwaraNeural")
    await communicate.save("test_swara_hindi.mp3")
    print("Saved test_swara_hindi.mp3 successfully!")

    print("\n--- Generating Hinglish Test Audio with hi-IN-SwaraNeural ---")
    test_text_hinglish = "Namaste! Welcome to Qloudflow WhatsApp Manager. Aapka order successfully confirm ho gaya hai."
    communicate2 = edge_tts.Communicate(test_text_hinglish, voice="hi-IN-SwaraNeural")
    await communicate2.save("test_swara_hinglish.mp3")
    print("Saved test_swara_hinglish.mp3 successfully!")

    print("\n--- Generating Hindi Test Audio with hi-IN-MadhurNeural (Male) ---")
    communicate3 = edge_tts.Communicate(test_text_hindi, voice="hi-IN-MadhurNeural")
    await communicate3.save("test_madhur_hindi.mp3")
    print("Saved test_madhur_hindi.mp3 successfully!")

if __name__ == "__main__":
    asyncio.run(list_hindi_voices())
