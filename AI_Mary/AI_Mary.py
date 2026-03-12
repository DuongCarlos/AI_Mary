import speech_recognition as sr
from faster_whisper import WhisperModel
from googletrans import Translator
from gtts import gTTS
import pygame
import os
import io

# =====================================================================
# ⚙️ KHU VỰC CÀI ĐẶT THÔNG SỐ (BẠN CHỈNH SỬA Ở ĐÂY)
# =====================================================================
WHISPER_MODEL_SIZE = "base"  # Chọn: "tiny", "base", "small", "medium", "large". Máy yếu chọn base/tiny.
COMPUTE_DEVICE = "cpu"       # Thay bằng "cuda" nếu máy bạn có card rời NVIDIA.
COMPUTE_TYPE = "int8"        # Dùng "float16" nếu chạy trên GPU (cuda) để mượt hơn.

RECORD_TIMEOUT = 5           # Thời gian tối đa (giây) để ghi âm 1 câu trước khi dịch. (Chỉnh nhỏ thì dịch nhanh, nhưng dễ đứt câu).
PHRASE_TIME_LIMIT = 5        # Thời lượng ngắt câu mặc định.
ENERGY_THRESHOLD = 300       # Độ nhạy âm thanh. Môi trường ồn thì tăng lên (vd: 1000).

TARGET_LANG = "vi"           # Ngôn ngữ muốn dịch ra (vi = Tiếng Việt).
# =====================================================================

# Khởi tạo các công cụ
print("⏳ Đang tải mô hình AI Whisper (có thể mất một lúc ở lần đầu tiên)...")
audio_model = WhisperModel(WHISPER_MODEL_SIZE, device=COMPUTE_DEVICE, compute_type=COMPUTE_TYPE)
translator = Translator()
recognizer = sr.Recognizer()
recognizer.energy_threshold = ENERGY_THRESHOLD

# Khởi tạo công cụ phát âm thanh (pygame)
pygame.mixer.init()

def play_audio(text):
    """Hàm chuyển chữ thành giọng nói và phát ra loa"""
    try:
        # Tạo file âm thanh TTS
        tts = gTTS(text=text, lang=TARGET_LANG, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Phát âm thanh
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy(): 
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Lỗi phát âm thanh: {e}")

def main():
    # Sử dụng thiết bị ghi âm mặc định (Hãy chắc chắn bạn đã bật Stereo Mix trên Windows)
    with sr.Microphone() as source:
        print("\n🎧 Đang hiệu chỉnh tạp âm môi trường... Vui lòng giữ im lặng 2 giây.")
        recognizer.adjust_for_ambient_noise(source)
        print("✅ Đã sẵn sàng! Hãy mở một video tiếng nước ngoài lên.")
        print("-" * 50)

        while True:
            try:
                # 1. Lắng nghe âm thanh
                print("🎙️ Đang nghe...")
                audio = recognizer.listen(source, timeout=RECORD_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
                
                # Lưu tạm âm thanh ra file wav để Whisper đọc
                with open("temp_audio.wav", "wb") as f:
                    f.write(audio.get_wav_data())

                # 2. Chuyển âm thanh thành văn bản (Speech to Text)
                print("🧠 Đang nhận diện...")
                segments, info = audio_model.transcribe("temp_audio.wav", beam_size=5)
                
                original_text = ""
                for segment in segments:
                    original_text += segment.text + " "
                
                original_text = original_text.strip()
                
                if original_text:
                    print(f"🗣️ Gốc ({info.language}): {original_text}")

                    # 3. Dịch thuật sang Tiếng Việt
                    translation = translator.translate(original_text, dest=TARGET_LANG)
                    translated_text = translation.text
                    print(f"🇻🇳 Dịch: {translated_text}")

                    # 4. Phát giọng nói Tiếng Việt (TTS)
                    play_audio(translated_text)
                    print("-" * 50)

            except sr.WaitTimeoutError:
                pass # Không nghe thấy gì trong khoảng thời gian timeout, tiếp tục vòng lặp
            except Exception as e:
                print(f"⚠️ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    main()