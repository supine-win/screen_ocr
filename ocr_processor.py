import cv2
import numpy as np
import re
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys
from model_path_manager import ModelPathManager
from simple_logger import log_info, log_error, log_warning

class OCRProcessor:
    def __init__(self, config: dict):
        self.config = config
        
        # EasyOCR-only版本，移除PaddleOCR支持
        self.easyocr_reader = None
        try:
            import easyocr
            log_info("初始化EasyOCR...")
            
            # 统一的模型路径管理
            ModelPathManager.setup_easyocr_environment(config)
            reader_params = ModelPathManager.get_easyocr_reader_params(config)
            
            easyocr_config = self.config.get('easyocr', {})
            use_gpu = easyocr_config.get('use_gpu', False)
            verbose = easyocr_config.get('verbose', False)  # 减少冗余日志
            
            # 使用ModelPathManager提供的参数作为基础
            base_params = {
                'lang_list': ['ch_sim', 'en'],
                'gpu': use_gpu,
                'verbose': verbose,
            }
            
            # 合并ModelPathManager的参数
            base_params.update(reader_params)
            
            # 移除None值的参数并只输出关键信息
            base_params = {k: v for k, v in base_params.items() if v is not None}
            log_info(f"EasyOCR GPU设置: {use_gpu}")
            log_info(f"模型存储目录: {base_params.get('model_storage_directory', './easyocr_models')}")
            log_info(f"EasyOCR初始化参数: {base_params}")
            
            try:
                # 在打包环境中，强制禁用网络访问
                if getattr(sys, 'frozen', False):
                    # 完全离线模式初始化
                    log_info("打包环境：启用完全离线模式")

                    # 1. 彻底屏蔽所有网络模块
                    import urllib.request
                    import urllib.parse
                    import urllib.error
                    import socket
                    import ssl

                    # 保存原始函数
                    original_urlopen = urllib.request.urlopen
                    original_urlretrieve = urllib.request.urlretrieve
                    original_socket_create = socket.socket

                    def blocked_network(*args, **kwargs):
                        raise urllib.error.URLError("Network access blocked in packaged mode")

                    def blocked_socket(*args, **kwargs):
                        raise socket.error("Socket access blocked in packaged mode")

                    # 屏蔽网络访问
                    urllib.request.urlopen = blocked_network
                    urllib.request.urlretrieve = blocked_network
                    socket.socket = blocked_socket

                    try:
                        # 2. 设置完全离线的环境变量
                        os.environ['EASYOCR_OFFLINE_MODE'] = 'true'
                        os.environ['EASYOCR_DOWNLOAD_ENABLED'] = 'false'
                        os.environ['TORCH_HOME'] = base_params.get('model_storage_directory', '')

                        # 3. CPU模式下禁用各种优化以避免网络调用
                        if not use_gpu:
                            import warnings
                            warnings.filterwarnings("ignore")
                            os.environ['CUDA_VISIBLE_DEVICES'] = ''

                        # 4. 获取实际的模型路径
                        base_storage_dir = base_params.get('model_storage_directory')

                        # 检查可能的模型目录
                        possible_model_dirs = [
                            Path(base_storage_dir) / "_internal" / "easyocr_models",
                            Path(base_storage_dir) / "easyocr_models",
                            Path(base_storage_dir).parent / "easyocr_models"
                        ]

                        actual_model_dir = None
                        for model_dir in possible_model_dirs:
                            if model_dir.exists():
                                models = list(model_dir.glob("*.pth"))
                                if models:
                                    actual_model_dir = model_dir
                                    log_info(f"找到模型目录: {actual_model_dir} (包含{len(models)}个模型文件)")
                                    break

                        if not actual_model_dir:
                            raise Exception("无法找到包含模型文件的目录")

                        # 5. 检查必要的模型文件
                        craft_models = list(actual_model_dir.glob("craft_*.pth"))
                        text_models = (list(actual_model_dir.glob("*_sim_*.pth")) + 
                                     list(actual_model_dir.glob("*_g2.pth")) +
                                     list(actual_model_dir.glob("chinese*.pth")))

                        log_info(f"检查模型文件: craft模型={len(craft_models)}, 文本模型={len(text_models)}")

                        if not craft_models:
                            raise Exception("未找到必要的检测模型 (craft_*.pth)")
                        if not text_models:
                            raise Exception("未找到必要的识别模型")

                        log_info("✅ 所有必要的离线模型文件都已找到")

                        # 6. 配置完全离线的初始化参数
                        # 使用模型目录的父目录作为存储目录，这样EasyOCR能找到.EasyOCR子目录
                        offline_storage_dir = str(actual_model_dir.parent)

                        offline_params = {
                            'lang_list': ['ch_sim', 'en'],
                            'gpu': False,  # 强制CPU模式确保稳定
                            'verbose': False,  # 完全关闭verbose避免触发下载
                            'model_storage_directory': offline_storage_dir,
                            'download_enabled': False  # 如果支持的话
                        }

                        log_info(f"离线模式参数: {offline_params}")

                        # 7. 创建EasyOCR期望的目录结构（如果不存在）
                        easyocr_home = Path(offline_storage_dir) / ".EasyOCR"
                        easyocr_model_subdir = easyocr_home / "model"
                        easyocr_model_subdir.mkdir(parents=True, exist_ok=True)

                        # 确保模型文件在EasyOCR期望的位置
                        for model_file in actual_model_dir.glob("*.pth"):
                            target_file = easyocr_model_subdir / model_file.name
                            if not target_file.exists():
                                try:
                                    target_file.hardlink_to(model_file)
                                except:
                                    import shutil
                                    shutil.copy2(model_file, target_file)

                        log_info(f"EasyOCR模型结构准备完成: {easyocr_home}")

                        # 8. 尝试离线初始化
                        self.easyocr_reader = easyocr.Reader(**offline_params)
                        log_info("✅ 打包环境EasyOCR初始化成功（完全离线模式）")

                    except Exception as offline_error:
                        log_error(f"离线模式初始化失败: {offline_error}")

                        # 最后的回退：尝试最简单的初始化（仅使用语言列表）
                        try:
                            log_warning("尝试最简单的回退初始化...")
                            # 只使用最基本的参数
                            minimal_params = ['ch_sim', 'en']
                            self.easyocr_reader = easyocr.Reader(minimal_params, gpu=False, verbose=False)
                            log_info("✅ 打包环境EasyOCR最简回退初始化成功")
                        except Exception as final_error:
                            log_error(f"所有离线初始化方式都失败: {final_error}")
                            log_error("请检查模型文件是否正确安装在_internal/easyocr_models目录中")
                            self.easyocr_reader = None
                    finally:
                        # 恢复网络函数（避免影响其他组件）
                        urllib.request.urlopen = original_urlopen
                        urllib.request.urlretrieve = original_urlretrieve
                        socket.socket = original_socket_create

                else:
                    # 开发环境正常初始化
                    self.easyocr_reader = easyocr.Reader(**base_params)
                    log_info("开发环境EasyOCR初始化成功")

            except Exception as e:
                log_error(f"EasyOCR主要初始化流程失败: {e}")
                # 不再进行回退尝试，直接设置为None
                self.easyocr_reader = None
            
            # 只有在真正初始化成功时才显示成功信息
            if self.easyocr_reader is not None:
                log_info("✅ EasyOCR初始化成功，引擎可用")
            else:
                log_error("❌ EasyOCR初始化失败，引擎不可用")
        except Exception as e:
            log_error(f"EasyOCR初始化失败: {e}")
            log_error(f"错误类型: {type(e).__name__}")
            raise Exception(f"EasyOCR初始化失败，无法继续运行: {e}")
            
        self.field_mappings = config.get('field_mappings', {})
        self.use_absolute_value = config.get('use_absolute_value', False)
    
    def process_image(self, image: np.ndarray) -> Dict[str, str]:
        """处理图像并提取字段值"""
        try:
            # 检查EasyOCR引擎可用性
            if self.easyocr_reader is None:
                log_error("EasyOCR引擎不可用")
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
            
            # 使用EasyOCR进行识别
            texts = []
            log_info("使用EasyOCR进行识别...")
            try:
                results = self.easyocr_reader.readtext(image, detail=1)
                log_info(f"EasyOCR识别到 {len(results)} 个文本区域:")
                
                for idx, (bbox, text, prob) in enumerate(results):
                    texts.append(text)
                    log_info(f"  {idx+1}. '{text}' (置信度: {prob:.2f})")
                
                if not texts:
                    log_warning("EasyOCR未识别到任何文本")
                    return {}
                    
            except Exception as e:
                log_error(f"EasyOCR识别失败: {e}")
                return {}
            
            # 根据字段映射提取值 - 支持一对多映射
            extracted_values = {}
            print(f"开始字段匹配，映射: {self.field_mappings}")
            
            for field_name, mapped_keys in self.field_mappings.items():
                print(f"查找字段: '{field_name}'")
                value = self._extract_field_value(texts, field_name)
                
                # 支持向后兼容：mapped_keys可以是字符串或数组
                if isinstance(mapped_keys, str):
                    mapped_keys = [mapped_keys]
                elif not isinstance(mapped_keys, list):
                    print(f"  警告: 字段 '{field_name}' 的映射格式错误，跳过")
                    continue
                
                if value:
                    # 处理数值（绝对值等）
                    processed_value = self._process_numeric_value(value)
                    
                    # 将相同的值设置到所有映射的key中
                    for mapped_key in mapped_keys:
                        extracted_values[mapped_key] = processed_value
                        print(f"  找到: {mapped_key} = {processed_value}")
                else:
                    # 为未找到的字段，所有映射的key都设置为None
                    for mapped_key in mapped_keys:
                        extracted_values[mapped_key] = None
                        print(f"  未找到字段 '{field_name}' -> {mapped_key} = None")
            
            print(f"最终结果: {extracted_values}")
            return extracted_values
            
        except Exception as e:
            print(f"OCR处理错误: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _extract_field_value(self, texts: List[str], field_name: str) -> Optional[str]:
        """从文本列表中提取指定字段的值"""
        log_info(f"  查找字段 '{field_name}' 在文本中...")

        # 方法1：使用模式匹配全文
        result = self._extract_with_patterns(texts, field_name)
        if result:
            return result
        
        # 方法2：逐个分析文本片段
        for i, text in enumerate(texts):
            log_info(f"  分析文本片段 {i+1}: '{text}'")
            result = self._extract_value_from_text(text, field_name)
            if result:
                log_info(f"  在文本片段 {i+1} 找到数值: {result}")
                return result
        
        # 方法3：跨片段组合匹配（处理OCR拆分字段的情况）
        result = self._extract_cross_fragment(texts, field_name)
        if result:
            return result
        
        # 方法4：后备方案
        result = self._fallback_extraction(texts, field_name)
        if result:
            return result
        
        log_warning(f"  未找到字段 '{field_name}' 的值")
        return None
    
    def _extract_value_from_text(self, text: str, field_name: str) -> Optional[str]:
        """从单个文本中精确提取字段值 - 基于配置动态生成模式"""
        
        # 动态生成正则模式，基于字段名
        patterns = self._generate_field_patterns(field_name)
        
        # 尝试匹配所有模式
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _generate_field_patterns(self, field_name: str) -> List[str]:
        """基于字段名动态生成匹配模式"""
        patterns = []
        
        # 转义特殊字符，用于正则表达式
        escaped_field = re.escape(field_name)
        
        # 去掉括号内容的基础字段名
        base_field = field_name
        for suffix in [" (rpm)", " (max)", " (min)", "（rpm）", "（max）", "（min）"]:
            base_field = base_field.replace(suffix, "")
        
        escaped_base = re.escape(base_field)
        
        # 1. 精确匹配完整字段名（支持负数）
        patterns.append(rf'{escaped_field}[：:\s]*(-?\d+\.?\d*)')
        
        # 2. 处理中英文括号差异（支持负数）
        normalized_field = field_name.replace("(", "[（(]").replace(")", "[）)]")
        normalized_field = re.escape(normalized_field).replace(r'\[（\(]', '[（(]').replace(r'\[）\)]', '[）)]')
        patterns.append(rf'{normalized_field}[：:\s]*(-?\d+\.?\d*)')
        
        # 3. 基础字段名匹配（去掉括号部分）- 仅当没有max/min区分时使用（支持负数）
        if base_field != field_name and not any(keyword in field_name for keyword in ["max", "min", "最大", "最小"]):
            patterns.append(rf'{escaped_base}[：:\s]*(-?\d+\.?\d*)')
        
        # 4. 特殊处理：如果字段包含特定关键词，生成更宽泛的模式（支持负数）
        if any(keyword in field_name for keyword in ["max", "min", "最大", "最小"]):
            # 提取关键词
            if "(max)" in field_name or "（max）" in field_name:
                patterns.append(rf'{escaped_base}.*?max.*?[：:\s]*(-?\d+\.?\d*)')
            elif "(min)" in field_name or "（min）" in field_name:
                patterns.append(rf'{escaped_base}.*?min.*?[：:\s]*(-?\d+\.?\d*)')
        
        return patterns
    
    def _process_numeric_value(self, value: str) -> str:
        """处理数值：根据配置决定是否取绝对值"""
        if not value:
            return value
            
        try:
            # 提取完整的数字（包括负号）
            import re
            match = re.search(r'(-?\d+\.?\d*)', value)
            if match:
                number_str = match.group(1)
                if self.use_absolute_value:
                    # 取绝对值，保持原始数据类型
                    if '.' in number_str:
                        # 浮点数
                        abs_value = str(abs(float(number_str)))
                    else:
                        # 整数
                        abs_value = str(abs(int(number_str)))
                    log_info(f"  数值处理：{number_str} -> {abs_value} (取绝对值)")
                    return abs_value
                else:
                    # 保留原始值（包括负号）
                    log_info(f"  数值处理：保留原始值 {number_str}")
                    return number_str
            return value
        except Exception as e:
            log_warning(f"  数值处理出错: {e}, 返回原始值: {value}")
            return value
    
    def _extract_cross_fragment(self, texts: List[str], field_name: str) -> Optional[str]:
        """跨片段匹配：处理OCR将字段拆分成多个片段的情况"""
        
        # 提取字段关键信息
        base_field = field_name
        field_suffix = ""
        
        for suffix in [" (max)", " (min)", "（max）", "（min）"]:
            if suffix in field_name:
                field_suffix = suffix.replace(" ", "").replace("（", "").replace("）", "").replace("(", "").replace(")", "")
                base_field = base_field.replace(suffix, "")
                break
        
        log_info(f"  跨片段匹配：查找 '{base_field}' + '{field_suffix}'")
        
        # 查找包含基础字段的片段位置
        base_indices = []
        for i, text in enumerate(texts):
            if base_field in text:
                base_indices.append(i)
        
        if not base_indices:
            return None
        
        # 对于每个基础字段位置，查找附近的后缀和数值
        for base_idx in base_indices:
            log_info(f"  找到基础字段 '{base_field}' 在片段 {base_idx+1}: '{texts[base_idx]}'")
            
            # 查找后缀在附近片段中的位置
            for offset in range(-2, 3):  # 前后2个片段范围内查找
                suffix_idx = base_idx + offset
                if 0 <= suffix_idx < len(texts):
                    text = texts[suffix_idx]
                    
                    # 检查是否包含目标后缀
                    if field_suffix:
                        # 对于max/min字段，需要精确匹配后缀
                        if any(pattern in text.lower() for pattern in [field_suffix, f"({field_suffix})", f"（{field_suffix}）"]):
                            log_info(f"  找到后缀 '{field_suffix}' 在片段 {suffix_idx+1}: '{text}'")
                            
                            # 在后缀片段和其后续片段中查找数字（支持负数）
                            for num_offset in range(0, 3):
                                num_idx = suffix_idx + num_offset
                                if 0 <= num_idx < len(texts):
                                    numbers = re.findall(r'(-?\d+\.?\d*)', texts[num_idx])
                                    if numbers:
                                        raw_value = numbers[0]
                                        log_info(f"  跨片段匹配成功：在片段 {num_idx+1} '{texts[num_idx]}' 找到数值: {raw_value}")
                                        return raw_value
                    else:
                        # 对于普通字段，直接在后续片段查找数字（支持负数）
                        numbers = re.findall(r'(-?\d+\.?\d*)', text)
                        if numbers:
                            raw_value = numbers[0]
                            log_info(f"  跨片段匹配成功：在片段 {suffix_idx+1} '{text}' 找到数值: {raw_value}")
                            return raw_value
        
        return None
    
    def _extract_with_patterns(self, texts: List[str], field_name: str) -> Optional[str]:
        """使用基于配置的模式匹配"""
        
        # 基于字段名生成多种匹配模式
        patterns = self._generate_field_patterns(field_name)
        
        # 使用模式匹配全部文本
        full_text = " ".join(texts)
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                log_info(f"  通过模式 '{pattern}' 找到数值: {match.group(1)}")
                return match.group(1)
        
        # 最后的后备方案：查找字段名后紧跟的数字
        return self._fallback_extraction(texts, field_name)
    
    def _fallback_extraction(self, texts: List[str], field_name: str) -> Optional[str]:
        """后备提取方法：智能容错的邻近搜索"""
        
        # 提取字段的关键信息
        base_field = field_name
        field_suffix = ""
        
        # 保留关键的区分信息
        for suffix in [" (max)", " (min)", "（max）", "（min）"]:
            if suffix in field_name:
                field_suffix = suffix.replace(" ", "").replace("（", "").replace("）", "").replace("(", "").replace(")", "")
                break
        
        # 清理基础字段名
        for suffix in [" (rpm)", " (max)", " (min)", "（rpm）", "（max）", "（min）"]:
            base_field = base_field.replace(suffix, "")
        
        log_info(f"  后备方案：查找基础字段='{base_field}', 后缀='{field_suffix}'")
        
        # 策略1：处理中文识别失败（识别为问号的情况）
        chinese_failed_texts = []
        for i, text in enumerate(texts):
            if '?' in text and any(keyword in text.lower() for keyword in ['max', 'min', 'mi', 'rpm']):
                chinese_failed_texts.append((i, text))
                log_info(f"  检测到中文识别失败: 片段{i+1} '{text}'")
        
        if chinese_failed_texts and field_suffix in ["max", "min"]:
            # 基于英文关键字匹配
            for i, text in chinese_failed_texts:
                if field_suffix == "max" and "max" in text.lower():
                    numbers = re.findall(r'(-?\d+\.?\d*)', text)
                    if numbers:
                        log_info(f"  中文识别失败修复：max字段 -> {numbers[0]}")
                        return numbers[0]
                elif field_suffix == "min" and ("min" in text.lower() or "mi" in text.lower()):
                    numbers = re.findall(r'(-?\d+\.?\d*)', text)
                    if numbers:
                        log_info(f"  中文识别失败修复：min字段 -> {numbers[0]}")
                        return numbers[0]
        
        # 对于max/min字段，使用智能匹配策略
        if field_suffix in ["max", "min"]:
            # 策略2：精确匹配
            for i, text in enumerate(texts):
                if base_field in text and field_suffix in text.lower():
                    numbers = re.findall(r'(-?\d+\.?\d*)', text)
                    if numbers:
                        log_info(f"  后备方案：精确匹配 '{text}' 中找到数值: {numbers[0]}")
                        return numbers[0]
            
            # 策略2：模糊匹配（处理OCR识别错误）
            similar_patterns = {
                "max": ["max", "nax", "mux", "mac"],
                "min": ["min", "mix", "nin", "mir", "mic"]
            }
            
            if field_suffix in similar_patterns:
                for i, text in enumerate(texts):
                    if base_field in text:
                        text_lower = text.lower()
                        for pattern in similar_patterns[field_suffix]:
                            if pattern in text_lower:
                                numbers = re.findall(r'(-?\d+\.?\d*)', text)
                                if numbers:
                                    log_info(f"  后备方案：模糊匹配 '{text}' (模式: {pattern}) 中找到数值: {numbers[0]}")
                                    return numbers[0]
            
            # 策略3：位置推断（基于顺序）
            base_texts = [text for text in texts if base_field in text]
            if len(base_texts) >= 2:
                if field_suffix == "max":
                    # 第一个通常是max
                    numbers = re.findall(r'(-?\d+\.?\d*)', base_texts[0])
                    if numbers:
                        log_info(f"  后备方案：位置推断(第1个) '{base_texts[0]}' 作为max: {numbers[0]}")
                        return numbers[0]
                elif field_suffix == "min":
                    # 第二个通常是min
                    numbers = re.findall(r'(-?\d+\.?\d*)', base_texts[1])
                    if numbers:
                        log_info(f"  后备方案：位置推断(第2个) '{base_texts[1]}' 作为min: {numbers[0]}")
                        return numbers[0]
        else:
            # 普通字段的邻近搜索
            for i, text in enumerate(texts):
                if base_field in text:
                    # 在同一个文本中查找数字
                    numbers = re.findall(r'(-?\d+\.?\d*)', text)
                    if numbers:
                        log_info(f"  后备方案：在文本 '{text}' 中找到数值: {numbers[0]}")
                        return numbers[0]
                    
                    # 在后续文本中查找数字
                    for j in range(i + 1, min(i + 3, len(texts))):
                        numbers = re.findall(r'(-?\d+\.?\d*)', texts[j])
                        if numbers:
                            log_info(f"  后备方案：在后续文本 '{texts[j]}' 中找到数值: {numbers[0]}")
                            return numbers[0]
        
        return None
    
    def update_field_mappings(self, mappings: Dict[str, Any]):
        """更新字段映射 - 支持一对多映射
        
        Args:
            mappings: 字段映射，格式如：
                {"字段名": "单个key"} 或 {"字段名": ["key1", "key2"]}
        """
        self.field_mappings = mappings
        print(f"字段映射已更新: {mappings}")
    
    def get_field_mappings(self) -> Dict[str, Any]:
        """获取当前字段映射"""
        return self.field_mappings.copy()
    
    def add_field_mapping(self, field_name: str, mapped_key: str):
        """添加字段映射"""
        self.field_mappings[field_name] = mapped_key
    
    def remove_field_mapping(self, field_name: str):
        """删除字段映射"""
        if field_name in self.field_mappings:
            del self.field_mappings[field_name]
