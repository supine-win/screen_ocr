#!/usr/bin/env python3
"""
模拟打包环境测试EasyOCR修复
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from model_path_manager import ModelPathManager

def create_mock_packaged_env():
    """创建模拟的打包环境"""
    # 创建临时目录模拟MEIPASS
    temp_dir = tempfile.mkdtemp(prefix="test_meipass_")
    models_dir = Path(temp_dir) / "easyocr_models"
    models_dir.mkdir(exist_ok=True)
    
    # 检查是否有现有的模型文件可以复制
    existing_models = Path.home() / ".EasyOCR" / "model"
    if existing_models.exists():
        # 复制现有模型文件到测试目录
        for model_file in existing_models.glob("*.pth"):
            if "craft" in model_file.name or "sim" in model_file.name:
                shutil.copy2(model_file, models_dir / model_file.name)
                print(f"复制模型文件: {model_file.name}")
    else:
        # 创建空的模型文件作为占位符
        (models_dir / "craft_mlt_25k.pth").write_bytes(b"fake_model_data_detection")
        (models_dir / "zh_sim_g2.pth").write_bytes(b"fake_model_data_recognition")
        print("创建了模拟模型文件")
    
    return temp_dir

def test_packaged_environment():
    """测试打包环境"""
    print("=" * 60)
    print("测试模拟打包环境")
    print("=" * 60)
    
    # 创建模拟环境
    mock_meipass = create_mock_packaged_env()
    
    try:
        # 模拟打包环境
        original_frozen = getattr(sys, 'frozen', False)
        original_meipass = getattr(sys, '_MEIPASS', None)
        
        sys.frozen = True
        sys._MEIPASS = mock_meipass
        
        print(f"模拟MEIPASS: {mock_meipass}")
        
        # 测试模型路径获取
        model_path = ModelPathManager.get_easyocr_model_path()
        print(f"获取到的模型路径: {model_path}")
        
        if model_path:
            model_dir = Path(model_path)
            models = list(model_dir.glob("*.pth"))
            print(f"找到模型文件: {len(models)}")
            for model in models:
                size_kb = model.stat().st_size / 1024
                print(f"  - {model.name}: {size_kb:.1f} KB")
        
        # 测试环境设置
        print("\n环境变量设置:")
        success = ModelPathManager.setup_easyocr_environment()
        print(f"环境设置成功: {success}")
        
        # 测试模型结构设置
        print("\n模型结构设置:")
        structure_success = ModelPathManager.setup_easyocr_model_structure()
        print(f"模型结构设置成功: {structure_success}")
        
        if structure_success:
            # 检查创建的目录结构
            easyocr_home = Path(mock_meipass) / ".EasyOCR"
            easyocr_models = easyocr_home / "model"
            if easyocr_models.exists():
                created_models = list(easyocr_models.glob("*.pth"))
                print(f"在.EasyOCR/model中创建了 {len(created_models)} 个模型文件")
        
        # 测试初始化参数
        print("\n初始化参数:")
        params = ModelPathManager.get_easyocr_reader_params()
        print(f"EasyOCR参数: {params}")
        
        # 显示关键环境变量
        print("\n关键环境变量:")
        env_vars = ['EASYOCR_MODULE_PATH', 'EASYOCR_MODEL_PATH', 'TORCH_HOME', 'USERPROFILE', 'HOME']
        for var in env_vars:
            value = os.environ.get(var, 'Not set')
            print(f"  {var}: {value}")
        
        return model_path is not None and success
        
    finally:
        # 恢复原始状态
        sys.frozen = original_frozen
        if original_meipass:
            sys._MEIPASS = original_meipass
        elif hasattr(sys, '_MEIPASS'):
            delattr(sys, '_MEIPASS')
        
        # 清理临时目录
        try:
            shutil.rmtree(mock_meipass)
            print(f"\n清理临时目录: {mock_meipass}")
        except:
            pass

def main():
    """主测试函数"""
    print("EasyOCR打包环境模拟测试")
    print("=" * 60)
    
    # 测试打包环境
    packaged_success = test_packaged_environment()
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"打包环境模拟: {'✅' if packaged_success else '❌'}")
    
    if packaged_success:
        print("🎉 打包环境测试通过！修复应该在实际打包后生效。")
    else:
        print("⚠️  打包环境测试失败，需要进一步调试。")
    
    print("\n重要提示:")
    print("- 这是模拟测试，实际效果需要在真正的打包应用中验证")
    print("- 请重新打包应用并测试是否还会从网络下载模型")

if __name__ == "__main__":
    main()
