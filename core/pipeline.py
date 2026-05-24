# -*- coding: utf-8 -*-
import os
import subprocess
import gradio as gr
import zipfile
import shutil
import sys
import threading
import re

# 🚨 Docker 部署时改为 /app/gaussian-splatting，本地运行改为你服务器的路径
GAUSSIAN_DIR = "/app/gaussian-splatting" 
OUTPUT_DIR = os.path.expanduser("~/zerosplat_jobs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 全局进程控制
_pipeline_process = None
_pipeline_lock = threading.Lock()
_terminate_requested = False

def clean_log_line(line):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    line = ansi_escape.sub('', line)
    if '\r' in line: line = line.split('\r')[-1]
    return line

def confirm_terminate():
    global _terminate_requested, _pipeline_process
    _terminate_requested = True
    with _pipeline_lock:
        if _pipeline_process is not None:
            try: _pipeline_process.terminate(); _pipeline_process.stdout.close()
            except Exception: pass
    return gr.update(visible=False)

def cancel_terminate(): return gr.update(visible=False)
def show_terminate_confirm(): return gr.update(visible=True)

def run_full_pipeline(zip_file, max_iter):
    global _pipeline_process, _terminate_requested
    
    if zip_file is None:
        yield "❌ 请上传照片 ZIP 包", None, None, None, gr.update(visible=False), gr.update(visible=False)
        return
    
    _terminate_requested = False
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    
    task_id = os.path.basename(zip_file.name).split('.')[0]
    source_dir = os.path.join(OUTPUT_DIR, task_id)
    model_dir = os.path.join(source_dir, "output")
    if os.path.exists(source_dir): shutil.rmtree(source_dir)
    os.makedirs(source_dir, exist_ok=True)

    # === 阶段 0: 解压 ===
    full_log = "📂 [阶段 0/3] 解压照片并重组目录...\n"
    yield full_log, None, None, None, gr.update(visible=True), gr.update(visible=False)
    
    with zipfile.ZipFile(zip_file.name, 'r') as zip_ref: zip_ref.extractall(source_dir)
    target_input_dir = os.path.join(source_dir, "input")
    os.makedirs(target_input_dir, exist_ok=True)
    
    image_files = []
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')): image_files.append(os.path.join(root, f))
    
    if not image_files:
        full_log += "❌ ZIP包中未找到任何图片！\n"
        yield full_log, None, None, None, gr.update(visible=False), gr.update(visible=False)
        return
        
    for src_file in image_files:
        dst_file = os.path.join(target_input_dir, os.path.basename(src_file))
        if src_file != dst_file: shutil.move(src_file, dst_file)

    full_log += f"✅ 找到 {len(image_files)} 张图片，解压完成。\n"
    yield full_log, None, None, None, gr.update(visible=True), gr.update(visible=False)

    # === 阶段 1: COLMAP ===
    full_log += "\n" + "="*40 + "\n⏳ [阶段 1/3] 运行 COLMAP (CPU)...\n" + "="*40 + "\n"
    yield full_log, None, None, None, gr.update(visible=True), gr.update(visible=False)
    
    colmap_cmd = [sys.executable, f"{GAUSSIAN_DIR}/convert.py", "-s", source_dir, "--no_gpu"]
    with _pipeline_lock:
        _pipeline_process = subprocess.Popen(colmap_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=GAUSSIAN_DIR, env=env, bufsize=1)
    
    terminated = False
    for line in iter(_pipeline_process.stdout.readline, ''):
        if not line: break
        if _terminate_requested: terminated = True; break
        clean_line = clean_log_line(line)
        if clean_line.strip():
            full_log += clean_line
            yield full_log, None, None, None, gr.update(visible=True), gr.update(visible=False)
    
    if terminated:
        with _pipeline_lock:
            try: _pipeline_process.terminate(); _pipeline_process.stdout.close(); _pipeline_process.wait()
            except: pass
            _pipeline_process = None
        _terminate_requested = False
        full_log += "\n🛑 流程已被用户终止！\n"
        yield full_log, None, None, None, gr.update(visible=False), gr.update(visible=False)
        return
    
    with _pipeline_lock:
        _pipeline_process.wait(); ret_code = _pipeline_process.returncode; _pipeline_process = None
    
    if ret_code != 0:
        full_log += "\n❌ COLMAP 失败！\n"
        yield full_log, None, None, None, gr.update(visible=False), gr.update(visible=False)
        return

    # === 阶段 2: 3DGS 训练 ===
    full_log += "\n" + "="*40 + "\n🚀 [阶段 2/3] COLMAP 完成！开始 3DGS 训练 (GPU)...\n" + "="*40 + "\n"
    yield full_log, None, None, None, gr.update(visible=True), gr.update(visible=False)
    
    train_cmd = [sys.executable, f"{GAUSSIAN_DIR}/train.py", "-s", source_dir, "-m", model_dir, "--iterations", str(max_iter), "--save_iterations", str(max_iter)]
    with _pipeline_lock:
        _pipeline_process = subprocess.Popen(train_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=GAUSSIAN_DIR, env=env, bufsize=1)
    
    terminated = False
    for line in iter(_pipeline_process.stdout.readline, ''):
        if not line: break
        if _terminate_requested: terminated = True; break
        clean_line = clean_log_line(line)
        if clean_line.strip():
            full_log += clean_line
            yield full_log, None, None, None, gr.update(visible=True), gr.update(visible=False)
    
    if terminated:
        with _pipeline_lock:
            try: _pipeline_process.terminate(); _pipeline_process.stdout.close(); _pipeline_process.wait()
            except: pass
            _pipeline_process = None
        _terminate_requested = False
        full_log += "\n🛑 流程已被用户终止！\n"
        yield full_log, None, None, None, gr.update(visible=False), gr.update(visible=False)
        return
    
    with _pipeline_lock:
        _pipeline_process.wait(); ret_code = _pipeline_process.returncode; _pipeline_process = None
    
    if ret_code != 0:
        full_log += "\n❌ 训练失败！\n"
        yield full_log, None, None, None, gr.update(visible=False), gr.update(visible=False)
        return

    # === 阶段 3: 后处理 ===
    full_log += "\n" + "="*40 + "\n✂️ [阶段 3/3] 训练完成，后处理中...\n" + "="*40 + "\n"
    yield full_log, None, None, None, gr.update(visible=True), gr.update(visible=False)
    
    from core.processor import process_gaussian_splat
    ply_path = os.path.join(model_dir, f"point_cloud/iteration_{max_iter}/point_cloud.ply")
    if not os.path.exists(ply_path): 
        full_log += "❌ 找不到训练结果\n"
        yield full_log, None, None, None, gr.update(visible=False), gr.update(visible=False)
        return
    
    dgs, rgb, splat, report = process_gaussian_splat(ply_path)
    full_log += f"\n🎉 全流程完成！\n{report}\n\n⚠️ 请及时下载所需文件，上传新数据集将覆盖！"
    yield full_log, dgs, rgb, splat, gr.update(visible=False), gr.update(visible=False)