import cv2
import numpy as np
from paddleocr import PaddleOCR
import re
from typing import Dict, List, Optional, Tuple
import json
import os
import sys
from model_manager import ModelManager

class OCRProcessor:
    def __init__(self, config: dict):
        self.config = config
        
        # 使用模型管理器设置路径
        self.model_manager = ModelManager()
        
        # 使用新的参数名称
        use_angle_cls = config.get('use_angle_cls', True)
        self.ocr = PaddleOCR(
            use_textline_orientation=use_angle_cls,
            lang=config.get('language', 'ch')
        )
        self.field_mappings = config.get('field_mappings', {})
    
    def process_image(self, image: np.ndarray) -> Dict[str, str]:
        """处理图像并提取字段值"""
        try:
            # 如果图像太大，先缩放
            height, width = image.shape[:2]
            max_size = 3000  # 设置最大尺寸限制
            
            if max(height, width) > max_size:
                scale = max_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
            
            # OCR识别
            result = self.ocr.ocr(image)
            
            if not result or not result[0]:
                return {}
            
            # 提取文本
            texts = []
            for line in result[0]:
                if line and len(line) >= 2:
                    # 检查数据结构
                    if isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                        text = line[1][0]
                        texts.append(text)
                    elif isinstance(line[1], str):
                        # 如果直接是字符串
                        text = line[1]
                        texts.append(text)
            
            # 根据字段映射提取值
            extracted_values = {}
            for field_name, mapped_key in self.field_mappings.items():
                value = self._extract_field_value(texts, field_name)
                if value:
                    extracted_values[mapped_key] = value
            
            return extracted_values
            
        except Exception as e:
            print(f"OCR处理错误: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _extract_field_value(self, texts: List[str], field_name: str) -> Optional[str]:
        """从文本列表中提取指定字段的值"""
        # 将所有文本连接成一个字符串
        full_text = " ".join(texts)
        
        # 转义字段名中的特殊字符
        escaped_field_name = re.escape(field_name)
        
        # 扩展的单位匹配模式，包括中文单位
        unit_pattern = r'([A-Za-z%°℃℉\u4e00-\u9fff]*)'
        
        # 查找字段名后的数值 - 支持多种格式
        patterns = [
            # 字段名:数值单位 或 字段名 数值单位
            rf"{escaped_field_name}[:\s]*([0-9]+\.?[0-9]*)\s*{unit_pattern}",
            # 字段名:数值 (无单位)
            rf"{escaped_field_name}[:\s]*([0-9]+\.?[0-9]*)",
            # 数值单位 字段名 (倒序)
            rf"([0-9]+\.?[0-9]*)\s*{unit_pattern}\s*{escaped_field_name}",
            # 字段名(参数):数值
            rf"{escaped_field_name}[:\s]*([0-9]+\.?[0-9]*)",
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, full_text)
            if match:
                value = match.group(1)
                unit = match.group(2) if len(match.groups()) > 1 else ""
                result = f"{value}{unit}".strip()
                return result
        
        # 如果没有找到，尝试在每行文本中查找
        for i, text in enumerate(texts):
            if field_name in text:
                # 查找当前行或下一行的数值
                for j in range(i, min(i + 2, len(texts))):
                    # 扩展数值匹配，支持更多单位格式
                    numbers = re.findall(r'([0-9]+\.?[0-9]*)\s*([A-Za-z%°℃℉\u4e00-\u9fff]*)', texts[j])
                    if numbers:
                        value, unit = numbers[0]
                        result = f"{value}{unit}".strip()
                        return result
        return None
    
    def update_field_mappings(self, mappings: Dict[str, str]):
        """更新字段映射"""
        self.field_mappings = mappings
    
    def get_field_mappings(self) -> Dict[str, str]:
        """获取当前字段映射"""
        return self.field_mappings.copy()
    
    def add_field_mapping(self, field_name: str, mapped_key: str):
        """添加字段映射"""
        self.field_mappings[field_name] = mapped_key
    
    def remove_field_mapping(self, field_name: str):
        """删除字段映射"""
        if field_name in self.field_mappings:
            del self.field_mappings[field_name]
