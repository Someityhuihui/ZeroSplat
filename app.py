# -*- coding: utf-8 -*-

import gradio as gr
import numpy as np
from plyfile import PlyData, PlyElement
import os

OUTPUT_DIR = "gradio_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def convert_ply_to_splat(ply_path, output_path):
    """修正版：严格对齐 Web 端 32 bytes 标准的 .splat 格式"""
    plydata = PlyData.read(ply_path)
    v = plydata['vertex'].data
    
    # 1. 位置 (3 * float32 = 12 bytes)
    pos = np.vstack([v['x'], v['y'], v['z']]).T
    
    # 2. 缩放 (3 * float32 = 12 bytes) - 必须放在旋转前面！
    scales = np.exp(np.vstack([v['scale_0'], v['scale_1'], v['scale_2']]).T)
    
    # 3. 颜色与透明度 (4 * uint8 = 4 bytes)
    SH_C0 = 0.28209479177387814
    dc = np.vstack([v['f_dc_0'], v['f_dc_1'], v['f_dc_2']]).T
    rgb = np.clip((dc * SH_C0 + 0.5) * 255, 0, 255).astype(np.uint8)
    opacity = np.clip((1.0 / (1.0 + np.exp(-v['opacity']))) * 255, 0, 255).astype(np.uint8)
    rgba = np.hstack([rgb, opacity.reshape(-1, 1)])

    # 4. 旋转 (4 * uint8 = 4 bytes) - 必须从 float32 压缩！
    rot = np.vstack([v['rot_0'], v['rot_1'], v['rot_2'], v['rot_3']]).T
    rot = rot / np.linalg.norm(rot, axis=1, keepdims=True)
    # 将 [-1, 1] 的四元数映射到 [0, 255] 的无符号整数
    rot_uint8 = np.clip((rot + 1.0) * 0.5 * 255, 0, 255).astype(np.uint8)

    # 构建严格 32 字节结构：pos(12) + scale(12) + rgba(4) + rot(4) = 32 bytes
    dtype = np.dtype([
        ('pos', np.float32, (3,)),
        ('scale', np.float32, (3,)),
        ('rgba', np.uint8, (4,)),
        ('rot', np.uint8, (4,))
    ])
    buffer = np.empty(len(pos), dtype=dtype)
    buffer['pos'] = pos
    buffer['scale'] = scales
    buffer['rgba'] = rgba
    buffer['rot'] = rot_uint8
    
    with open(output_path, 'wb') as f:
        f.write(buffer.tobytes())
    

def process_gaussian_splat(input_ply, opacity_thresh, roi_radius, max_distance, export_rgb, progress=gr.Progress()):
    if input_ply is None:
        return None, None, None, None, "❌ 请先上传 .ply 文件！"
    
    splat_path = None
    rgb_path = None
    
    try:
        progress(0.1, desc="📂 读取点云数据...")
        plydata = PlyData.read(input_ply.name)
        vertex_data = plydata['vertex'].data
        original_count = len(vertex_data)
        
        progress(0.3, desc="🧮 计算透明度与空间距离...")
        raw_opacity = vertex_data['opacity']
        alpha = 1.0 / (1.0 + np.exp(-raw_opacity))
        
        positions = np.vstack([vertex_data['x'], vertex_data['y'], vertex_data['z']]).T
        roi_center = np.mean(positions, axis=0)
        distances = np.linalg.norm(positions - roi_center, axis=1)
        
        progressive_threshold = opacity_thresh + (1.0 - opacity_thresh) * np.clip(distances / roi_radius, 0, 1)
        
        mask_opacity = alpha >= progressive_threshold
        mask_distance = distances <= max_distance
        final_mask = mask_opacity & mask_distance
        
        progress(0.5, desc="✂️ 执行智能剪枝...")
        pruned_data = vertex_data[final_mask]
        pruned_count = len(pruned_data)
        removal_percentage = ((original_count - pruned_count) / original_count) * 100

        base_name = os.path.splitext(os.path.basename(input_ply.name))[0]
        pruned_3dgs_path = os.path.join(OUTPUT_DIR, f"{base_name}_pruned.ply")
        PlyData([PlyElement.describe(pruned_data, 'vertex')]).write(pruned_3dgs_path)

        progress(0.7, desc="🌐 正在生成 Web 实时渲染文件...")
        splat_path = os.path.join(OUTPUT_DIR, f"{base_name}_web.splat")
        convert_ply_to_splat(pruned_3dgs_path, splat_path)

        if export_rgb:
            progress(0.9, desc="🎨 转换并导出 RGB 点云...")
            C0 = 0.28209479177387814
            r = np.clip((pruned_data['f_dc_0'] * C0 + 0.5) * 255, 0, 255).astype(np.uint8)
            g = np.clip((pruned_data['f_dc_1'] * C0 + 0.5) * 255, 0, 255).astype(np.uint8)
            b = np.clip((pruned_data['f_dc_2'] * C0 + 0.5) * 255, 0, 255).astype(np.uint8)

            pure_vertices = np.empty(pruned_count, dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'), 
                                                          ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')])
            pure_vertices['x'] = pruned_data['x']
            pure_vertices['y'] = pruned_data['y']
            pure_vertices['z'] = pruned_data['z']
            pure_vertices['red'] = r
            pure_vertices['green'] = g
            pure_vertices['blue'] = b

            rgb_path = os.path.join(OUTPUT_DIR, f"{base_name}_rgb.ply")
            PlyData([PlyElement.describe(pure_vertices, 'vertex')]).write(rgb_path)

        progress(1.0, desc="✅ 全部处理完成！")
        report = f"""
✅ 处理完成！
📊 原始高斯球: {original_count:,}
✂️ 删除废点: {original_count - pruned_count:,} ({removal_percentage:.2f}%)
🎯 保留高斯球: {pruned_count:,}
📂 ROI 中心: [{roi_center[0]:.1f}, {roi_center[1]:.1f}, {roi_center[2]:.1f}]
🌐 Web文件已生成！下载 .splat 文件后，可使用本地浏览器查看器体验 60 帧照片级渲染！
        """
        return rgb_path, pruned_3dgs_path, rgb_path, splat_path, report

    except Exception as e:
        return None, None, None, None, f"❌ 处理出错: {str(e)}\n(请确保上传的是标准的3DGS .ply文件)"


with gr.Blocks(theme=gr.themes.Soft(), title="ZeroSplat MVP") as app:
    gr.Markdown(
        """
        # 🚀 ZeroSplat: 3DGS 智能剪枝与全格式导出工具
        上传臃肿的 3DGS `.ply` 模型，一键瘦身！支持**网页内3D预览**，导出兼容 CloudCompare 的 RGB 点云，及 🌐**Web 端实时渲染专属格式 (.splat)**！
        """
    )

    # ================= 新增：专业的帮助文档 =================
    with gr.Accordion("❓ 参数说明与使用指南", open=False):
        gr.Markdown(
            """
            ### 🛠️ 核心参数解析
            - **核心区透明度阈值**: 低于此值的高斯球将被视为“透明废点”直接删除。**建议**：0.01 为极度安全（几乎无损），0.05~0.1 为激进压缩（可能丢失半透明细节，但体积更小）。
            - **ROI 渐进半径**: 以模型中心为起点，在此半径内，阈值保持为你设定的“核心区阈值”；超出此半径，阈值会随距离线性增加，越远的高斯球越容易被砍掉。**这能完美保护主体，同时大幅砍除远景冗余。**
            - **远景去除距离**: 距离中心超过此距离的高斯球，无论透明度多少，一律强制作废。适用于直接切掉天空或极远处的背景。
            - **导出纯 RGB 点云**: 勾选后，会额外输出一个极小的点云文件，可用 CloudCompare、MeshLab 等传统软件打开。
            
            ### 🌐 关于 Web 实时渲染文件
            下载我们生成的 `_web.splat` 文件，配合基于 WebGPU 的开源查看器（如 [antimatter15/splat](https://github.com/antimatter15/splat)），即可在浏览器中体验 **60帧、照片级、无需GPU** 的丝滑渲染！这是将 3DGS 部署到网页/手机端的唯一途径。
            """
        )
    # ========================================================

    with gr.Row():
        with gr.Column(scale=1):
            input_file = gr.File(label="1. 上传 3DGS 模型", file_types=[".ply"])
            opacity_thresh = gr.Slider(0.005, 0.2, value=0.01, step=0.005, label="2. 核心区透明度阈值", info="越低越保真，0.01为无损，0.1为激进")
            roi_radius = gr.Slider(1.0, 50.0, value=10.0, step=0.5, label="3. ROI 渐进半径", info="保护中心主体，激进去除边缘")
            max_distance = gr.Slider(5.0, 100.0, value=30.0, step=1.0, label="4. 远景去除距离", info="强制删除超出此距离的背景")
            export_rgb = gr.Checkbox(label="5. 同时导出纯 RGB 点云", value=True)
            run_btn = gr.Button("⚡ 开始处理", variant="primary")

        with gr.Column(scale=1):
            # ================= 新增：3D 预览窗口 =================
            preview_3d = gr.Model3D(label="👀 剪枝后 3D 预览 (RGB点云)", camera_position=(0, 0, -5))
            # ========================================================
            report_box = gr.Textbox(label="处理报告", lines=6)
            with gr.Row():
                output_3dgs = gr.File(label="📥 3DGS模型")
                output_rgb = gr.File(label="📥 RGB点云")
                output_splat = gr.File(label="🌐 Web模型")

    run_btn.click(
        fn=process_gaussian_splat,
        inputs=[input_file, opacity_thresh, roi_radius, max_distance, export_rgb],
        outputs=[preview_3d, output_3dgs, output_rgb, output_splat, report_box]
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=True)
    