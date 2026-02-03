import socket
import threading
import json
import time

# Configuration
SERVER_IP = '0.0.0.0'
SERVER_PORT = 5000

# Sample Questions
QUESTIONS = [
    {
        "id": 1,
        "text": "Apa kepanjangan dari TCP?",
        "options": ["Transmission Control Protocol", "Total Control Protocol", "Transfer Control Protocol", "Transmission Central Protocol"],
        "answer_index": 0,
        "duration": 10
    },
    {
        "id": 2,
        "text": "Di layer manakah IP berada dalam model OSI?",
        "options": ["Fisik", "Data Link", "Network", "Transport"],
        "answer_index": 2,
        "duration": 10
    },
    {
        "id": 3,
        "text": "Apa port default untuk HTTP?",
        "options": ["21", "80", "443", "25"],
        "answer_index": 1,
        "duration": 10
    },
    {
        "id": 4,
        "text": "Perintah mana yang digunakan untuk memeriksa konektivitas?",
        "options": ["ipconfig", "ping", "netstat", "traceroute"],
        "answer_index": 1,
        "duration": 10
    },
    {
        "id": 5,
        "text": "Apa port default untuk SSH?",
        "options": ["21", "22", "80", "110"],
        "answer_index": 1,
        "duration": 10
    },
    {
        "id": 6,
        "text": "Apa kepanjangan dari DNS?",
        "options": ["Domain Name System", "Dynamic Network Service", "Domain Network Server", "Direct Network Speed"],
        "answer_index": 0,
        "duration": 10
    },
    {
        "id": 7,
        "text": "Protokol mana yang bersifat connectionless (tanpa koneksi)?",
        "options": ["TCP", "UDP", "FTP", "HTTP"],
        "answer_index": 1,
        "duration": 10
    },
    {
        "id": 8,
        "text": "Perangkat mana yang menghubungkan jaringan yang berbeda?",
        "options": ["Switch", "Hub", "Router", "Repeater"],
        "answer_index": 2,
        "duration": 10
    },
    {
        "id": 9,
        "text": "Apa itu alamat loopback?",
        "options": ["192.168.1.1", "127.0.0.1", "10.0.0.1", "255.255.255.0"],
        "answer_index": 1,
        "duration": 10
    },
    {
        "id": 10,
        "text": "Apa kepanjangan dari LAN?",
        "options": ["Large Area Network", "Local Area Network", "Light Area Network", "Long Area Network"],
        "answer_index": 1,
        "duration": 10
    },
    {
        "id": 11,
        "text": "Apa yang mewakili alamat fisik dari kartu jaringan?",
        "options": ["Alamat IP", "Alamat MAC", "Nomor Port", "Socket"],
        "answer_index": 1,
        "duration": 10
    },
    {
        "id": 12,
        "text": "Apa port default untuk HTTPS?",
        "options": ["80", "443", "21", "22"],
        "answer_index": 1,
        "duration": 10
    },
    {
        "id": 13,
        "text": "Termasuk kelas apakah alamat IP 192.168.1.1?",
        "options": ["Kelas A", "Kelas B", "Kelas C", "Kelas D"],
        "answer_index": 2,
        "duration": 10
    },
    {
        "id": 14,
        "text": "Apa fungsi DHCP?",
        "options": ["Menyelesaikan nama domain", "Memberikan alamat IP", "Mentransfer file", "Mengirim email"],
        "answer_index": 1,
        "duration": 10
    },
    {
        "id": 15,
        "text": "Berapa batas panjang standar untuk segmen kabel Cat5e?",
        "options": ["50 meter", "100 meter", "150 meter", "200 meter"],
        "answer_index": 1,
        "duration": 10
    }
]

class QuizServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_IP, SERVER_PORT))
        self.server_socket.listen(5)
        
        # clients structure: {socket: {"name": "User1", "score": 0, "addr": address}}
        self.clients = {}
        self.lock = threading.Lock()
        self.game_started = False
        self.running = True
        
        print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

    def start(self):
        # Thread for accepting connections
        accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
        accept_thread.start()
        
        # Main Game Loop
        self.game_loop()

    def accept_connections(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                # Start a thread for this client
                threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            except Exception as e:
                print(f"Error accepting connection: {e}")
                if not self.running:
                    break

    def handle_client(self, client_socket, addr):
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    self.process_message(client_socket, message, addr)
                except json.JSONDecodeError:
                    print(f"Invalid JSON from {addr}")
        except ConnectionResetError:
            pass
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            self.remove_client(client_socket)

    def process_message(self, client_socket, message, addr):
        msg_type = message.get("type")
        
        if msg_type == "LOGIN":
            name = message.get("name", "Unknown")
            with self.lock:
                self.clients[client_socket] = {"name": name, "score": 0, "addr": addr}
            print(f"Player logged in: {name} ({addr})")
            
        elif msg_type == "ANSWER":
            if not self.game_started:
                return # Ignore answers if game not running
                
            payload = message.get("payload", {})
            question_id = payload.get("question_id")
            answer_index = payload.get("answer_index")
            
            # Verify answer
            # We need to know which question is current to score correctly
            # Check current question context from Game Loop (shared state needed)
            # For simplicity, passing current_question_id in global/class scope would be better.
            # Implemented in game_loop below.
            
            correct = False
            if self.current_question and self.current_question["id"] == question_id:
                if answer_index == self.current_question["answer_index"]:
                    correct = True
            
            if correct:
                with self.lock:
                    if client_socket in self.clients:
                        self.clients[client_socket]["score"] += 10
                        print(f"Correct answer from {self.clients[client_socket]['name']}")

    def remove_client(self, client_socket):
        with self.lock:
            if client_socket in self.clients:
                name = self.clients[client_socket]["name"]
                del self.clients[client_socket]
                print(f"Player {name} disconnected.")
        client_socket.close()

    def broadcast(self, message):
        data = json.dumps(message).encode('utf-8')
        with self.lock:
            for sock in list(self.clients.keys()):
                try:
                    sock.sendall(data)
                except:
                    self.remove_client(sock)

    def game_loop(self):
        print("Waiting for players to join...")
        # Wait until at least 1 player joins
        while True:
            with self.lock:
                if len(self.clients) > 0:
                    break
            time.sleep(1)
            
        print("Player joined. Starting quiz in 5 seconds...")
        time.sleep(5)
        
        self.game_started = True
        
        for q in QUESTIONS:
            self.current_question = q
            print(f"Asking Question {q['id']}: {q['text']}")
            
            # 1. Send Question
            self.broadcast({
                "type": "QUESTION",
                "payload": {
                    "id": q["id"],
                    "text": q["text"],
                    "options": q["options"],
                    "duration": q["duration"]
                }
            })
            
            # 2. Wait for duration
            time.sleep(q["duration"])
            
            # 3. Send Leaderboard
            leaderboard = []
            with self.lock:
                # Sort clients by score
                sorted_clients = sorted(self.clients.values(), key=lambda x: x['score'], reverse=True)
                leaderboard = [{"name": c['name'], "score": c['score']} for c in sorted_clients]
            
            print("Sending Leaderboard...")
            self.broadcast({
                "type": "LEADERBOARD",
                "payload": leaderboard
            })
            
            # Short break between questions
            time.sleep(3)
            
        # End of Game
        print("Quiz Finished.")
        self.broadcast({
            "type": "QUIZ_FINISHED",
            "payload": {"message": "Quiz Finished! Thanks for participating."}
        })
        self.game_started = False
        self.current_question = None

if __name__ == "__main__":
    server = QuizServer()
    server.start()
