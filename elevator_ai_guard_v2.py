import os, json, time, cv2
from ultralytics import YOLO
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()
model = YOLO('yolov8n.pt') # 載入輕量化模型 [cite: 3, 5]

# 從 .env 讀取設定
BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT"))
TOPIC = os.getenv("MQTT_TOPIC")
THRESHOLD = int(os.getenv("PERSON_THRESHOLD"))

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, userdata, flags, rc, properties):
    print(f"✅ 連線至本地 MQTT Broker 成功")

client.on_connect = on_connect
client.connect(BROKER, PORT, 60)
client.loop_start() # 啟動背景迴圈，避免重複握手造成的延遲

# 模擬從 data 資料夾讀取影片 
video_path = 'data/elevator_video.mp4'
cap = cv2.VideoCapture(video_path)
last_count = -1

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # 執行 GPU 推論 
        results = model.predict(source=frame, device=0, verbose=False)
        current_count = sum(1 for box in results[0].boxes if int(box.cls[0]) == 0)

        # 變動觸發：僅在人數變化時上傳，優化 Data Quality 
        if current_count != last_count:
            payload = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "person_count": current_count,
                "status": "OVERCROWDED" if current_count >= THRESHOLD else "NORMAL"
            }
            client.publish(TOPIC, json.dumps(payload))
            print(f"📡 狀態變更：{current_count} 人")
            last_count = current_count

        time.sleep(0.1) # 平衡效能與即時性
finally:
    cap.release()
    client.loop_stop()