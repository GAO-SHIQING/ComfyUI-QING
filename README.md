# 🎨 ComfyUI-QING：解锁ComfyUI媒体处理全场景能力  
[English](#english-intro)  

![ComfyUI-QING Banner](https://picsum.photos/seed/qing/1200/300)  

一款为ComfyUI量身打造的「全能媒体处理扩展」，让图像、SVG、文本、视频的复杂工作流变得简单高效。无论是创意设计、动画制作还是批量处理，都能提供精准工具链支持，释放你的创作潜能。  


## ✨ 核心亮点  
- **SVG全链路解决方案**  
  从本地文件加载到高质量格式转换，一站式搞定SVG素材的全流程管理，完美适配图像生成工作流。  

- **精细化遮罩工程**  
  智能拆分含文字/图形的复杂遮罩，支持多策略缩放（按长边/短边/像素数等），细节无损保留。  

- **文本交互引擎**  
  多组文本对比与条件判断，让工作流根据内容智能分支，轻松实现模板切换、内容审核等场景。  

- **专业级视频合成**  
  覆盖mp4/webm/avi/gif/mkv/flv等格式，内置H.264/H.265/AV1/ProRes等编码器，自定义压缩率与质量参数。  


## 🎯 适用场景  
- **创意设计工作流**：集成SVG素材到图像生成，实现矢量图与像素图的无缝衔接。  
- **精细遮罩处理**：拆分含文字的复杂遮罩，用于图像编辑、区域替换等场景。  
- **智能文本分支**：基于文本匹配结果自动切换工作流（如审核合规内容、选择对应模板）。  
- **视频创作 pipeline**：序列帧合成动画、多格式导出、编码器优化，满足从草稿到发布的全需求。  


## 🛠️ 功能模块详解  
### 1. SVG全流程工具链  

| 节点名称 | 核心功能 |  
|---------|---------|  
| `加载SVG` | 读取本地SVG文件（支持绝对/相对路径），自动校验格式有效性，输出原始SVG内容。 |  
| `加载图像（支持SVG）` | 统一处理PNG/JPG/SVG等格式，同步输出图像、遮罩与元信息，简化多格式素材管理。 |  
| `SVG到图像` | 实现SVG到PNG/JPG的无损转换，支持自定义尺寸、缩放策略（长边/短边/像素数）、插值方法与背景色。 |  


### 2. 遮罩高级处理套件  
| 节点名称 | 核心功能 |  
|---------|---------|  
| `拆分遮罩` | 智能拆分复杂遮罩，保持文字/图形组件完整性，提供自动分组与激进合并模式，轻松拆解多元素遮罩。 |  
| `遮罩缩放` | 支持按宽度/高度/长边/短边/总像素数缩放，搭配nearest/bilinear/lanczos等插值算法，确保缩放后细节清晰。 |  


### 3. 文本与视频处理引擎  
| 节点名称 | 核心功能 |  
|---------|---------|  
| `文本对比` | 支持3组文本对比，可配置大小写敏感模式，输出精准匹配结果，适配条件分支场景（如内容过滤、模板切换）。 |  
| `合成视频` | 序列帧转视频的专业工具，支持：<br>- 格式：mp4/webm/avi/mov/gif/mkv/flv<br>- 编码器：H.264/H.265/AV1/ProRes/VP9等<br>- 自定义压缩率、帧率、质量参数 |  


## 🚀 快速开始  
### 安装步骤  

1. 克隆仓库到ComfyUI的`custom_nodes`目录：  
   ```bash  
   cd ComfyUI/custom_nodes  
   git clone https://github.com/GAOSHI-QING/ComfyUI-QING.git  
   ```  

2. 安装依赖：  
   ```bash  
   cd ComfyUI-QING  
   pip install -r requirements.txt  
   ```  

3. 重启ComfyUI，节点将自动加载，可在「自定义节点」「image」等分类中找到。  


## 📦 依赖说明  
- 图像处理：`numpy`、`opencv-python`、`scipy`、`scikit-image`  
- 格式转换：`Pillow`、`cairosvg`（SVG转图像核心依赖）  
- 张量运算：`torch`（适配ComfyUI核心计算）  


## 🌟 参与共建  
欢迎提交Issues反馈问题，或通过PR贡献新功能！无论是节点优化、格式支持扩展还是文档完善，你的参与都能让这个工具更强大。  

让ComfyUI-QING成为你的媒体处理利器，简化流程，释放创意！ 🚀  


---


<a id="english-intro"></a>
# 🎨 ComfyUI-QING: Unlock Full-Scenario Media Processing Capabilities for ComfyUI  

![ComfyUI-QING Banner](https://picsum.photos/seed/qing/1200/300)  

A powerful all-in-one media processing extension tailored for ComfyUI, simplifying complex workflows involving images, SVG, text, and video. Whether for creative design, animation production, or batch processing, it provides precise toolchain support to unleash your creative potential.  


## ✨ Core Highlights  
- **Full SVG Workflow Solution**  
  Seamless management of SVG materials from local file loading to high-quality format conversion, perfectly integrating with image generation workflows.  

- **Precision Mask Engineering**  
  Intelligently split complex masks containing text/graphics, supporting multi-strategy scaling (by long side/short side/pixel count, etc.) while preserving details.  

- **Text Interaction Engine**  
  Multi-group text comparison and conditional judgment enable workflows to branch intelligently based on content, easily implementing scenarios like template switching and content review.  

- **Professional Video Synthesis**  
  Supports formats including mp4/webm/avi/gif/mkv/flv, with built-in encoders (H.264/H.265/AV1/ProRes, etc.) and customizable compression rates and quality parameters.  


## 🎯 Use Cases  
- **Creative Design Workflows**: Integrate SVG materials into image generation for seamless vector-raster integration.  
- **Fine Mask Processing**: Split complex text-containing masks for image editing and region replacement.  
- **Smart Text Branching**: Automatically switch workflows based on text matching results (e.g., content compliance review, template selection).  
- **Video Creation Pipelines**: Sequence frame animation synthesis, multi-format export, and encoder optimization, covering needs from draft to publication.  


## 🛠️ Feature Modules  
### 1. SVG Full-Process Toolchain  
| Node Name               | Core Function                                                                 |  
|-------------------------|-------------------------------------------------------------------------------|  
| `Load SVG`              | Reads local SVG files (supports absolute/relative paths) and outputs raw SVG content. |  
| `CustomLoadImageWithFormat` | Unified handling of PNG/JPG/SVG formats, outputting images, masks, and metadata. |  
| `SVG To Image`          | Lossless SVG-to-PNG/JPG conversion with customizable size, scaling strategies, and background color. |  


### 2. Advanced Mask Processing Suite  
| Node Name               | Core Function                                                                 |  
|-------------------------|-------------------------------------------------------------------------------|  
| `MaskSplitterPro`       | Intelligently splits complex masks, preserving text/graphic integrity with auto-grouping and aggressive merging modes. |  
| `MaskScale`             | Scales masks by width/height/longest side/shortest side/total pixels, with interpolation algorithms (nearest/bilinear/lanczos) for clear details. |  


### 3. Text & Video Processing Engine  
| Node Name               | Core Function                                                                 |  
|-------------------------|-------------------------------------------------------------------------------|  
| `TextCompare`           | Supports 3 groups of text comparison with case sensitivity configuration, outputting precise matching results for conditional branching. |  
| `SyntheticVideo`        | Professional sequence frame to video tool supporting formats (mp4/webm/avi/gif/mkv/flv) and encoders (H.264/H.265/AV1/ProRes/VP9, etc.), with customizable compression, frame rate, and quality. |  


## 🚀 Quick Start  
### Installation Steps  
1. Clone the repository to ComfyUI's `custom_nodes` directory:  
   ```bash  
   cd ComfyUI/custom_nodes  
   git clone https://github.com/GAOSHI-QING/ComfyUI-QING.git  
   ```  

2. Install dependencies:  
   ```bash  
   cd ComfyUI-QING  
   pip install -r requirements.txt  
   ```  

3. Restart ComfyUI. Nodes will load automatically, found under "Custom Nodes" or "Image" categories.  


## 📦 Dependencies  
- Image Processing: `numpy`, `opencv-python`, `scipy`, `scikit-image`  
- Format Conversion: `Pillow`, `cairosvg` (core for SVG-to-image conversion)  
- Tensor Operations: `torch` (compatible with ComfyUI's core computing)  


## 🌟 Contribute  
Welcome to submit Issues for feedback or PRs to contribute new features! Whether node optimization, format support expansion, or documentation improvement, your participation makes this tool more powerful.  

Let ComfyUI-QING be your media processing tool, simplifying workflows and unlocking creativity! 🚀
