"""
Windows exe优化配置
优化启动速度和资源使用
"""
import os
import sys
import warnings

def optimize_for_exe():
    """在exe环境中应用优化"""
    if getattr(sys, 'frozen', False):
        # 1. 禁用不必要的警告
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*pin_memory.*")
        
        # 2. 优化环境变量
        os.environ['TORCH_DISABLE_PIN_MEMORY_WARNING'] = '1'
        os.environ['OMP_NUM_THREADS'] = '2'  # 限制OpenMP线程数
        os.environ['NUMBA_NUM_THREADS'] = '2'  # 限制Numba线程数
        
        # 3. PyTorch优化
        try:
            import torch
            if not torch.cuda.is_available():
                torch.set_num_threads(2)  # CPU模式限制线程数
                torch.backends.cudnn.enabled = False
                print("✅ PyTorch CPU优化已应用")
        except ImportError:
            pass
            
        # 4. 禁用TensorFlow警告（如果存在）
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        
        # 5. 设置临时目录优化
        temp_dir = os.environ.get('TEMP', 'C:\\temp')
        os.environ['TMPDIR'] = temp_dir
        
        print("✅ exe环境优化设置已应用")
        
        return True
    return False

def get_performance_tips():
    """获取性能优化建议"""
    tips = [
        "1. 首次启动会较慢，后续启动会更快",
        "2. 将exe文件放在SSD上可加快启动速度", 
        "3. 添加杀毒软件白名单以避免实时扫描",
        "4. 确保有足够的临时空间（至少500MB）",
        "5. 模型文件放在exe同目录可提高加载速度"
    ]
    return tips

if __name__ == "__main__":
    if optimize_for_exe():
        print("运行在exe环境中")
        tips = get_performance_tips()
        print("\n性能优化建议:")
        for tip in tips:
            print(f"  {tip}")
    else:
        print("运行在开发环境中")
