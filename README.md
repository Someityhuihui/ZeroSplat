---
title: ZeroSplat
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker 
app_file: app.py
pinned: false
license: mit
---

🚀 ZeroSplat: 3DGS 智能剪枝与跨生态导出工具
License

ZeroSplat 是一个针对 3D Gaussian Splatting (3DGS) 模型的轻量化压缩与格式转换工具。它提供了基于 Gradio 的直观 Web UI，能够一键去除冗余高斯球，大幅缩小模型体积，并支持导出兼容传统三维软件的纯 RGB 点云。

🤔 为什么需要 ZeroSplat？
原始的 3DGS 模型存在两个致命痛点：

体积臃肿：动辄数百 MB 至数 GB，包含大量对渲染贡献极低的半透明废点，无法在移动端实时渲染。
生态封闭：.ply 文件中包含了球谐系数、缩放、旋转等 59 维特征，传统三维软件（CloudCompare, Blender, Maya）无法正常识别其颜色和结构。
ZeroSplat 完美解决了这两个问题！

✨ 核心功能
🚀 渐进式 ROI 剪枝：基于透明度与空间距离的双重掩膜。近处核心区域保留细节（低阈值），远处背景激进去除（高阈值）。
🎨 跨生态 RGB 导出：自动解析 0 阶球谐系数 (f_dc)，还原真实 RGB 颜色，导出仅包含 (X, Y, Z, R, G, B) 的通用点云格式。
🖥️ 零代码 Web UI：基于 Gradio 构建，拖拽上传，滑块调参，一键下载结果。
📊 性能表现 (以 Tanks and Temples - Truck 为例)
指标	原始模型	ZeroSplat 压缩后	降幅
文件体积	488.0 MB	43.8 MB	缩小 91.02%
高斯球数量	2,063,406	185,208	去除 187 万冗余点
RGB点云体积	-	2.6 MB	极致轻量，通吃所有3D软件
视觉质量几乎无损！

🛠️ 安装与运行
克隆仓库：
git clone https://github.com/Someityhuihui/ZeroSplat.gitcd ZeroSplat
安装依赖 (建议使用 Python 3.9+):
bash

pip install -r requirements.txt
启动 Web UI：
bash

python app.py
然后在浏览器中打开 http://localhost:7860 即可使用。

📝 待办事项 (Roadmap)
支持向量量化 (VQ) 进一步压缩球谐系数
集成 3DGS 的 WebGPU 渲染器实现在线预览
增加基于梯度的敏感性剪枝
🤝 致谢
3D Gaussian Splatting
Gradio
License
MIT License
