# Watermark/Subtitle Remover Core Module
import cv2
import numpy as np
from pathlib import Path
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class WatermarkDetector:
    """智能水印/字幕检测器"""
    
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.frame_sample_rate = 30  # 每隔30帧取一帧检测
    
    def detect(self, video_path: str) -> List[Tuple[int, int, int, int]]:
        """
        检测视频中的水印/字幕区域
        返回: [(x1, y1, x2, y2), ...] 多个检测到的区域
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 收集所有检测到的区域
        all_regions = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 每隔frame_sample_rate帧检测一次
            if frame_count % self.frame_sample_rate == 0:
                regions = self._detect_regions_in_frame(frame)
                all_regions.extend(regions)
            
            frame_count += 1
        
        cap.release()
        
        # 合并重叠区域
        merged_regions = self._merge_overlapping_regions(all_regions)
        
        logger.info(f"Detected {len(merged_regions)} watermark/subtitle regions")
        return merged_regions
    
    def _detect_regions_in_frame(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """检测单帧中的水印/字幕区域"""
        regions = []
        
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 方法1: 检测边缘（字幕通常是规则的边缘）
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 过滤太小的区域（可能是噪点）
            if w > 50 and h > 10 and w < frame.shape[1] * 0.8:
                # 检查是否是横向的长条形（字幕特征）
                aspect_ratio = w / h
                if aspect_ratio > 3:  # 长宽比大于3认为是字幕
                    regions.append((x, y, x + w, y + h))
        
        # 方法2: 检测文字区域（使用形态学操作）
        # 自适应阈值
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 形态学闭操作，连接相邻的文字
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        contours2, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours2:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 80 and h > 8 and h < 100:
                regions.append((x, y, x + w, y + h))
        
        return regions
    
    def _merge_overlapping_regions(self, regions: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """合并重叠或接近的区域"""
        if not regions:
            return []
        
        # 按x坐标排序
        regions = sorted(regions, key=lambda r: (r[1], r[0]))
        merged = [regions[0]]
        
        for current in regions:
            last = merged[-1]
            
            # 计算重叠度
            x1 = min(last[0], current[0])
            y1 = min(last[1], current[1])
            x2 = max(last[2], current[2])
            y2 = max(last[3], current[3])
            
            # 检查是否有足够的重叠（IoU > 0.3）或水平位置接近
            last_width = last[2] - last[0]
            last_height = last[3] - last[1]
            overlap_w = max(0, min(last[2], current[2]) - max(last[0], current[0]))
            overlap_h = max(0, min(last[3], current[3]) - max(last[1], current[1]))
            
            iou = (overlap_w * overlap_h) / ((last_width * last_height) + 1)
            
            # 如果重叠度>0.3或y坐标接近（在同一水平线上），合并
            if iou > 0.3 or (abs(current[1] - last[1]) < 20 and abs(current[3] - last[3]) < 20):
                merged[-1] = (x1, y1, x2, y2)
            else:
                merged.append(current)
        
        return merged


class WatermarkRemover:
    """水印/字幕去除器"""
    
    def __init__(self):
        self.blur_kernel = (30, 30)
        self.inpaint_radius = 3
    
    def remove_with_ffmpeg(
        self, 
        input_path: str, 
        output_path: str, 
        regions: List[Tuple[int, int, int, int]]
    ) -> str:
        """
        使用FFmpeg去除水印/字幕
        regions: [(x1, y1, x2, y2), ...] 要去除的区域
        """
        import subprocess
        
        if not regions:
            # 没有区域，直接复制
            cmd = ['ffmpeg', '-i', input_path, '-c', 'copy', output_path, '-y']
        else:
            # 构建filter_complex
            filter_str = self._build_multi_region_filter(regions)
            
            cmd = [
                'ffmpeg', '-i', input_path,
                '-vf', filter_str,
                '-c:a', 'copy',
                output_path, '-y'
            ]
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg processing failed: {result.stderr}")
        
        return output_path
    
    def _build_multi_region_filter(self, regions: List[Tuple[int, int, int, int]]) -> str:
        """构建多区域滤镜"""
        # 使用delogo滤镜（支持多区域）
        delogo_parts = []
        for x1, y1, x2, y2 in regions:
            delogo_parts.append(f"delogo=x={x1}:y={y1}:w={x2-x1}:h={y2-y1}")
        
        return ",".join(delogo_parts) if delogo_parts else "[0:v]copy[out]"
    
    def remove_with_opencv(
        self, 
        video_path: str, 
        output_path: str, 
        regions: List[Tuple[int, int, int, int]]
    ) -> str:
        """
        使用OpenCV修复去除水印（逐帧处理）
        """
        cap = cv2.VideoCapture(video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 修复每个区域
            for x1, y1, x2, y2 in regions:
                # 确保坐标在有效范围内
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width, x2), min(height, y2)
                
                if x2 > x1 and y2 > y1:
                    # 提取水印区域
                    roi = frame[y1:y2, x1:x2]
                    
                    # 使用高斯模糊
                    blurred = cv2.GaussianBlur(roi, (51, 51), 0)
                    
                    # 如果区域足够大，使用inpaint
                    if (x2 - x1) > 20 and (y2 - y1) > 10:
                        mask = np.zeros(roi.shape[:2], dtype=np.uint8)
                        mask.fill(255)
                        try:
                            inpainted = cv2.inpaint(roi, mask, 3, cv2.INPAINT_TELEA)
                            frame[y1:y2, x1:x2] = inpainted
                        except:
                            frame[y1:y2, x1:x2] = blurred
                    else:
                        frame[y1:y2, x1:x2] = blurred
            
            out.write(frame)
            frame_count += 1
        
        cap.release()
        out.release()
        
        return output_path
    
    def process(
        self, 
        input_path: str, 
        output_path: str, 
        regions: List[Tuple[int, int, int, int]],
        method: str = "ffmpeg"
    ) -> str:
        """
        处理视频去除水印/字幕
        method: "ffmpeg" 或 "opencv"
        """
        if method == "ffmpeg":
            return self.remove_with_ffmpeg(input_path, output_path, regions)
        else:
            return self.remove_with_opencv(input_path, output_path, regions)
