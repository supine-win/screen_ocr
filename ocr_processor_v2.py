#!/usr/bin/env python3
"""
优化的OCR处理器 v2
集成缓存、性能监控、错误处理等优化功能
"""

import cv2
import numpy as np
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path

from logger_config import get_logger
from performance_monitor import performance_monitor
from cache_manager import OCRCache
from error_handler import ErrorHandler, ErrorType, CircuitBreaker
from model_path_manager import ModelPathManager
from config_validator import ConfigValidator

logger = get_logger(__name__)

class OCRProcessorV2:
    """优化的OCR处理器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化OCR处理器"""
        # 验证并加载配置
        if config is None:
            config = ConfigValidator.load_and_validate()
        self.config = config
        
        # 初始化组件
        self.cache = OCRCache(ttl=config.get('performance', {}).get('cache_ttl', 300))
        self.error_handler = ErrorHandler()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # OCR引擎配置
        self.ocr_engine = config.get('ocr', {}).get('engine', 'auto')
        self.field_mappings = config.get('ocr', {}).get('field_mappings', {})
        
        # 设置模型路径环境
        ModelPathManager.setup_easyocr_environment()
        
        # 初始化OCR引擎
        self.easyocr_reader = None
        self.paddleocr_engine = None
        self._initialize_ocr_engines()
        
        # 性能设置
        self.max_image_size = config.get('performance', {}).get('max_image_size', 1920)
        self.ocr_timeout = config.get('performance', {}).get('ocr_timeout', 30)
        self.enable_cache = config.get('performance', {}).get('enable_cache', True)
        
        logger.info(f"OCRProcessorV2 initialized with engine: {self.ocr_engine}")
    
    def _initialize_ocr_engines(self):
        """初始化OCR引擎"""
        # 优先尝试EasyOCR
        if self.ocr_engine in ['easyocr', 'auto']:
            try:
                import easyocr
                
                # 获取模型路径
                model_path = ModelPathManager.get_easyocr_model_path()
                if model_path:
                    logger.info(f"Using EasyOCR model path: {model_path}")
                    
                    # 尝试指定模型目录（如果支持）
                    try:
                        self.easyocr_reader = easyocr.Reader(
                            ['ch_sim', 'en'],
                            gpu=False,
                            verbose=True,  # 临时启用详细日志帮助调试
                            model_storage_directory=str(Path(model_path).parent)
                        )
                    except:
                        # 回退到默认初始化
                        logger.warning("Failed to use custom model path, using default")
                        self.easyocr_reader = easyocr.Reader(
                            ['ch_sim', 'en'],
                            gpu=False,
                            verbose=True
                        )
                else:
                    logger.warning("No EasyOCR model path found, trying default initialization")
                    self.easyocr_reader = easyocr.Reader(
                        ['ch_sim', 'en'],
                        gpu=False,
                        verbose=True
                    )
                
                logger.info("EasyOCR engine initialized successfully")
                if self.ocr_engine == 'auto':
                    self.ocr_engine = 'easyocr'
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                if self.ocr_engine == 'easyocr':
                    raise
        
        # 备选PaddleOCR
        if self.ocr_engine in ['paddleocr', 'auto'] and not self.easyocr_reader:
            try:
                from paddleocr import PaddleOCR
                self.paddleocr_engine = PaddleOCR(
                    use_angle_cls=False,
                    lang='ch',
                    show_log=False
                )
                logger.info("PaddleOCR engine initialized successfully")
                if self.ocr_engine == 'auto':
                    self.ocr_engine = 'paddleocr'
            except Exception as e:
                logger.warning(f"Failed to initialize PaddleOCR: {e}")
                if self.ocr_engine == 'paddleocr':
                    raise
        
        if not self.easyocr_reader and not self.paddleocr_engine:
            raise RuntimeError("No OCR engine available")
    
    @performance_timer
    @monitor_memory(threshold_mb=100)
    def process_image(self, image: np.ndarray, region: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理图像并提取字段值
        
        Args:
            image: 输入图像
            region: 可选的区域信息
            
        Returns:
            提取的字段值和元信息
        """
        start_time = time.time()
        
        try:
            # 生成图像哈希用于缓存
            image_hash = self._compute_image_hash(image)
            
            # 检查缓存
            if self.enable_cache:
                cached_result = self.cache.get_ocr_result(image_hash, region)
                if cached_result:
                    logger.info("OCR result retrieved from cache")
                    performance_monitor.record_success()
                    return cached_result
            
            # 预处理图像
            processed_image = self._preprocess_image(image)
            
            # 使用熔断器保护的OCR识别
            ocr_result = self.circuit_breaker.call(
                self._perform_ocr,
                processed_image
            )
            
            # 提取字段值
            extracted_values = self._extract_fields(ocr_result)
            
            # 构建完整结果
            result = {
                'success': True,
                'fields': extracted_values,
                'raw_text': ocr_result.get('texts', []),
                'confidence': ocr_result.get('confidence', 0),
                'engine': self.ocr_engine,
                'processing_time': time.time() - start_time,
                'image_size': image.shape[:2],
                'cached': False
            }
            
            # 缓存结果
            if self.enable_cache and extracted_values:
                self.cache.set_ocr_result(image_hash, result, region)
            
            # 记录性能指标
            performance_monitor.record_ocr_time(time.time() - start_time)
            performance_monitor.record_success()
            
            return result
            
        except Exception as e:
            # 记录错误
            self.error_handler.log_error(ErrorType.OCR_FAILURE, e, {
                'image_shape': image.shape,
                'region': region
            })
            
            performance_monitor.record_failure()
            
            return {
                'success': False,
                'error': str(e),
                'fields': {},
                'engine': self.ocr_engine,
                'processing_time': time.time() - start_time
            }
    
    def _compute_image_hash(self, image: np.ndarray) -> str:
        """计算图像哈希值"""
        # 降采样以加快哈希计算
        small = cv2.resize(image, (64, 64))
        return hashlib.md5(small.tobytes()).hexdigest()
    
    @retry_on_error(max_attempts=2, delay=0.5)
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """预处理图像"""
        height, width = image.shape[:2]
        
        # 智能缩放
        if max(height, width) > self.max_image_size:
            scale = self.max_image_size / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.debug(f"Image resized from {(width, height)} to {(new_width, new_height)}")
        
        # 图像增强
        if len(image.shape) == 3:
            # 转换到LAB色彩空间进行增强
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # CLAHE增强
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # 合并回RGB
            enhanced = cv2.merge([l, a, b])
            image = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            # 降噪
            image = cv2.bilateralFilter(image, 5, 75, 75)
        
        return image
    
    def _perform_ocr(self, image: np.ndarray) -> Dict[str, Any]:
        """执行OCR识别"""
        future = self.executor.submit(self._ocr_worker, image)
        
        try:
            result = future.result(timeout=self.ocr_timeout)
            return result
        except TimeoutError:
            logger.error(f"OCR timeout after {self.ocr_timeout} seconds")
            future.cancel()
            raise TimeoutError(f"OCR processing exceeded {self.ocr_timeout} seconds")
    
    def _ocr_worker(self, image: np.ndarray) -> Dict[str, Any]:
        """OCR工作线程"""
        texts = []
        confidences = []
        
        if self.easyocr_reader:
            # 使用EasyOCR
            try:
                results = self.easyocr_reader.readtext(image, detail=1)
                for _, text, confidence in results:
                    texts.append(text)
                    confidences.append(confidence)
                
                logger.debug(f"EasyOCR detected {len(texts)} text regions")
                
            except Exception as e:
                logger.error(f"EasyOCR failed: {e}")
                if not self.paddleocr_engine:
                    raise
        
        elif self.paddleocr_engine:
            # 使用PaddleOCR
            try:
                result = self.paddleocr_engine.ocr(image)
                if result and result[0]:
                    for line in result[0]:
                        if line and len(line) >= 2:
                            if isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                                texts.append(line[1][0])
                                confidences.append(line[1][1])
                
                logger.debug(f"PaddleOCR detected {len(texts)} text regions")
                
            except Exception as e:
                logger.error(f"PaddleOCR failed: {e}")
                raise
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'texts': texts,
            'confidences': confidences,
            'confidence': avg_confidence
        }
    
    def _extract_fields(self, ocr_result: Dict[str, Any]) -> Dict[str, str]:
        """提取字段值"""
        texts = ocr_result.get('texts', [])
        extracted = {}
        
        for field_name, mapped_key in self.field_mappings.items():
            value = self._find_field_value(texts, field_name)
            if value:
                extracted[mapped_key] = value
                logger.debug(f"Extracted {mapped_key}: {value}")
        
        return extracted
    
    def _find_field_value(self, texts: List[str], field_name: str) -> Optional[str]:
        """查找字段值"""
        import re
        
        # 清理字段名
        clean_name = field_name.replace(" (rpm)", "").replace(" (max)", "").replace(" (min)", "").strip()
        
        # 在文本中查找
        for i, text in enumerate(texts):
            if clean_name in text:
                # 查找后续的数值
                for j in range(i, min(i + 3, len(texts))):
                    numbers = re.findall(r'\d+\.?\d*', texts[j])
                    if numbers:
                        return numbers[0]
        
        return None
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self.config = config
        self.field_mappings = config.get('ocr', {}).get('field_mappings', {})
        self.max_image_size = config.get('performance', {}).get('max_image_size', 1920)
        self.ocr_timeout = config.get('performance', {}).get('ocr_timeout', 30)
        self.enable_cache = config.get('performance', {}).get('enable_cache', True)
        
        # 更新缓存TTL
        cache_ttl = config.get('performance', {}).get('cache_ttl', 300)
        self.cache.cache_manager.ttl = cache_ttl
        
        logger.info("OCR processor configuration updated")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        return {
            'engine': self.ocr_engine,
            'cache': self.cache.get_statistics(),
            'errors': self.error_handler.get_error_statistics(),
            'circuit_breaker': {
                'state': self.circuit_breaker.state,
                'failure_count': self.circuit_breaker.failure_count
            },
            'field_mappings': self.field_mappings
        }
    
    def cleanup(self):
        """清理资源"""
        self.executor.shutdown(wait=True)
        self.cache.clear()
        logger.info("OCR processor resources cleaned up")
