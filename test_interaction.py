import socket
import json
import time
import threading

def run_test_client(name):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 5000))
        
        # Login
        s.sendall(json.dumps({"type": "LOGIN", "name": name}).encode('utf-8'))
        
        while True:
            data = s.recv(4096)
            if not data:
                break
            
            # Simple handling for stream (split by '}{' naive approach for test)
            msgs = data.decode('utf-8').replace('}{', '}|{').split('|')
            
            for m in msgs:
                try:
                    msg = json.loads(m)
                    
                    if msg['type'] == 'QUESTION':
                        print(f"[{name}] Received Question: {msg['payload']['text']}")
                        # Answer immediately
                        ans = {
                            "type": "ANSWER", 
                            "payload": {
                                "question_id": msg['payload']['id'],
                                "answer_index": 0 # Always pick A
                            }
                        }
                        s.sendall(json.dumps(ans).encode('utf-8'))
                        
                    elif msg['type'] == 'LEADERBOARD':
                        print(f"[{name}] Leaderboard: {msg['payload']}")
                        
                    elif msg['type'] == 'GAME_OVER':
                        print(f"[{name}] Game Over")
                        s.close()
                        return
                        
                except Exception as e:
                    pass
    except Exception as e:
        print(f"[{name}] Error: {e}")

if __name__ == "__main__":
    t1 = threading.Thread(target=run_test_client, args=("Tester1",))
    t2 = threading.Thread(target=run_test_client, args=("Tester2",))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
