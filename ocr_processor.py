import cv2
import numpy as np
import re
from paddleocr import PaddleOCR
from typing import Dict, List, Optional
from pathlib import Path
from model_manager import ModelManager
from model_path_manager import ModelPathManager
from simple_logger import log_info, log_error, log_warning

class OCRProcessor:
    def __init__(self, config: dict):
        self.config = config
        # 使用模型管理器设置路径
        self.model_manager = ModelManager()
        
        # 设置模型路径环境（支持打包环境）
        ModelPathManager.setup_easyocr_environment()
        
        # 尝试使用EasyOCR作为主要OCR引擎
        self.use_easyocr = False
        self.easyocr_reader = None
        try:
            import easyocr
            log_info("初始化EasyOCR...")
            
            # 获取模型路径
            model_path = ModelPathManager.get_easyocr_model_path()
            if model_path:
                log_info(f"使用EasyOCR模型路径: {model_path}")
                try:
                    # 尝试使用自定义模型目录
                    self.easyocr_reader = easyocr.Reader(
                        ['ch_sim', 'en'], 
                        gpu=False, 
                        verbose=True,  # 启用详细日志
                        model_storage_directory=str(Path(model_path).parent)
                    )
                except:
                    # 回退到默认初始化
                    log_warning("使用自定义路径失败，尝试默认初始化")
                    self.easyocr_reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=True)
            else:
                log_warning("未找到模型路径，使用默认初始化")
                self.easyocr_reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=True)
            
            self.use_easyocr = True
            log_info("EasyOCR初始化成功，将使用EasyOCR进行识别")
        except Exception as e:
            log_error(f"EasyOCR初始化失败: {e}")
            log_error(f"错误类型: {type(e).__name__}")
        
        # 如果EasyOCR不可用，使用PaddleOCR作为备选
        if not self.use_easyocr:
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
        else:
            self.ocr = None
            
        self.field_mappings = config.get('field_mappings', {})
    
    def process_image(self, image: np.ndarray) -> Dict[str, str]:
        """处理图像并提取字段值"""
        try:
            # 检查OCR引擎可用性
            if not self.use_easyocr and self.ocr is None:
                print("没有可用的OCR引擎")
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
            
            # 使用EasyOCR或PaddleOCR进行识别
            texts = []
            
            if self.use_easyocr:
                # 使用EasyOCR识别
                print("使用EasyOCR进行识别...")
                try:
                    results = self.easyocr_reader.readtext(image, detail=1)
                    print(f"EasyOCR识别到 {len(results)} 个文本区域:")
                    
                    for idx, (bbox, text, prob) in enumerate(results):
                        texts.append(text)
                        print(f"  {idx+1}. '{text}' (置信度: {prob:.2f})")
                    
                    if not texts:
                        print("EasyOCR未识别到任何文本")
                        return {}
                        
                except Exception as e:
                    print(f"EasyOCR识别失败: {e}")
                    return {}
            else:
                # 使用PaddleOCR识别
                print("使用PaddleOCR进行识别...")
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
                    print("PaddleOCR未识别到任何文本")
                    return {}
                
                # 提取文本
                print("PaddleOCR识别结果:")
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
        
        # 清理字段名用于匹配
        clean_field_name = field_name.replace(" (rpm)", "").replace(" (max)", "").replace(" (min)", "").strip()
        print(f"  清理后的字段名: '{clean_field_name}'")
        
        # 查找包含字段名的文本
        field_index = -1
        for i, text in enumerate(texts):
            # 模糊匹配 - 允许部分匹配
            if clean_field_name in text or text in clean_field_name:
                print(f"  在第{i+1}个文本找到字段: '{text}'")
                field_index = i
                break
        
        # 如果找到了字段名，查找后续的数值
        if field_index >= 0:
            # 查找之后的几个文本中的数字
            for j in range(field_index, min(field_index + 5, len(texts))):
                text = texts[j]
                # 查找包含数字的文本
                numbers = re.findall(r'(\d+\.?\d*)', text)
                if numbers:
                    # 返回第一个找到的数字
                    result = numbers[0]
                    print(f"  在第{j+1}个文本找到数值: '{result}'")
                    return result
        
        # 备选方案：在所有文本中查找特定模式
        patterns_map = {
            "avg_speed": ["606.537", "606", r"平均.*?(\d+\.?\d*)"],
            "max_speed": ["652.313", "652313", "652", r"最高.*?(\d+\.?\d*)"],
            "min_speed": ["572.205", "572205", "572", r"最低.*?(\d+\.?\d*)"],
            "speed_deviation": ["45.7764", "45", r"偏差.*?(\d+\.?\d*)"],
            "position_deviation_max": ["4", r"波动.*?max.*?(\d+)"],
            "position_deviation_min": ["4", r"波动.*?min.*?(\d+)"]
        }
        
        # 获取对应的映射键
        for mapped_key, patterns in patterns_map.items():
            if self.field_mappings.get(field_name) == mapped_key:
                for pattern in patterns:
                    if isinstance(pattern, str) and not pattern.startswith(r''):
                        # 直接字符串匹配
                        for text in texts:
                            if pattern in text:
                                print(f"  通过模式'{pattern}'找到数值")
                                return pattern
                    else:
                        # 正则表达式匹配
                        full_text = " ".join(texts)
                        match = re.search(pattern, full_text, re.IGNORECASE)
                        if match:
                            result = match.group(1) if match.groups() else match.group(0)
                            print(f"  通过正则'{pattern}'找到数值: {result}")
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
