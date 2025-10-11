# 🎨QING 节点目录结构

本目录包含ComfyUI-QING项目的所有自定义节点，采用**功能分类目录结构**，通过自动发现机制统一管理。

## 📁 目录结构

```
nodes/
├── api/              # API调用节点
├── image/            # 图像处理节点
├── mask/             # 遮罩处理节点
├── svg/              # SVG处理节点
├── video/            # 视频处理节点
├── data/             # 数据处理节点
└── utils/            # 工具类节点
```

## 📁 节点文件列表

### 🤖 **API集成节点** (`api/`)
- `API_DeepSeek_Language.py` - DeepSeek语言模型API
- `API_Doubao_Vision.py` - 豆包视觉模型API  
- `API_Gemini_Vision.py` - Gemini视觉模型API
- `API_Gemini_Edit.py` - Gemini图像编辑模型API
- `API_GLM_Language.py` - GLM语言模型API
- `API_GLM_Vision.py` - GLM视觉模型API
- `API_Kimi_Language.py` - Kimi语言模型API
- `API_Kimi_Vision.py` - Kimi视觉模型API
- `API_Qwen_Language.py` - Qwen语言模型API
- `API_Qwen_Vision.py` - Qwen视觉模型API
- `base_api_framework.py` - API框架基础类
- `config/` - 配置文件目录
  - `config_server.py` - 配置服务器
- `utils/` - 工具模块
  - `settings_approach.py` - 设置管理方法

### 📊 **数据处理节点** (`data/`)
- **`Data_converter.py`** - 数据类型转换工具集
  - `IntToString` - 整数到字符串转换
  - `StringToInt` - 字符串到整数转换  
  - `StringToBool` - 字符串到布尔转换
  - `BoolToInt` - 布尔到整数转换
  - `IntToBool` - 整数到布尔转换
  - `BoolInvert` - 布尔值反转

- **`Data_tools.py`** - 数据分析工具集
  - `ImageDataAnalyzer` - 图像数据分析器（维度、统计、内存占用）
  - `MaskDataAnalyzer` - 遮罩数据分析器（覆盖率、形状分析）
  - `TextCompare` - 文本比较工具（支持大小写敏感）

### 🔧 **调试工具节点** (`utils/`)
- **`Debug_tools.py`** - 调试预览工具集
  - `LetMeSee` - 我想看看（详细数据分析 + 系统资源监控）
  - `ShowMePure` - 让我看看（纯净内容显示，无额外信息）

### 🖼️ **图像处理节点** (`image/`)
- **`Image_cache.py`** - 图像缓存管理器
  - `ImageCache` - 支持99张图像缓存，自动保存清理

- **`Image_loader.py`** - 图像加载器
  - `CustomLoadImageWithFormat` - 多格式图像加载（支持SVG）

- **`Image_mask_converter.py`** - 图像遮罩转换器
  - `ImageMaskConverter` - 图像与遮罩相互转换

- **`Image_to_svg.py`** - 图像转SVG工具
  - 位图图像转换为矢量SVG格式

- **`Image_transform.py`** - 图像变换工具集
  - `ImageRotation` - 图像旋转
  - `ImageFlipping` - 图像翻转
  - `ImageScaling` - 图像缩放
  - `MaskScale` - 遮罩缩放

### 🎭 **遮罩处理节点** (`mask/`)
- **`Mask_blend.py`** - 遮罩混合工具
- **`Mask_expansion.py`** - 遮罩扩张工具  
- **`Mask_fill.py`** - 遮罩填充工具
  - `MaskFill` - 填充遮罩孔洞，支持反转填充，输出遮罩尺寸信息
- **`Mask_judgment.py`** - 遮罩判断工具
- **`Mask_preview.py`** - 遮罩预览工具
- **`Mask_Splitter.py`** - 遮罩分割工具

### 🎨 **SVG处理节点** (`svg/`)
- **`SVG_io.py`** - SVG输入输出工具
- **`Svg_to_image.py`** - SVG转图像工具

### 🎬 **视频处理节点** (`video/`)
- **`Video_processor.py`** - 视频处理工具

### ⚙️ **配置管理节点** (`utils/`)
- **`Config_manager.py`** - 配置文件管理工具集
  - `ConfigExport` - 配置文件丨导出
    - 导出节点信息（含GitHub地址）
    - 导出完整Python环境依赖
    - 导出前端设置、工作流
    - 支持自定义路径，智能过滤备份文件
  - `ConfigImport` - 配置文件丨导入  
    - 支持ZIP压缩包或文件夹导入
    - 三种导入模式：覆盖/跳过/自动重命名
    - 自动备份到output目录
    - ZIP完整性检测

## 🚀 节点特色功能

### 🔍 **右键快速调试**
- 任意节点右键 → **🔍 添加：我想看看** → 详细数据分析
- 任意节点右键 → **👀 添加：让我看看** → 纯净内容显示
- 自动连接当前节点输出，支持任意数据类型透传

### 📡 **多平台API支持**
支持主流AI模型平台：
- **OpenAI系列**：GPT-4、GPT-3.5等
- **国产模型**：GLM、Qwen、Kimi、DeepSeek、豆包
- **统一接口**：一套代码适配多个平台
- **智能重试**：网络异常自动重试

### 🖼️ **图像处理增强**
- **多格式支持**：PNG、JPG、SVG、GIF、WebP等
- **缓存机制**：智能图像缓存，提升处理效率  
- **变换工具**：旋转、翻转、缩放一应俱全
- **遮罩高级操作**：混合、扩张、填充、分割、判断
  - 遮罩填充：智能填充孔洞，支持反转和尺寸输出

### 📊 **数据分析助手**
- **类型转换**：各种基础类型互转
- **数据分析**：图像、遮罩的深度分析
- **文本比较**：支持批量文本对比
- **透传输出**：分析的同时保持数据完整传递

### ⚙️ **配置管理增强**
- **一键备份**：导出完整ComfyUI配置和环境
- **智能导入**：支持ZIP和文件夹，三种导入策略
- **环境追踪**：记录所有节点GitHub地址和版本
- **安全可靠**：自动备份、完整性检测、智能过滤

## 🔄 自动发现机制

项目采用智能节点发现系统：

1. **无需手动注册**：主`__init__.py`自动递归搜索所有`.py`文件
2. **标准化接口**：每个节点文件定义`NODE_CLASS_MAPPINGS`和`NODE_DISPLAY_NAME_MAPPINGS`
3. **热重载支持**：重启ComfyUI即可加载新增节点
4. **错误容错**：单个节点出错不影响其他节点加载

## 📝 添加新节点

### 快速开始
1. **选择目录**：根据节点功能选择合适的子目录（`api/`, `image/`, `mask/`, `svg/`, `video/`, `data/`, `utils/`）
2. **创建节点文件**：在选定的子目录下创建`.py`文件
3. **定义节点类**：实现ComfyUI标准节点接口
4. **注册节点**：添加`NODE_CLASS_MAPPINGS`和`NODE_DISPLAY_NAME_MAPPINGS`
5. **重启加载**：重启ComfyUI，自动发现机制会递归扫描所有子目录并加载新节点

### 目录选择指南
- **`api/`** - AI模型API调用节点
- **`image/`** - 图像加载、转换、变换等处理节点
- **`mask/`** - 遮罩相关的所有操作节点
- **`svg/`** - SVG格式的输入输出和转换节点
- **`video/`** - 视频合成和处理节点
- **`data/`** - 数据类型转换和数据分析节点
- **`utils/`** - 调试工具和配置管理等通用节点


## 📋 项目统计

- **📁 功能目录**：7个分类子目录
- **🎯 节点文件**：25+个节点文件
- **🔧 功能节点**：37个独立节点类
- **🤖 API节点**：10个（支持9大AI平台）
- **🌍 多语言**：支持中英文界面
- **🚀 活跃开发**：持续更新维护
- **⚙️ 最新版本**：v1.2.0
  - 目录结构优化：功能分类组织
  - JavaScript模块化重构
  - API模块增强：Gemini编辑模型支持

---

*🎨QING项目 - 让ComfyUI更强大、更智能、更易用！*