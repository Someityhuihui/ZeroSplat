# -*- coding: utf-8 -*-
import gradio as gr
from core.processor import process_gaussian_splat
from core.pipeline import run_full_pipeline, show_terminate_confirm, confirm_terminate, cancel_terminate

css = """
#flow-log textarea { max-height: 450px !important; overflow-y: auto !important; font-family: monospace !important; font-size: 13px !important; line-height: 1.4 !important; }
#prune-log textarea { max-height: 250px !important; overflow-y: auto !important; font-family: monospace !important; }
"""

with gr.Blocks(theme=gr.themes.Soft(), title="ZeroSplat Platform", css=css) as app:
    gr.Markdown("# 🌍 ZeroSplat: 3DGS 全链路平台")
    
    with gr.Tab("📸 一键从照片生成 3DGS (需本地GPU)"):
        gr.Markdown("上传包含照片的 ZIP 压缩包，自动完成 COLMAP → 3DGS 训练 → 压缩 → Web导出。**需在带有 NVIDIA 显卡的环境下运行！**\n\n⚠️ **请及时下载所需文件，上传新的照片数据集文件将覆盖当前结果！**")
        with gr.Row():
            with gr.Column(scale=2, min_width=350):
                zip_input = gr.File(label="1. 上传照片 ZIP 包", file_types=[".zip"])
                max_iter = gr.Slider(1000, 30000, value=7000, step=1000, label="2. 最大训练迭代次数", info="7000次较快，30000次精细")
                with gr.Row():
                    full_run_btn = gr.Button("🚀 一键生成 3D 模型", variant="primary", scale=3)
                    terminate_btn = gr.Button("🛑 终止流程", variant="stop", visible=False, scale=1)
                with gr.Column(visible=False) as confirm_panel:
                    gr.Markdown("⚠️ **确认终止？所有进度将丢失！**")
                    with gr.Row():
                        confirm_terminate_btn = gr.Button("🔴 确认终止", variant="stop")
                        cancel_terminate_btn = gr.Button("取消")

            with gr.Column(scale=3):
                full_report = gr.Textbox(label="全流程报告", lines=18, max_lines=25, elem_id="flow-log", show_copy_button=True)
                with gr.Row():
                    full_3dgs = gr.File(label="📥 3DGS模型", scale=1)
                    full_rgb = gr.File(label="📥 RGB点云", scale=1)
                    full_splat = gr.File(label="🌐 Web模型", scale=1)

        full_run_btn.click(fn=run_full_pipeline, inputs=[zip_input, max_iter], outputs=[full_report, full_3dgs, full_rgb, full_splat, terminate_btn, confirm_panel])
        terminate_btn.click(fn=show_terminate_confirm, outputs=[confirm_panel])
        confirm_terminate_btn.click(fn=confirm_terminate, outputs=[confirm_panel])
        cancel_terminate_btn.click(fn=cancel_terminate, outputs=[confirm_panel])

    with gr.Tab("✂️ 剪枝与格式导出 (在线版)"):
        gr.Markdown("上传臃肿的 3DGS `.ply` 模型，一键瘦身！支持导出兼容 CloudCompare 的纯 RGB 点云，及 🌐**Web 端实时渲染专属格式 (.splat)**！")
        with gr.Row():
            with gr.Column(scale=2):
                input_file = gr.File(label="1. 上传 3DGS 模型", file_types=[".ply"])
                with gr.Row():
                    opacity_thresh = gr.Slider(0.005, 0.2, value=0.01, step=0.005, label="2. 透明度阈值")
                    roi_radius = gr.Slider(1.0, 50.0, value=10.0, step=0.5, label="3. ROI 渐进半径")
                with gr.Row():
                    max_distance = gr.Slider(5.0, 100.0, value=30.0, step=1.0, label="4. 远景去除距离")
                    export_rgb = gr.Checkbox(label="5. 同时导出纯 RGB 点云", value=True)
                run_btn = gr.Button("⚡ 开始处理", variant="primary")

            with gr.Column(scale=3):
                report_box = gr.Textbox(label="处理报告", lines=6, max_lines=10, elem_id="prune-log")
                with gr.Row():
                    output_3dgs = gr.File(label="📥 3DGS模型", scale=1)
                    output_rgb = gr.File(label="📥 RGB点云", scale=1)
                    output_splat = gr.File(label="🌐 Web模型", scale=1)

    run_btn.click(fn=process_gaussian_splat, inputs=[input_file, opacity_thresh, roi_radius, max_distance, export_rgb], outputs=[output_3dgs, output_rgb, output_splat, report_box])

if __name__ == "__main__":
    app.queue()
    app.launch(server_name="0.0.0.0", server_port=7860)