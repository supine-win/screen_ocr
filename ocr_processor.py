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
        
        # 使用PaddleOCR 3.2.0的新功能和优化设置
        try:
            lang = config.get('language', 'ch')
            print(f"初始化PaddleOCR 3.2.0，语言: {lang}")
            
            # PaddleOCR 3.2.0针对中文优化的配置
            self.ocr = PaddleOCR(
                use_angle_cls=False,     # 禁用角度分类，提高稳定性
                lang='ch',               # 强制使用中文
                # 针对中文文本优化的参数
                det_limit_side_len=1280, # 增加检测边长限制
                det_limit_type='max',    
                # 降低检测阈值，提高敏感度
                det_db_thresh=0.2,       # 降低检测阈值
                det_db_box_thresh=0.3,   # 降低框检测阈值
                det_db_unclip_ratio=2.0, # 增加检测框扩展比例
            )
            print("PaddleOCR 3.2.0初始化成功")
        except Exception as e:
            print(f"PaddleOCR初始化失败: {e}")
            self.ocr = None
            
        self.field_mappings = config.get('field_mappings', {})
    
    def process_image(self, image: np.ndarray) -> Dict[str, str]:
        """处理图像并提取字段值"""
        try:
            if self.ocr is None:
                print("OCR引擎未初始化")
                return {}
            
            # 针对中文字符优化的图像预处理
            height, width = image.shape[:2]
            print(f"原始图像尺寸: {image.shape}")
            
            # 确保图像有足够的分辨率用于中文识别
            target_height = 600
            if height < target_height:
                scale = target_height / height
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                print(f"图像放大到: {image.shape}")
            
            # 专门针对中文字符的图像处理
            if len(image.shape) == 3:
                # 1. 转换为灰度图进行处理
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # 2. 使用高斯模糊去噪
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
                
                # 3. 自适应阈值处理，更适合中文字符
                adaptive_thresh = cv2.adaptiveThreshold(
                    blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
                
                # 4. 形态学操作，改善字符连通性
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                processed = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
                
                # 5. 转回BGR格式
                processed_image = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
            else:
                processed_image = image
            
            # 保存处理后的图像用于调试
            cv2.imwrite("debug_chinese_optimized.jpg", processed_image)
            print("已保存中文优化处理后的图像: debug_chinese_optimized.jpg")
            
            print(f"最终处理图像尺寸: {processed_image.shape}")
            
            # 尝试多种图像进行OCR识别
            images_to_try = [
                ("原始图像", image),
                ("处理后图像", processed_image)
            ]
            
            result = None
            for img_name, img in images_to_try:
                print(f"尝试OCR识别: {img_name}")
                try:
                    result = self.ocr.ocr(img)
                    if result and result[0]:
                        print(f"使用{img_name}识别成功")
                        break
                except Exception as e:
                    print(f"{img_name}识别失败: {e}")
                    continue
            
            if not result or not result[0]:
                print("OCR未识别到任何文本")
                return {}
            
            # 提取文本并打印调试信息
            texts = []
            print("OCR识别结果:")
            for i, line in enumerate(result[0]):
                if line and len(line) >= 2:
                    # 检查数据结构
                    if isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        texts.append(text)
                        print(f"  {i+1}: '{text}' (置信度: {confidence:.2f})")
                    elif isinstance(line[1], str):
                        # 如果直接是字符串
                        text = line[1]
                        texts.append(text)
                        print(f"  {i+1}: '{text}'")
            
            # 根据字段映射提取值
            extracted_values = {}
            print(f"开始字段匹配，映射: {self.field_mappings}")
            
            for field_name, mapped_key in self.field_mappings.items():
                print(f"查找字段: '{field_name}'")
                value = self._extract_field_value(texts, field_name)
                if value:
                    extracted_values[mapped_key] = value
                    print(f"  找到: {mapped_key} = {value}")
                else:
                    print(f"  未找到字段 '{field_name}'")
            
            print(f"最终结果: {extracted_values}")
            return extracted_values
            
        except Exception as e:
            print(f"OCR处理错误: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _extract_field_value(self, texts: List[str], field_name: str) -> Optional[str]:
        """从文本列表中提取指定字段的值"""
        print(f"  查找字段 '{field_name}' 在文本中...")
        
        # 将所有文本连接成一个字符串
        full_text = " ".join(texts)
        print(f"  完整文本: {full_text}")
        
        # 尝试多种匹配方式
        # 1. 精确匹配（包含冒号）
        for i, text in enumerate(texts):
            if field_name in text and ":" in text:
                print(f"  在第{i+1}行找到字段: '{text}'")
                # 提取冒号后的数值
                parts = text.split(":")
                if len(parts) > 1:
                    value_part = parts[1].strip()
                    # 提取数字
                    numbers = re.findall(r'([0-9]+\.?[0-9]*)', value_part)
                    if numbers:
                        result = numbers[0]
                        print(f"  提取到数值: {result}")
                        return result
        
        # 2. 模糊匹配（去掉括号和冒号）
        clean_field_name = field_name.replace(" (rpm)", "").replace(" (max)", "").replace(" (min)", "")
        print(f"  尝试模糊匹配: '{clean_field_name}'")
        
        for i, text in enumerate(texts):
            if clean_field_name in text:
                print(f"  模糊匹配在第{i+1}行: '{text}'")
                # 查找当前行和下一行的数值
                for j in range(i, min(i + 3, len(texts))):
                    numbers = re.findall(r'([0-9]+\.?[0-9]*)', texts[j])
                    if numbers:
                        result = numbers[0]
                        print(f"  在第{j+1}行找到数值: {result}")
                        return result
        
        # 3. 关键词匹配
        keywords = {
            "平均速度": ["平均", "avg"],
            "最高速度": ["最高", "最大", "max"],
            "最低速度": ["最低", "最小", "min"],
            "速度偏差": ["偏差", "deviation"],
            "位置波动": ["波动", "位置"]
        }
        
        for key_field, keywords_list in keywords.items():
            if key_field in field_name:
                for keyword in keywords_list:
                    for i, text in enumerate(texts):
                        if keyword in text:
                            print(f"  关键词'{keyword}'匹配在第{i+1}行: '{text}'")
                            # 查找数值
                            for j in range(i, min(i + 2, len(texts))):
                                numbers = re.findall(r'([0-9]+\.?[0-9]*)', texts[j])
                                if numbers:
                                    result = numbers[0]
                                    print(f"  找到数值: {result}")
                                    return result
        
        print(f"  未找到字段 '{field_name}' 的值")
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
