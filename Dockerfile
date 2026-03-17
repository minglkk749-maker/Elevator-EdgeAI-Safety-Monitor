# 使用 NVIDIA CUDA 映像檔確保 GPU 加速
FROM nvidia/cuda:12.0.1-cudnn8-devel-ubuntu22.04

# 避免安裝過程中的互動提問
ENV DEBIAN_FRONTEND=noninteractive

# 安裝系統層級工具：Python, OpenCV 依賴與 Mosquitto 客戶端
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    mosquitto-clients \
    && rm -rf /var/lib/apt/lists/*

# 安裝 2026 AIoT 核心套件
RUN pip3 install opencv-python ultralytics numpy python-dotenv paho-mqtt

# 每分鐘檢查一次 Python 程式是否還活著
HEALTHCHECK --interval=60s --timeout=10s \
  CMD pgrep -f elevator_ai_guard_v2.py || exit 1