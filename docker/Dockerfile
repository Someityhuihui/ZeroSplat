FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip python3-dev git cmake build-essential \
    libboost-all-dev libflann-dev libeigen3-dev \
    libqt5opengl5-dev libglew-dev colmap \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

RUN git clone https://github.com/graphdeco-inria/gaussian-splatting.git /app/gaussian-splatting
WORKDIR /app/gaussian-splatting
RUN pip3 install submodules/diff-gaussian-rasterization
RUN pip3 install submodules/simple-knn

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860
ENV PYTHONUNBUFFERED=1
CMD ["python3", "app.py"]