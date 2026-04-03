import tkinter as tk
from tkinter import scrolledtext
import threading
import random

# Nhập các hàm xử lý từ não bộ và hệ thống
from brain_logic import extract_intent_and_target, teach_ai
from cmd_executor import (
    run_live_search,
    get_exact_package_for_install,
    install_software_as_admin,
    uninstall_software_as_admin,
    SOFTWARE_NAMES
)

class DuongCarlos:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis - Duong Carlos Assistant")
        self.root.geometry("800x850")
        self.root.configure(bg="#1e1e1e") 

        # ==========================================
        # 1. KHUNG HEADER (TIÊU ĐỀ)
        # ==========================================
        header_frame = tk.Frame(root, bg="#252526", pady=15)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(header_frame, text="DUONG CARLOS ASSISTANT", font=("Segoe UI", 16, "bold"), bg="#252526", fg="#ffffff")
        title_lbl.pack()

        sub_lbl = tk.Label(header_frame, text="System Management & Automation", font=("Segoe UI", 10, "italic"), bg="#252526", fg="#9cdcfe")
        sub_lbl.pack()

        # ==========================================
        # 2. KHUNG CHAT TƯƠNG TÁC
        # ==========================================
        chat_frame = tk.Frame(root, bg="#1e1e1e")
        chat_frame.pack(padx=20, pady=15, fill=tk.BOTH, expand=True)

        self.chat_area = tk.Text(
            chat_frame, wrap=tk.WORD, state='disabled',
            bg="#1e1e1e", bd=0, highlightthickness=0,
            padx=15, pady=10
        )
        self.chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Cấu hình định dạng chữ tách biệt (tên, màu, font riêng)
        self.chat_area.tag_config("user_name", foreground="#569CD6", font=("Segoe UI", 11, "bold"))
        self.chat_area.tag_config("user_msg", foreground="#ffffff", font=("Segoe UI", 11))
        
        self.chat_area.tag_config("bot_name", foreground="#DCDCAA", font=("Segoe UI", 11, "bold"))
        self.chat_area.tag_config("bot_msg", foreground="#cccccc", font=("Segoe UI", 11))
        
        self.chat_area.tag_config("terminal_output", foreground="#ce9178", font=("Consolas", 10))

        scrollbar = tk.Scrollbar(chat_frame, command=self.chat_area.yview, bg="#1e1e1e", bd=0, troughcolor="#1e1e1e")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_area.configure(yscrollcommand=scrollbar.set)

        # ==========================================
        # 3. KHUNG NHẬP LIỆU
        # ==========================================
        input_frame = tk.Frame(root, bg="#252526", pady=10, padx=10)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.entry_box = tk.Entry(
            input_frame, font=("Segoe UI", 12),
            bg="#333333", fg="#ffffff", insertbackground="#ffffff",
            bd=0, highlightthickness=1, highlightbackground="#3e3e42", highlightcolor="#007acc",
            relief="flat"
        )
        self.entry_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=8, padx=(10, 15))
        self.entry_box.bind("<Return>", self.send_message)

        send_btn = tk.Button(
            input_frame, text="GỬI LỆNH", command=self.send_message,
            bg="#007acc", fg="white", font=("Segoe UI", 10, "bold"),
            bd=0, relief="flat", activebackground="#005f9e", activeforeground="white",
            cursor="hand2", padx=20
        )
        send_btn.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5))

        # Các biến lưu trữ trạng thái chờ xác nhận cài đặt
        self.pending_package = None
        self.pending_version = None
        self.pending_intent = None

        self.insert_message("Duong Carlos", "Chào Bạn! Hệ thống AI Duong Carlos đã sẵn sàng.\nMẹo: Nếu mình không hiểu, Bạn có thể dạy mình bằng lệnh:\n👉 'Dạy [nhóm lệnh]: [câu nói]'\n👉 Hoặc: 'Nếu tôi nói [A] thì bạn trả lời là [B]'")

    def insert_message(self, sender, message, is_terminal=False):
        self.chat_area.config(state='normal')
        
        if sender == "Bạn":
            self.chat_area.insert(tk.END, f"\n👤 {sender}:\n", "user_name")
            self.chat_area.insert(tk.END, f"{message}\n", "user_msg")
        else:
            self.chat_area.insert(tk.END, f"🤖 {sender}:\n", "bot_name")
            if is_terminal:
                self.chat_area.insert(tk.END, f"{message}\n\n", "terminal_output")
            else:
                self.chat_area.insert(tk.END, f"{message}\n\n", "bot_msg")
            
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END) 

    def process_response(self, user_text):
        intent, target_name = extract_intent_and_target(user_text)

        # -----------------------------------------------
        # CHẾ ĐỘ DẠY HỌC MACHINE LEARNING
        # -----------------------------------------------
        if intent == "teach":
            success, response_msg = teach_ai(target_name)
            self.insert_message("Duong Carlos", response_msg)
            return

        # -----------------------------------------------
        # CHẾ ĐỘ LUẬT TÙY CHỈNH (Q&A THEO Ý NGƯỜI DÙNG)
        # -----------------------------------------------
        if intent == "teach_custom":
            self.insert_message("Duong Carlos", target_name)
            return
            
        if intent == "custom_qa":
            self.insert_message("Duong Carlos", target_name)
            return

        # -----------------------------------------------
        # CHẾ ĐỘ XÁC NHẬN CÀI ĐẶT / GỠ BỎ
        # -----------------------------------------------
        if intent == "confirm" and self.pending_package:
            pkg = self.pending_package
            ver = self.pending_version
            itn = self.pending_intent
            self.pending_package = None 
            
            if itn == "uninstall":
                self.insert_message("Duong Carlos", f"🚀 Đang tiến hành gỡ bỏ '{pkg}'...")
                threading.Thread(target=self.thread_execute_uninstall, args=(pkg, ver)).start()
            else:
                self.insert_message("Duong Carlos", f"🚀 Đang tiến hành cài đặt '{pkg}'...")
                threading.Thread(target=self.thread_execute_install, args=(pkg, ver)).start()
            return

        if intent == "cancel" and self.pending_package:
            self.insert_message("Duong Carlos", f"❌ Đã hủy lệnh xử lý gói '{self.pending_package}'.")
            self.pending_package = None
            return

        if self.pending_package and intent not in ["confirm", "cancel"]:
            self.pending_package = None 

        # -----------------------------------------------
        # XỬ LÝ GIAO TIẾP THÔNG THƯỜNG
        # -----------------------------------------------
        if intent == "gratitude":
            wishes = ["Rất sẵn lòng được hỗ trợ Bạn! ✨", "Không có gì đâu ạ! Cần gì Bạn cứ gọi AI nhé! 🚀"]
            self.insert_message("Duong Carlos", random.choice(wishes))
            return

        if intent == "greeting":
            greetings = [
                "Chào Bạn! Bạn cần cài hay gỡ phần mềm gì hôm nay ạ? 💻",
                "Chào Bạn! Mình là AI Duong Carlos đây, Bạn cần hỗ trợ gì không?",
                "Mình nghe đây! Bạn cứ gõ lệnh cài đặt hoặc tra cứu nhé. 🚀"
            ]
            self.insert_message("Duong Carlos", random.choice(greetings))
            return
            
        if intent == "ask_permission":
            self.insert_message("Duong Carlos", "Bạn cứ hỏi đi ạ, mình sẵn sàng giải đáp! 💡")
            return
            
        if intent == "general_search_inquiry":
            self.insert_message("Duong Carlos", "Được chứ! Bạn muốn tra cứu phần mềm gì, cứ gõ 'tìm <tên phần mềm>' nhé. 🔍")
            return
            
        if intent == "about":
            msg = ("Mình là hệ thống AI Duong Carlos. Các tính năng chính của mình bao gồm:\n"
                   "📌 1. Tra cứu phần mềm (VD: 'tìm office')\n"
                   "📌 2. Cài đặt tự động (VD: 'cài 7zip 23.01')\n"
                   "📌 3. Gỡ cài đặt (VD: 'gỡ firefox')\n"
                   "Bạn cần mình hỗ trợ tính năng nào ạ? 🦾")
            self.insert_message("Duong Carlos", msg)
            return
            
        if intent == "smalltalk":
            self.insert_message("Duong Carlos", "Mình là AI chuyên về IT nên mảng tâm sự hơi kém một chút 😅. Nếu Bạn cần thì mình có thể hỗ trợ cài vài phần mềm giải trí nhé!")
            return
            
        if intent == "unknown":
            self.insert_message("Duong Carlos", "Câu này mình chưa hiểu rõ ý. Nếu Bạn muốn dạy mình hiểu câu này, hãy gõ lệnh:\n👉 Dạy [nhóm lệnh]: [câu nói của Bạn]")
            return

        # -----------------------------------------------
        # XỬ LÝ LỆNH HỆ THỐNG
        # -----------------------------------------------
        if intent == "list":
            self.insert_message("Duong Carlos", "📋 Chế độ tra cứu kho phần mềm online. Bạn gõ: 'tìm <tên phần mềm>' để xem danh sách nhé.")
            return

        if intent == "search":
            self.insert_message("Duong Carlos", f"🔍 Đang quét kho tổng để tìm '{target_name}', Bạn vui lòng chờ...")
            threading.Thread(target=self.thread_search, args=(target_name,)).start()
            return

        # LUỒNG CÀI ĐẶT/GỠ BỎ: CHỈ TÌM TÊN VÀ HỎI XÁC NHẬN
        if intent in ["install", "uninstall"]:
            self.insert_message("Duong Carlos", f"🔍 Đang tra cứu gói chuẩn cho '{target_name}'...")
            threading.Thread(target=self.thread_prepare_action, args=(intent, target_name)).start()

    def thread_search(self, query):
        output = run_live_search(query)
        if not output.strip() or "0 packages found" in output:
            self.insert_message("Duong Carlos", f"❌ Không tìm thấy thông tin nào cho '{query}' trên hệ thống.")
        else:
            self.insert_message("Duong Carlos", f"📦 Kết quả tra cứu thực tế:\n{'-'*60}\n{output}", is_terminal=True)

    def thread_prepare_action(self, intent, target_name):
        pkg, ver = get_exact_package_for_install(target_name)
        if not pkg:
            self.insert_message("Duong Carlos", f"❌ Rất tiếc, mình chưa tìm thấy hoặc quá thời gian chờ tra cứu gói '{target_name}'.")
            return
        
        self.pending_package = pkg
        self.pending_version = ver
        self.pending_intent = intent
        
        action_text = "CÀI ĐẶT" if intent == "install" else "GỠ BỎ"
        ver_text = f" (phiên bản {ver})" if ver else ""
        self.insert_message("Duong Carlos", f"✅ Mình đã tìm thấy gói: '{pkg}'{ver_text}.\nBạn có đồng ý {action_text} không? (Gõ 'Có' hoặc 'Không')")

    def thread_execute_install(self, pkg, ver):
        if install_software_as_admin(pkg, ver):
            self.insert_message("Duong Carlos", f"🚀 Tiến trình cài đặt đã khởi chạy. Cửa sổ CMD sẽ tự động đóng khi hoàn tất.")
        else:
            self.insert_message("Duong Carlos", "⚠️ Không thể chạy cài đặt (từ chối quyền hoặc lỗi).")

    def thread_execute_uninstall(self, pkg, ver):
        if uninstall_software_as_admin(pkg, ver):
            self.insert_message("Duong Carlos", f"🚀 Tiến trình gỡ cài đặt đã khởi chạy. Cửa sổ CMD sẽ tự động đóng khi hoàn tất.")
        else:
            self.insert_message("Duong Carlos", "⚠️ Không thể chạy lệnh gỡ cài đặt (từ chối quyền hoặc lỗi hệ thống).")

    def send_message(self, event=None):
        user_text = self.entry_box.get()
        if not user_text.strip(): return
        self.insert_message("Bạn", user_text)
        self.entry_box.delete(0, tk.END)
        self.process_response(user_text)