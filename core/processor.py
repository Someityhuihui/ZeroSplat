# -*- coding: utf-8 -*-
import numpy as np
from plyfile import PlyData, PlyElement
import os

def convert_ply_to_splat(ply_path, output_path):
    plydata = PlyData.read(ply_path)
    v = plydata['vertex'].data
    pos = np.vstack([v['x'], v['y'], v['z']]).T
    scales = np.exp(np.vstack([v['scale_0'], v['scale_1'], v['scale_2']])).T
    rot = np.vstack([v['rot_0'], v['rot_1'], v['rot_2'], v['rot_3']]).T
    rot = rot / np.linalg.norm(rot, axis=1, keepdims=True)
    SH_C0 = 0.28209479177387814
    dc = np.vstack([v['f_dc_0'], v['f_dc_1'], v['f_dc_2']]).T
    rgb = np.clip((dc * SH_C0 + 0.5) * 255, 0, 255).astype(np.uint8)
    opacity = np.clip((1.0 / (1.0 + np.exp(-v['opacity']))) * 255, 0, 255).astype(np.uint8)
    rgba = np.hstack([rgb, opacity.reshape(-1, 1)])
    rot_uint8 = np.clip((rot + 1.0) * 0.5 * 255, 0, 255).astype(np.uint8)
    dtype = np.dtype([('pos', np.float32, (3,)), ('scale', np.float32, (3,)), ('rgba', np.uint8, (4,)), ('rot', np.uint8, (4,))])
    buffer = np.empty(len(pos), dtype=dtype)
    buffer['pos'] = pos; buffer['scale'] = scales; buffer['rgba'] = rgba; buffer['rot'] = rot_uint8
    with open(output_path, 'wb') as f: f.write(buffer.tobytes())
    return output_path

def process_gaussian_splat(input_ply, opacity_thresh=0.01, roi_radius=10.0, max_distance=30.0, export_rgb=True):
    plydata = PlyData.read(input_ply)
    vertex_data = plydata['vertex'].data
    original_count = len(vertex_data)
    raw_opacity = vertex_data['opacity']
    alpha = 1.0 / (1.0 + np.exp(-raw_opacity))
    positions = np.vstack([vertex_data['x'], vertex_data['y'], vertex_data['z']]).T
    roi_center = np.mean(positions, axis=0)
    distances = np.linalg.norm(positions - roi_center, axis=1)
    progressive_threshold = opacity_thresh + (1.0 - opacity_thresh) * np.clip(distances / roi_radius, 0, 1)
    final_mask = (alpha >= progressive_threshold) & (distances <= max_distance)
    pruned_data = vertex_data[final_mask]
    pruned_count = len(pruned_data)
    removal_percentage = ((original_count - pruned_count) / original_count) * 100
    
    base_name = os.path.splitext(os.path.basename(input_ply))[0]
    pruned_3dgs_path = os.path.join(os.path.dirname(input_ply), f"{base_name}_pruned.ply")
    PlyData([PlyElement.describe(pruned_data, 'vertex')]).write(pruned_3dgs_path)
    
    splat_path = os.path.join(os.path.dirname(input_ply), f"{base_name}_web.splat")
    convert_ply_to_splat(pruned_3dgs_path, splat_path)
    
    rgb_path = None
    if export_rgb:
        C0 = 0.28209479177387814
        r = np.clip((pruned_data['f_dc_0'] * C0 + 0.5) * 255, 0, 255).astype(np.uint8)
        g = np.clip((pruned_data['f_dc_1'] * C0 + 0.5) * 255, 0, 255).astype(np.uint8)
        b = np.clip((pruned_data['f_dc_2'] * C0 + 0.5) * 255, 0, 255).astype(np.uint8)
        pure_vertices = np.empty(pruned_count, dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')])
        pure_vertices['x'] = pruned_data['x']; pure_vertices['y'] = pruned_data['y']; pure_vertices['z'] = pruned_data['z']
        pure_vertices['red'] = r; pure_vertices['green'] = g; pure_vertices['blue'] = b
        rgb_path = os.path.join(os.path.dirname(input_ply), f"{base_name}_rgb.ply")
        PlyData([PlyElement.describe(pure_vertices, 'vertex')]).write(rgb_path)
        
    report = f"✅ 处理完成！\n📊 原始高斯球: {original_count:,}\n✂️ 删除废点: {original_count - pruned_count:,} ({removal_percentage:.2f}%)\n🎯 保留高斯球: {pruned_count:,}"
    return pruned_3dgs_path, rgb_path, splat_path, report