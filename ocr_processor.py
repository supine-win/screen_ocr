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
            # OCR识别
            result = self.ocr.ocr(image, cls=True)
            
            if not result or not result[0]:
                return {}
            
            # 提取文本
            texts = []
            for line in result[0]:
                if line and len(line) >= 2:
                    texts.append(line[1][0])
            
            # 根据字段映射提取值
            extracted_values = {}
            for field_name, mapped_key in self.field_mappings.items():
                value = self._extract_field_value(texts, field_name)
                if value:
                    extracted_values[mapped_key] = value
            
            return extracted_values
            
        except Exception as e:
            print(f"OCR处理错误: {e}")
            return {}
    
    def _extract_field_value(self, texts: List[str], field_name: str) -> Optional[str]:
        """从文本列表中提取指定字段的值"""
        # 将所有文本连接成一个字符串
        full_text = " ".join(texts)
        
        # 查找字段名后的数值
        patterns = [
            rf"{field_name}[:\s]*([0-9]+\.?[0-9]*)\s*([A-Za-z%°℃℉]*)",
            rf"{field_name}[:\s]*([0-9]+\.?[0-9]*)",
            rf"([0-9]+\.?[0-9]*)\s*([A-Za-z%°℃℉]*)\s*{field_name}",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                value = match.group(1)
                unit = match.group(2) if len(match.groups()) > 1 else ""
                return f"{value}{unit}".strip()
        
        # 如果没有找到，尝试在每行文本中查找
        for i, text in enumerate(texts):
            if field_name in text:
                # 查找当前行或下一行的数值
                for j in range(i, min(i + 2, len(texts))):
                    numbers = re.findall(r'([0-9]+\.?[0-9]*)\s*([A-Za-z%°℃℉]*)', texts[j])
                    if numbers:
                        value, unit = numbers[0]
                        return f"{value}{unit}".strip()
        
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
