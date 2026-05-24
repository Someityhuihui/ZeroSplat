# 🌍 ZeroSplat: 3DGS 全链路开源平台

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/zerosplat.svg)](https://github.com/YOUR_USERNAME/zerosplat)

无需编写任何代码，只需上传你拍摄的照片 ZIP 压缩包，即可一键体验最前沿的三维重建技术 —— **3D Gaussian Splatting (3DGS)**！

从稀疏重建 (COLMAP) 到 模型训练 (3DGS) 再到 Web 端实时渲染格式导出，全流程自动化完成。

## ✨ 核心功能

- 📸 **一键式体验**：打开网页即可开始生成你的 3D 模型。
- 🔄 **全链路闭环**：自动执行 `照片解压` ➡️ `COLMAP 位姿估计` ➡️ `3DGS 训练` ➡️ `模型后处理`。
- 🌐 **Web 友好导出**：自动将庞大的 3DGS 模型转换为轻量级的 `.splat` 格式。
- ✂️ **智能剪枝引擎**：内置基于透明度与空间距离的渐进式剪枝算法。
- 🛑 **安全可控**：支持训练过程中随时终止（二次确认防误触）。

## 🚀 快速开始

### 方式一：Docker 部署 (推荐)

前提：已安装 NVIDIA 显卡驱动及 NVIDIA Container Toolkit。

```bash
git clone https://github.com/YOUR_USERNAME/zerosplat.git
cd zerosplat
docker build -f docker/Dockerfile -t zerosplat .
docker run -it -p 7860:7860 --gpus all zerosplat

```

### 方式二：Conda 本地部署

请确保你的服务器已经配置好 Gaussian Splatting 的环境。

```bash
git clone https://github.com/Someityhuihui/zerosplat.git
cd zerosplat
pip install -r requirements.txt

# 修改 core/pipeline.py 中的 GAUSSIAN_DIR 为你本地的路径
python app.py

```

## 📂 项目结构

```text
zerosplat/
├── app.py                  # Gradio 前端主入口
├── core/                   # 核心引擎代码（与 UI 解耦）
│   ├── processor.py        # 剪枝与格式转换引擎
│   └── pipeline.py         # 全流程调度与进程管理
├── docker/                 # 环境封装配置
│   └── Dockerfile          
└── requirements.txt        # Python 依赖

```

## 🙏 致谢

- [Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting)
- [COLMAP](https://github.com/colmap/colmap)
- [Gradio](https://github.com/gradio-app/gradio)