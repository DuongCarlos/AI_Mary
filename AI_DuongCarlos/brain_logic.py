import unicodedata
import json
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib

DATA_FILE = 'training_data.json'
MODEL_FILE = 'ai_model.pkl'
CUSTOM_QA_FILE = 'custom_qa.json'

def smart_match(text, keyword_groups):
    for group in keyword_groups:
        if all(word in text for word in group):
            return True
    return False

def train_model():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "install": ["cài cho anh", "setup phần mềm"],
            "uninstall": ["gỡ ứng dụng", "xóa phần mềm"],
            "search": ["tìm thử xem", "tra cứu"],
            "greeting": ["xin chào", "hello", "hi"],
            "smalltalk": ["tâm sự đi", "buồn quá"],
            "about": ["bạn làm được gì", "chức năng là gì"]
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
            
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    texts = []
    labels = []
    for intent, phrases in data.items():
        for phrase in phrases:
            normalized_phrase = unicodedata.normalize('NFC', phrase.lower().strip())
            texts.append(normalized_phrase)
            labels.append(intent)

    model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), MultinomialNB())
    model.fit(texts, labels)
    
    joblib.dump(model, MODEL_FILE)
    return model

def load_ai_model():
    if not os.path.exists(MODEL_FILE):
        return train_model()
    return joblib.load(MODEL_FILE)

AI_MODEL = load_ai_model()

def teach_ai(text):
    match = re.match(r'^dạy\s+(.*?)\s*:\s*(.*)$', text.lower())
    if not match:
        return False, "⚠️ Sai cú pháp. Mẫu: 'Dạy [nhóm lệnh]: [câu mẫu]'"
    
    vietnamese_intent = match.group(1).strip()
    phrase = match.group(2).strip()
    
    intent_map = {
        "chào hỏi": "greeting", "chào": "greeting",
        "cài đặt": "install", "cài": "install",
        "gỡ bỏ": "uninstall", "gỡ": "uninstall", "xóa": "uninstall",
        "tìm kiếm": "search", "tìm": "search",
        "chức năng": "about", "khả năng": "about",
        "tâm sự": "smalltalk", "nói chuyện": "smalltalk"
    }
    
    target_intent = intent_map.get(vietnamese_intent)
    if not target_intent:
        return False, f"⚠️ Nhóm '{vietnamese_intent}' không tồn tại."
        
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if target_intent not in data: data[target_intent] = []
        
    if phrase not in data[target_intent]:
        data[target_intent].append(phrase)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        if os.path.exists(MODEL_FILE): os.remove(MODEL_FILE)
        global AI_MODEL
        AI_MODEL = train_model() 
        return True, f"🧠 Đã học thuộc câu: '{phrase}' (Nhóm: {vietnamese_intent})."
    else:
        return False, "Câu này mình đã biết rồi!"

def extract_intent_and_target(user_input):
    text_raw = user_input.strip()
    text = unicodedata.normalize('NFC', text_raw.lower())
    words = text.split()
    
    # ==========================================
    # 1. HỌC LUẬT NẾU - THÌ (REGEX SIÊU LINH HOẠT)
    # ==========================================
    # Hỗ trợ đủ kiểu: ngoặc kép, thiếu chữ 'thì', có chữ 'là', 'có thể', 'phải'...
    pattern = r'nếu (?:tôi|anh|mình|bạn) nói\s*(?:là)?\s*["\']?(.*?)["\']?\s*(?:thì)?\s*(?:bạn|mình|ai)\s*(?:có thể|phải|nên)?\s*(?:trả lời|nói)\s*(?:là)?\s*["\']?:?\s*(.*?)["\']?$'
    match = re.search(pattern, text_raw, re.IGNORECASE)
    if match:
        question = unicodedata.normalize('NFC', match.group(1).strip().lower())
        answer = match.group(2).strip()
        
        qa_data = {}
        if os.path.exists(CUSTOM_QA_FILE):
            with open(CUSTOM_QA_FILE, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)
                
        qa_data[question] = answer
        with open(CUSTOM_QA_FILE, 'w', encoding='utf-8') as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=4)
            
        return "teach_custom", f"🧠 Đã thiết lập thành công!\nTừ giờ nếu Bạn nói: '{question}'\nMình sẽ trả lời: '{answer}'"

    # ==========================================
    # 2. KIỂM TRA BỘ NHỚ Q&A (Hỗ trợ quét không cần ngoặc kép)
    # ==========================================
    clean_text = text.replace('"', '').replace("'", "")
    if os.path.exists(CUSTOM_QA_FILE):
        with open(CUSTOM_QA_FILE, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
        for q, a in qa_data.items():
            if q in clean_text:
                return "custom_qa", a

    # ==========================================
    # 3. CHẾ ĐỘ DẠY HỌC MACHINE LEARNING
    # ==========================================
    if text.startswith("dạy "):
        return "teach", text_raw

    # ==========================================
    # 4. SAFETY NET (Khiên bảo vệ giao tiếp cứng)
    # ==========================================
    if smart_match(text, [["nói chuyện"], ["trò chuyện"], ["tâm sự"], ["chán"], ["buồn"]]):
        return "smalltalk", ""
    if smart_match(text, [["làm", "gì"], ["hỗ trợ", "gì"], ["chức", "năng"], ["tính", "năng"]]):
        return "about", ""
    if smart_match(text, [["chào"], ["hello"], ["hi"], ["alo"]]):
        if not smart_match(text, [["cài"], ["tìm"], ["gỡ"]]):
            return "greeting", ""

    # ==========================================
    # 5. CHẠY MACHINE LEARNING PREDICTION
    # ==========================================
    intent = "unknown"
    if AI_MODEL:
        predicted_intents = AI_MODEL.predict([text])
        probabilities = AI_MODEL.predict_proba([text])[0]
        max_prob = max(probabilities)
        if max_prob > 0.15:
            intent = predicted_intents[0]

    # Các lệnh cố định cứng
    if any(word in text for word in ["cảm ơn", "thanks", "thank", "tạm biệt", "bye"]): intent = "gratitude"
    if any(word in text for word in ["danh sách", "liệt kê", "list"]): intent = "list"
    if any(word in text for word in ["có", "ok", "ừ", "cài đi", "triển", "đồng ý"]):
        if len(words) <= 3: intent = "confirm"
    if any(word in text for word in ["không", "hủy", "đừng", "cancel"]):
        if len(words) <= 3: intent = "cancel"

    # Lọc từ rác
    common_stop_words = [
        "bạn", "mình", "tôi", "cần", "tìm", "tim", "search", "tra", "cứu", "thử", "xem", 
        "phần", "mềm", "ứng", "dụng", "giúp", "hộ", "cho", "được", "không", "ko", "nhỉ", 
        "nhé", "với", "nào", "ạ", "thì", "sao", "đi", "nha", "vậy", "cái", "này", 
        "đó", "kia", "kìa", "hướng", "dẫn", "cách", "làm", "để", "cài", "cai", "đặt", "setup", 
        "gỡ", "xóa", "uninstall", "remove", "luôn", "ngay", "em", "anh",
        "thấy", "chưa", "rồi", "đâu", "đây", "nhá", "đấy", "hả", "hở", "ơi", "nữa",
        "có", "những", "các", "một", "vài", "lại", "chứ", "mà", "naiof",
        "á", "à", "ừ", "thế", "đã", "chỉ", "cũng", "vẫn", "đang", "sẽ", "vừa", "mới",
        "1", "hữu", "ích", "ấy", "hay", "tốt", "nhất", "của", "những", "giùm", "quất", "tiêu", "diệt"
    ]

    query = " ".join([w for w in words if w not in common_stop_words]).strip()
    
    if intent in ["search", "install", "uninstall"]:
        if not query:
            if intent == "search": return "general_search_inquiry", ""
            return "unknown", ""
            
    return intent, query