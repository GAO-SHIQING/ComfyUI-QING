# 🎨QING 节点目录结构

本目录包含所有ComfyUI-QING项目的自定义节点，按功能分类组织：

## 📁 目录结构

### 🤖 **api/** - API集成节点
- `GLM_Language_API.py` - GLM语言模型API调用
- `GLM_Vision_API.py` - GLM视觉模型API调用
- `api_key_server.py` - API密钥管理服务
- `config_server.py` - 配置服务器
- `settings_approach.py` - 设置管理方法

### 🖼️ **image_processing/** - 图像处理节点
- `Custom_load_image.py` - 自定义图像加载
- `Image_cache.py` - 图像缓存管理
- `Image_flipping.py` - 图像翻转旋转
- `Image_mask_converter.py` - 图像遮罩转换
- `Size_scaling.py` - 尺寸缩放处理

### 🎭 **mask_processing/** - 遮罩处理节点
- `Mask_blend.py` - 遮罩混合
- `Mask_expansion.py` - 遮罩扩张
- `Mask_judgment.py` - 遮罩判断
- `Mask_preview.py` - 遮罩预览
- `Mask_Splitter.py` - 遮罩分割

### 🎨 **svg_processing/** - SVG处理节点
- `Image_to_svg.py` - 图像转SVG
- `Svg_to_image.py` - SVG转图像

### 📁 **io_operations/** - 输入输出节点
- `Load_svg.py` - SVG文件加载
- `Svg_saver.py` - SVG文件保存

### 📊 **data_types/** - 数据类型节点
- `Data_preview.py` - 数据预览分析
- `Text_compare.py` - 文本比较
- `Type_conversion.py` - 类型转换

### 🔧 **debug_tools/** - 调试工具节点
- `LetMeSee.py` - 通用数据调试预览

### 🎬 **video_processing/** - 视频处理节点
- `Video_combine.py` - 视频合成处理

## 🔄 自动发现机制

主`__init__.py`文件使用递归搜索自动发现所有子目录中的节点文件，无需手动注册。每个节点文件通过`NODE_CLASS_MAPPINGS`和`NODE_DISPLAY_NAME_MAPPINGS`定义其导出的节点类。

分类目录不需要`__init__.py`文件，保持目录结构简洁干净。

## 📝 添加新节点

要添加新节点：
1. 将节点文件放在合适的分类目录中
2. 确保文件包含`NODE_CLASS_MAPPINGS`和`NODE_DISPLAY_NAME_MAPPINGS`定义
3. 重启ComfyUI即可自动加载新节点

---
*🎨QING项目 - 让ComfyUI更强大、更易用*
