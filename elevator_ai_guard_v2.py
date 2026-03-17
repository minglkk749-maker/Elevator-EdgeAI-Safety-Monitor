import os, json, time, cv2
from ultralytics import YOLO
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()
# 載入輕量化模型，展現對邊緣運算資源配置的優化思維 [cite: 3, 5, 36, 125]
model = YOLO('yolov8n.pt') 

# 從 .env 讀取設定 [cite: 39, 158]
BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT"))
TOPIC = os.getenv("MQTT_TOPIC")
THRESHOLD = int(os.getenv("PERSON_THRESHOLD"))

# 初始化 MQTT 客戶端 [cite: 35, 126]
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# --- 新增 1：MQTT 自動重連機制 (強化連線韌性) ---
# 設定最小延遲 1 秒，最大 120 秒，確保 Broker 閃斷後能自動回連 [cite: 162, 187]
client.reconnect_delay_set(min_delay=1, max_delay=120)

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print(f"✅ 連線至本地 MQTT Broker 成功")
    else:
        print(f"⚠️ 連線失敗，錯誤碼: {rc}")

client.on_connect = on_connect
client.connect(BROKER, PORT, 60)
client.loop_start() 

# 模擬從 data 資料夾讀取影片 
video_path = 'data/elevator_video.mp4'
cap = cv2.VideoCapture(video_path)
last_count = -1

try:
    while True: # 改為無限迴圈，配合內部的影像重連邏輯 [cite: 163, 199]
        ret, frame = cap.read()
        
        # --- 新增 2：影像串流自癒邏輯 (避免硬體閃斷導致程式終止) ---
        if not ret: 
            print("⚠️ 影像串流中斷或讀取失敗，嘗試重新啟動鏡頭...")
            cap.release()
            time.sleep(5) # 等待 5 秒後重試，展現維運時效管理思維 
            cap = cv2.VideoCapture(video_path)
            continue

        # 執行 GPU 推論，展現高效率搶修與邏輯分析能力 [cite: 45, 162]
        results = model.predict(source=frame, device=0, verbose=False)
        current_count = sum(1 for box in results[0].boxes if int(box.cls[0]) == 0)

        # 變動觸發：僅在人數變化時上傳，優化 Data Quality 並減少頻寬負擔 [cite: 37, 39, 186]
        if current_count != last_count:
            payload = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "person_count": current_count,
                "status": "OVERCROWDED" if current_count >= THRESHOLD else "NORMAL"
            }
            client.publish(TOPIC, json.dumps(payload))
            print(f"📡 狀態變更：偵測到 {current_count} 人，已拋轉數據")
            last_count = current_count

        time.sleep(0.1) 
        
except KeyboardInterrupt:
    print("🛑 使用者終止程式")
finally:
    cap.release()
    client.loop_stop()