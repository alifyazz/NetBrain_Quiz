import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import socket
import threading
import json

# Configuration
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000

# Set modern theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class QuizClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Network Quiz Contest")
        self.geometry("600x700")
        
        # Connection state
        self.client_socket = None
        self.is_connected = False
        self.username = ""
        self.current_question_id = 0
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Main Container
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- UI Pages ---
        self.create_login_page()
        self.create_quiz_page()
        
        # Show Login initially
        self.show_login()

    def create_login_page(self):
        self.login_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        self.lbl_title = ctk.CTkLabel(self.login_frame, text="NetBrain Quiz", font=("Roboto", 32, "bold"))
        self.lbl_title.pack(pady=(40, 20))
        
        self.lbl_subtitle = ctk.CTkLabel(self.login_frame, text="Enter your name to join the battle!", font=("Roboto", 16))
        self.lbl_subtitle.pack(pady=(0, 30))
        
        self.entry_name = ctk.CTkEntry(self.login_frame, placeholder_text="Username", width=300, height=40, font=("Roboto", 14))
        self.entry_name.pack(pady=10)
        
        self.entry_ip = ctk.CTkEntry(self.login_frame, placeholder_text="Server IP (e.g. 192.168.1.5)", width=300, height=40, font=("Roboto", 14))
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(pady=10)
        
        self.btn_join = ctk.CTkButton(self.login_frame, text="Join Quiz", width=300, height=50, font=("Roboto", 16, "bold"),
                                      command=self.connect_to_server, corner_radius=25)
        self.btn_join.pack(pady=20)
        
    def create_quiz_page(self):
        self.quiz_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Top Bar (Timer & Status)
        self.top_bar = ctk.CTkFrame(self.quiz_frame, height=50, fg_color="transparent")
        self.top_bar.pack(fill="x", pady=(0, 20))
        
        self.lbl_timer = ctk.CTkLabel(self.top_bar, text="Time: --", font=("Roboto", 18, "bold"), text_color="#FF5555")
        self.lbl_timer.pack(side="right")
        
        self.lbl_status = ctk.CTkLabel(self.top_bar, text="Status: Waiting...", font=("Roboto", 14), text_color="gray")
        self.lbl_status.pack(side="left")

        # Question Area
        self.q_container = ctk.CTkFrame(self.quiz_frame, corner_radius=10, border_width=1, border_color="#333333")
        self.q_container.pack(fill="x", pady=10, ipady=20)
        
        self.lbl_question = ctk.CTkLabel(self.q_container, text="Questions will appear here...", 
                                         font=("Roboto", 22, "bold"), wraplength=500)
        self.lbl_question.pack(padx=20, pady=20)

        # Options Area
        self.options_frame = ctk.CTkFrame(self.quiz_frame, fg_color="transparent")
        self.options_frame.pack(fill="both", expand=True, pady=20)
        
        self.option_buttons = []
        for i in range(4):
            btn = ctk.CTkButton(self.options_frame, text=f"Option {i+1}", font=("Roboto", 16), 
                                height=50, border_spacing=10, fg_color="transparent", border_width=2,
                                text_color=("gray10", "#DCE4EE"), border_color=("#3E454A", "#949A9F"),
                                hover_color=("#325882", "#14375e"),
                                command=lambda idx=i: self.send_answer(idx))
            btn.pack(fill="x", pady=8)
            self.option_buttons.append(btn)

    def show_login(self):
        self.quiz_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_quiz(self):
        self.login_frame.pack_forget()
        self.quiz_frame.pack(fill="both", expand=True)
        self.title(f"Quiz Contest - {self.username}")

    def connect_to_server(self):
        name = self.entry_name.get().strip()
        server_ip = self.entry_ip.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Please enter a name")
            return
            
        if not server_ip:
             messagebox.showerror("Error", "Please enter Server IP")
             return

        self.username = name
        
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, SERVER_PORT))
            self.is_connected = True
            
            # Send LOGIN
            login_req = {"type": "LOGIN", "name": self.username}
            self.client_socket.sendall(json.dumps(login_req).encode('utf-8'))
            
            # Start background thread
            threading.Thread(target=self.listen_to_server, daemon=True).start()
            
            self.show_quiz()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")

    def listen_to_server(self):
        while self.is_connected:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                
                msg_str = data.decode('utf-8')
                # Handle concatenated JSONs
                raw_msgs = msg_str.replace('}{', '}|{').split('|')
                
                for raw in raw_msgs:
                    try:
                        message = json.loads(raw)
                        self.process_server_message(message)
                    except json.JSONDecodeError:
                        print(f"JSON Error: {raw}")
                            
            except Exception as e:
                print(f"Listen error: {e}")
                break
        
        if self.is_connected:
            self.is_connected = False
            self.after(0, lambda: messagebox.showinfo("Disconnected", "Server closed connection"))
            self.after(0, self.destroy)

    def process_server_message(self, message):
        try:
            msg_type = message.get("type")
            payload = message.get("payload")
            
            if msg_type == "QUESTION":
                self.after(0, self.update_ui_question, payload)
            elif msg_type == "LEADERBOARD":
                self.after(0, self.show_leaderboard, payload)
            elif msg_type == "GAME_OVER":
                self.after(0, lambda: messagebox.showinfo("Game Over", payload.get("message")))
                self.after(0, self.destroy)
        except Exception as e:
            print(f"Error processing message: {e}")

    def update_ui_question(self, payload):
        if not self.winfo_exists(): return

        # Hide Leaderboard if open
        if hasattr(self, 'leaderboard_frame') and self.leaderboard_frame.winfo_exists():
            self.leaderboard_frame.destroy()
            
        # Restore Question and Options frames if they were hidden
        self.q_container.pack(fill="x", pady=10, ipady=20)
        self.options_frame.pack(fill="both", expand=True, pady=20)

        self.current_question_id = payload.get("id")
        q_text = payload.get("text")
        options = payload.get("options")
        duration = payload.get("duration")
        
        self.lbl_question.configure(text=q_text)
        self.lbl_status.configure(text="Select an answer!", text_color="yellow")
        
        for i, btn in enumerate(self.option_buttons):
            if i < len(options):
                btn.configure(text=options[i], state="normal", fg_color="transparent", border_color=("#3E454A", "#949A9F"))
            else:
                btn.configure(text="", state="disabled")
        
        self.countdown_val = duration
        self.update_timer()

    def update_timer(self):
        if not self.winfo_exists(): return
        
        if self.countdown_val >= 0:
            self.lbl_timer.configure(text=f"Time: {self.countdown_val}", text_color="#FF5555" if self.countdown_val < 5 else "#00FF00")
            self.countdown_val -= 1
            self.timer_id = self.after(1000, self.update_timer)

    def send_answer(self, index):
        if not self.is_connected:
            return
            
        # UI Feedback
        for i, btn in enumerate(self.option_buttons):
            if i == index:
                btn.configure(fg_color="#1f6aa5", border_color="#1f6aa5") # Selected
            else:
                btn.configure(state="disabled")
        
        self.lbl_status.configure(text="Answer Submitted.", text_color="cyan")
        
        req = {
            "type": "ANSWER",
            "payload": {
                "question_id": self.current_question_id,
                "answer_index": index
            }
        }
        try:
            self.client_socket.sendall(json.dumps(req).encode('utf-8'))
        except:
            pass

    def show_leaderboard(self, leaderboard):
        if not self.winfo_exists(): return

        # Hide Question UI to show leaderboard "below timer"
        self.q_container.pack_forget()
        self.options_frame.pack_forget()

        # Create frame for leaderboard (using pack instead of place)
        self.leaderboard_frame = ctk.CTkFrame(self.quiz_frame, corner_radius=15, fg_color=("gray90", "gray20"), border_width=2, border_color="#333")
        self.leaderboard_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        lbl_title = ctk.CTkLabel(self.leaderboard_frame, text="Round Results", font=("Roboto", 24, "bold"))
        lbl_title.pack(pady=20)
        
        # Scrollable area for list
        scroll_frame = ctk.CTkScrollableFrame(self.leaderboard_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for i, entry in enumerate(leaderboard):
            color = "#FFD700" if i == 0 else ("#C0C0C0" if i == 1 else ("#CD7F32" if i == 2 else "gray"))
            row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row, text=f"#{i+1}", font=("Roboto", 18, "bold"), text_color=color, width=30).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=entry['name'], font=("Roboto", 18)).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"{entry['score']} pts", font=("Roboto", 18, "bold")).pack(side="right", padx=10)

        self.lbl_status.configure(text="Waiting for next question...", text_color="gray")

    def on_closing(self):
        self.is_connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.destroy()

if __name__ == "__main__":
    app = QuizClientApp()
    app.mainloop()
