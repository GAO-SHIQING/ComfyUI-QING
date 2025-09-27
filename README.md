# 🎨 ComfyUI-QING：解锁ComfyUI媒体处理全场景能力  
[English](#english-intro) | [节点文档](#nodes-documentation) | [最新更新](#latest-updates)

![ComfyUI-QING Banner](https://picsum.photos/seed/qing/1200/300)  

一款为ComfyUI量身打造的「全能媒体处理扩展」，集成30个专业节点，让图像、SVG、文本、视频、AI对话、视觉理解的复杂工作流变得简单高效。无论是创意设计、动画制作、AI内容生成、图像分析还是批量处理，都能提供精准工具链支持，释放你的创作潜能。

## 🆕 最新更新 <a id="latest-updates"></a>

### 🔧 项目架构优化 (2025年9月)
- **节点目录重构**: 将`nodes`目录下的节点文件按功能分类到子目录中，结构更加清晰直观
  - 📁 `api/` - API相关节点和服务
  - 📁 `image_processing/` - 图像处理节点
  - 📁 `mask_processing/` - 遮罩处理节点
  - 📁 `svg_processing/` - SVG处理节点
  - 📁 `data_types/` - 数据类型转换节点
  - 📁 `video_processing/` - 视频处理节点
  - 📁 `io_nodes/` - 输入输出节点

### ⚙️ API密钥管理系统升级
- **实时双向同步**: ComfyUI设置界面与本地配置文件实时同步
- **多平台支持**: 智谱GLM、月之暗面、火山引擎、阿里云百炼、硅基流动、腾讯云六大平台
- **智能优先级**: 设置界面 → 环境变量 → 本地文件的多层级管理
- **离线友好**: 本地存储支持，无需重复配置

### 🌐 国际化支持
- **多语言设置**: 支持中文和英文的设置界面
- **节点分类翻译**: 所有节点分类支持多语言显示
- **设置项翻译**: API密钥设置支持多语言提示和说明



## ✨ 核心亮点  
- **🎨QING智能设置系统**  
  全新的实时双向同步设置管理，支持智谱GLM、月之暗面、火山引擎、阿里云百炼、硅基流动、腾讯云六大平台API密钥配置，在ComfyUI设置界面与本地配置文件之间自动同步，支持多语言界面，智能频率调节，一键配置所有AI模型节点。

- **SVG全链路解决方案**  
  从本地文件加载到高质量格式转换，一站式搞定SVG素材的全流程管理，完美适配图像生成工作流。  

- **精细化遮罩工程**  
  智能拆分、缩放、混合、扩张含文字/图形的复杂遮罩，支持多策略处理，细节无损保留。  

- **图像遮罩双向转换**  
  独立的双向转换系统，实现图像通道提取和遮罩灰度可视化，每个输入对应特定输出。  

- **文本交互引擎**  
  多组文本对比与条件判断，让工作流根据内容智能分支，轻松实现模板切换、内容审核等场景。  

- **专业级视频合成**  
  覆盖mp4/webm/avi/gif/mkv/flv等格式，内置H.264/H.265/AV1/ProRes等编码器，自定义压缩率与质量参数。

- **智能AI对话引擎**  
  支持16个GLM语言模型，包括最新GLM-4.5系列，提供多轮对话记忆、参数精细控制和完整错误处理机制。

- **强大视觉理解能力**  
  集成GLM-4V视觉模型，支持图像分析、描述生成、视觉问答，实现图像+文本多模态智能交互。  


## 🎯 适用场景  
- **创意设计工作流**：集成SVG素材到图像生成，实现矢量图与像素图的无缝衔接。  
- **精细遮罩处理**：拆分、混合、扩张含文字的复杂遮罩，用于图像编辑、区域替换等场景。  
- **图像通道操作**：提取特定颜色通道制作遮罩，或将遮罩转换为可视化图像。  
- **智能文本分支**：基于文本匹配结果自动切换工作流（如审核合规内容、选择对应模板）。  
- **视频创作 pipeline**：序列帧合成动画、多格式导出、编码器优化，满足从草稿到发布的全需求。
- **AI内容生成工作流**：智谱GLM模型驱动的文本生成，支持多轮对话、长文档分析和创意写作。
- **智能图像理解分析**：GLM-4V视觉模型驱动的图像分析，支持图像描述、视觉问答和内容识别。  


## 📊 节点总览  
ComfyUI-QING 提供 **32个专业节点**，覆盖11大功能领域：

| 分类 | 节点数量 | 主要功能 |
|------|----------|----------|
| 🎨 **SVG处理** | 5个 | 加载、转换、保存、格式互转 |
| 🎭 **遮罩工程** | 7个 | 拆分、缩放、混合、扩张、判断、转换、预览 |
| 📝 **文本处理** | 1个 | 多组对比、条件分支 |
| 🤖 **API调用** | 4个 | GLM语言/视觉模型、DeepSeek语言模型、Kimi语言模型、多轮对话、智能生成 |
| 🔄 **数据类型转换** | 6个 | 整数、字符串、布尔值互转、反转 |
| 🔄 **图像变换** | 3个 | 旋转、翻转、缩放、多种插值算法 |
| 🎬 **视频合成** | 1个 | 序列帧转视频、多格式支持 |
| 📦 **缓存管理** | 1个 | 智能图像缓存、预览、自动保存 |
| 📊 **数据分析** | 2个 | 图像数据分析、遮罩数据分析 |
| 🔧 **调试工具** | 2个 | 数据查看器、系统监控、纯净内容显示 |

---

<a id="nodes-documentation"></a>
## 🛠️ 节点详细文档  

### 1. SVG全流程工具链 (5个节点)

| 节点名称 | 功能描述 | 主要特性 |
|---------|----------|----------|
| **加载SVG文件** | 读取本地SVG文件内容 | • 支持绝对/相对路径<br>• 自动格式校验<br>• 输出原始SVG内容 |
| **加载图像(支持SVG)** | 统一加载多种图像格式 | • 支持PNG/JPG/SVG格式<br>• 同步输出图像、遮罩、元信息<br>• 简化多格式素材管理 |
| **SVG转图像** | SVG到栅格图像的高质量转换 | • 无损转换到PNG/JPG<br>• 自定义尺寸和缩放策略<br>• 可配置背景色和插值方法 |
| **图像转SVG** | 将栅格图像转换为矢量SVG | • 多种转换模式(边缘检测/颜色量化/剪影)<br>• 预设模式(简单/详细/艺术)<br>• 智能参数优化 |
| **保存SVG** | 保存SVG内容到文件系统 | • 自定义保存目录和覆盖策略<br>• 自动生成预览图<br>• 适配ComfyUI输出目录结构 |

### 2. 遮罩高级处理套件 (7个节点)

| 节点名称 | 功能描述 | 主要特性 |
|---------|----------|----------|
| **遮罩拆分** | 智能拆分复杂多元素遮罩 | • 保持文字/图形完整性<br>• 自动分组和激进合并模式<br>• 小区域处理和结构保护 |
| **遮罩缩放** | 多策略遮罩尺寸调整 | • 按宽度/高度/长边/短边/像素数缩放<br>• 多种插值算法(nearest/bilinear/lanczos)<br>• 保持细节清晰度 |
| **遮罩混合** | 多遮罩高级混合处理 | • 8种混合模式(相加/相减/交集/异或等)<br>• 边缘效果(羽化/渐变/描边)<br>• 专家模式和阈值控制 |
| **遮罩扩张** | 方向性遮罩区域扩展 | • 支持四方向独立控制<br>• 可配置扩张距离和羽化<br>• 保持边缘平滑过渡 |
| **遮罩判断** | 遮罩有效性检测分析 | • 检测遮罩是否有效<br>• 输出比例和统计信息<br>• 提供布尔和数值结果 |
| **图像遮罩转换** | 图像与遮罩的双向转换 | • 独立转换：image1→mask1, mask1→image1<br>• 图像提取指定通道到遮罩<br>• 遮罩转换为灰度图像 |
| **图像遮罩预览** | 高级图像和遮罩混合预览 | • 实时预览混合效果<br>• 9种遮罩颜色选择(黑白赤橙黄绿青蓝紫)<br>• 透明度调节(0-100)，支持单输入模式 |

### 3. 文本处理引擎 (1个节点)

| 节点名称 | 功能描述 | 主要特性 |
|---------|----------|----------|
| **文本对比** | 多组文本比较和条件判断 | • 支持3组独立文本对比<br>• 可配置大小写敏感性<br>• 输出布尔结果用于条件分支 |

### 4. API调用 (4个节点)

| 节点名称 | 功能描述 | 主要特性 |
|---------|----------|----------|
| **GLM_语言丨API** | 智谱GLM语言模型API调用和文本生成 | • 支持16个GLM语言模型（GLM-4.5/4/3系列）<br>• 智能多轮对话记忆（最多18轮）<br>• 精细参数控制（温度、top_p、max_tokens）<br>• 完整错误处理和智能分类<br>• 实时token统计和对话信息<br>• 基于官方zai-sdk，完全兼容 |
| **GLM_视觉丨API** | 智谱GLM视觉模型API调用和图像理解 | • 支持5个GLM视觉模型（GLM-4.5V/4.1V/4V系列）<br>• 智能参数适配，自动解决1210兼容性问题<br>• 图像+文本多模态输入<br>• 智能图像分析和描述生成<br>• 三种图像质量模式（auto/low/high）<br>• 多轮视觉对话记忆<br>• 多层参数尝试机制，确保所有模型可用 |
| **DeepSeek_语言丨API** | DeepSeek语言模型API调用和推理生成 | • 支持3个DeepSeek模型（V3.1/R1/V3系列）<br>• 多平台支持（火山引擎/阿里云百炼/硅基流动/腾讯云）<br>• 智能多轮对话记忆（最多25轮）<br>• 精细参数控制（温度、top_p、max_tokens）<br>• 完整错误处理和重试机制<br>• 详细token统计信息（输入/输出/总计/限制）<br>• 基于OpenAI兼容API，稳定可靠 |
| **Kimi_语言丨API** | Kimi语言模型API调用和智能对话 | • 支持3个Kimi模型（kimi-k2-0905/0711/turbo系列）<br>• 多平台支持（月之暗面/火山引擎/阿里云百炼/硅基流动）<br>• 超长上下文能力（200万字）和联网搜索特性<br>• 优化参数配置：max_tokens 4096，history 25轮<br>• 创造性参数调优：temperature 0.8，top_p 0.95<br>• 详细token统计信息（输入/输出/总计/限制）<br>• 特别适合长文档分析、复杂推理和深度对话 |

### 5. 数据类型转换工具 (6个节点)

| 节点名称 | 功能描述 | 主要特性 |
|---------|----------|----------|
| **整数到字符串** | 将整数转换为字符串格式 | • 支持全范围整数转换<br>• 异常处理机制<br>• 简单高效的类型转换 |
| **字符串到整数** | 将字符串转换为整数 | • 自动处理空格和格式<br>• 支持标准数学四舍五入(0.5进位)<br>• 转换失败时返回默认值0 |
| **字符串到布尔** | 将字符串转换为布尔值 | • 智能识别多种真假值格式<br>• 支持"true/false"、"1/0"、"yes/no"等<br>• 数字字符串按非零判断 |
| **布尔到整数** | 将布尔值转换为整数 | • True转换为1，False转换为0<br>• 标准布尔逻辑转换<br>• 可用于条件计算 |
| **整数到布尔** | 将整数转换为布尔值 | • 0转换为False，非0转换为True<br>• 标准C风格布尔转换<br>• 支持条件分支逻辑 |
| **布尔反转** | 将布尔值进行逻辑反转 | • True反转为False，False反转为True<br>• 简单的逻辑非操作<br>• 用于条件逻辑反转 |

### 6. 图像变换工具 (3个节点)

| 节点名称 | 功能描述 | 主要特性 |
|---------|----------|----------|
| **图像缩放** | 高级图像和遮罩缩放处理 | • 4种缩放模式(保持比例/拉伸/裁剪/填充)<br>• 6种插值算法(lanczos/bicubic/bilinear等)<br>• 7种缩放定义(最长边/最短边/宽度/高度/百分比/总像素)<br>• 智能倍数约束(就近舍入减少黑边)<br>• 无上限数值支持(适用高分辨率)<br>• **同时输出缩放后的图像和遮罩** |
| **图像旋转** | 对图像进行精确旋转操作 | • 支持正向/反向旋转模式<br>• 0-360度自由角度控制<br>• 6种插值算法(lanczos/bicubic/hamming等)<br>• 可选颜色填充或透明填充<br>• 9种填充颜色选择<br>• **输出填充区域遮罩** |
| **图像翻转** | 对图像进行翻转变换 | • 支持水平翻转和垂直翻转<br>• 6种高质量插值算法<br>• 保持图像质量的精确变换<br>• 批量处理支持 |

### 7. 视频合成工具 (1个节点)

| 节点名称 | 功能描述 | 主要特性 |
|---------|----------|----------|
| **合成视频** | 序列帧到视频的专业转换 | • 支持格式：mp4/webm/avi/mov/gif/mkv/flv<br>• 编码器：H.264/H.265/AV1/ProRes/VP9<br>• 自定义压缩率、帧率、质量参数 |

### 8. 智能缓存管理系统 (1个节点)

| 节点名称 | 功能描述 | 主要特性 |
|---------|----------|----------|
| **图像缓存** | 智能图像缓存和批量管理 | • 支持99张图像缓存上限<br>• 实时预览显示所有缓存图像<br>• 达到上限自动保存到独立目录<br>• 支持手动清理缓存和预览<br>• 多实例完全隔离运行 |

### 9. 调试工具 (2个节点)

| 节点名称 | 功能描述 | 主要特性 |
|---------|----------|----------|
| **我想看看** | 通用数据查看器和系统监控 | • 支持任意数据类型显示<br>• 实时显示数据类型、尺寸、运行时长<br>• 内存和GPU使用监控<br>• 透传输出不修改原数据<br>• 零CSS纯净架构，基于HTML标准属性 |
| **让我看看** | 极简纯净内容显示工具 | • 直接输出原始数据内容，无任何格式化<br>• 无额外分析信息，专注内容本身<br>• 支持任意数据类型，自动适配显示<br>• 透传输出不修改原数据<br>• 零CSS纯净架构，轻量化设计 |

---

## 💡 使用示例  

### 🎨 SVG工作流示例
```
1. 加载SVG文件 → 读取矢量图标
2. SVG转图像 → 转换为PNG格式
3. 图像转SVG → 优化后重新矢量化
4. 保存SVG → 输出到指定目录
```

### 🎭 遮罩处理流水线  
```
1. 遮罩拆分 → 分离复杂元素
2. 遮罩缩放 → 调整到目标尺寸
3. 遮罩混合 → 多遮罩组合处理
4. 遮罩扩张 → 扩展选区范围
5. 图像遮罩转换 → 可视化结果
```

### 📝 条件分支工作流
```
1. 文本对比 → 检测关键词匹配
2. 根据布尔结果 → 切换不同处理分支
3. 实现智能内容筛选和模板选择
```

### 🤖 AI对话工作流
```
1. GLM_语言丨API → 连接智谱GLM语言模型
2. 选择模型 → GLM-4.5-flash（快速）或GLM-4-long（长文档）
3. 输入提示词 → 创意写作、文档分析、代码生成
4. 多轮对话 → 保持上下文，实现连续对话
5. 获取结果 → 生成文本 + token统计 + 对话信息
```

### 👁️ AI视觉理解工作流
```
1. GLM_视觉丨API → 连接智谱GLM视觉模型
2. 输入图像 → 上传要分析的图片
3. 选择模型 → GLM-4.5V（推荐）/4.1V-thinking/4V系列
4. 输入问题 → "描述图片内容"、"图中有什么文字？"
5. 设置质量 → auto自动/low快速/high精细
6. 获取结果 → 图像分析文本 + 对话信息 + token统计
```

### 🚀 DeepSeek推理工作流
```
1. DeepSeek_语言丨API → 连接DeepSeek语言模型
2. 选择平台 → 火山引擎/阿里云百炼/硅基流动
3. 选择模型 → DeepSeek-V3.1（最新）/R1（推理）/V3（稳定）
4. 输入提示词 → 复杂推理、数学计算、代码分析
5. 调节参数 → 温度、top_p、频率惩罚、最大token
6. 多轮对话 → 支持最多20轮连续推理对话
7. 获取结果 → 推理文本 + token统计 + 成本信息
```

### 🔄 数据类型转换流水线
```
1. 字符串到整数 → 将用户输入转换为数值
2. 整数到布尔 → 用于条件判断
3. 布尔到整数 → 转换为数值用于计算
4. 整数到字符串 → 格式化输出结果
```

### 🔄 图像变换处理流程
```
1. 加载图像 → 输入原始图像
2. 图像缩放 → 选择缩放模式和目标尺寸，同时输出缩放后的图像和遮罩
3. 图像旋转 → 设置角度和填充选项，同时输出填充区域遮罩
4. 图像翻转 → 水平或垂直翻转
5. 输出处理后的图像和遮罩信息
```

### 🎬 视频制作管道
```
1. 准备序列帧图像
2. 合成视频 → 选择编码器和参数
3. 输出多格式视频文件
```

### 📦 智能缓存管理
```
1. 图像缓存 → 累积收集生成的图像
2. 实时预览 → 查看所有缓存内容
3. 达到99张 → 自动保存到专用目录
4. 手动清理 → 一键清空缓存和预览
5. 多实例并行 → 不同项目独立管理
```

### 📊 数据分析处理流程
```
1. 图像数据分析 → 获取图像的批次、尺寸、通道等信息
2. 遮罩数据分析 → 获取遮罩的尺寸、覆盖比例等统计
3. 智能空输入检测 → 精准识别无效或默认输入
4. 详细信息输出 → 内存占用、数值范围、质量评估
```

### 🔧 调试工具使用
```
【我想看看】→ 详细数据分析 + 系统监控
【让我看看】→ 纯净内容显示，无额外信息
```

---

## 🚀 快速开始  

### ⚙️ 🎨QING智能设置配置

全新的智能设置系统，支持实时双向同步和多语言界面：

1. **打开设置界面**
   - 通过ComfyUI菜单 → 设置 → 🎨QING → API配置
   - 支持中文/英文界面自动切换

2. **配置API密钥**（支持六大AI平台）
   - **智谱GLM**: 支持所有GLM语言和视觉模型
   - **月之暗面**: Kimi系列模型调用
   - **火山引擎**: DeepSeek、Kimi、Doubao系列模型调用
   - **阿里云百炼**: DeepSeek、Kimi系列模型调用  
   - **硅基流动**: DeepSeek、Kimi系列模型调用
   - **腾讯云**: DeepSeek系列模型调用
   - **实时同步**: 界面与配置文件自动双向同步

3. **获取API密钥**
   - 智谱GLM: [智谱AI开放平台](https://open.bigmodel.cn/)
   - 月之暗面: [月之暗面开放平台](https://platform.moonshot.cn/)
   - 火山引擎: [火山引擎开放平台](https://www.volcengine.com/)
   - 阿里云百炼: [阿里云百炼平台](https://dashscope.aliyun.com/)
   - 硅基流动: [硅基流动平台](https://siliconflow.cn/)
   - 腾讯云: [腾讯云开放平台](https://cloud.tencent.com/)

4. **配置文件位置**
   - 本地配置文件：`nodes/api/config/config.json`
   - 支持手动编辑和自动备份

配置完成后，所有AI节点将自动使用设置中的API密钥，支持多层级优先级和离线使用！

### 安装步骤  

1. 克隆仓库到ComfyUI的`custom_nodes`目录：  
   ```bash  
   cd ComfyUI/custom_nodes  
   git clone https://github.com/GAOSHI-QING/ComfyUI-QING.git  
   ```  

2. 安装依赖（选择其中一种方式）：  
   
   **方式一：自动化安装（推荐）**
   ```bash  
   cd ComfyUI-QING  
   python install_dependencies.py  
   ```  
   
   **方式二：手动安装**
   ```bash  
   cd ComfyUI-QING  
   pip install -r requirements.txt  
   ```  

3. 重启ComfyUI，节点将自动加载，可在「🎨QING」分类下找到所有节点，支持多语言显示。

### ⚠️ 重要提示
- **视频合成功能**需要系统安装FFmpeg
- **SVG处理**推荐安装cairosvg以获得最佳效果
- **API功能**需要配置相应平台API密钥（智谱GLM、月之暗面、火山引擎、阿里云百炼、硅基流动、腾讯云），支持实时同步管理
- 如遇到安装问题，请使用自动化安装脚本进行诊断


## 📦 依赖说明  

### 核心依赖 (必需)
| 库名 | 版本要求 | 用途 | 相关节点 |
|------|----------|------|----------|
| **Pillow** | ≥9.0.0 | 图像基础处理 | 所有图像相关节点 |
| **opencv-python** | ≥4.5.0 | 计算机视觉处理 | 遮罩拆分、图像转SVG、遮罩扩张 |
| **scipy** | ≥1.7.0 | 科学计算 | 遮罩拆分、遮罩扩张 |
| **scikit-image** | ≥0.18.0 | 图像分析 | 遮罩拆分 |
| **cairosvg** | ≥2.5.0 | SVG转换 | SVG转图像、保存SVG预览 |
| **zai-sdk** | ≥0.0.3.3 | 智谱AI API | GLM_语言丨API、GLM_视觉丨API节点 |

### ComfyUI内置依赖 (无需安装)
- **torch**: 张量计算核心
- **numpy**: 数组处理基础

### 可选依赖 (增强功能)
| 库名 | 版本要求 | 用途 | 说明 |
|------|----------|------|------|
| **svglib** | ≥1.4.0 | SVG处理备选 | cairosvg不可用时的备用方案 |
| **reportlab** | ≥3.6.0 | PDF/图形生成 | svglib的依赖库 |

### 系统级依赖
- **FFmpeg**: 视频处理核心 (合成视频节点必需)
  - Windows: [官网下载](https://ffmpeg.org/download.html)
  - Linux: `sudo apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`


## 🌟 参与共建  
欢迎提交Issues反馈问题，或通过PR贡献新功能！无论是节点优化、格式支持扩展还是文档完善，你的参与都能让这个工具更强大。  

让ComfyUI-QING成为你的媒体处理利器，简化流程，释放创意！ 🚀  


---


<a id="english-intro"></a>
# 🎨 ComfyUI-QING: Unlock Full-Scenario Media Processing Capabilities for ComfyUI  

![ComfyUI-QING Banner](https://picsum.photos/seed/qing/1200/300)  

A powerful all-in-one media processing extension tailored for ComfyUI, featuring **30 professional nodes** that simplify complex workflows involving images, SVG, text, video, AI conversation, and visual understanding. Whether for creative design, animation production, AI content generation, or batch processing, it provides precise toolchain support to unleash your creative potential.

## 🆕 Latest Updates

### 🔧 Project Architecture Optimization (September 2025)
- **Node Directory Restructuring**: Reorganized node files in the `nodes` directory into functional subdirectories for cleaner and more intuitive structure
  - 📁 `api/` - API-related nodes and services
  - 📁 `image_processing/` - Image processing nodes
  - 📁 `mask_processing/` - Mask processing nodes
  - 📁 `svg_processing/` - SVG processing nodes
  - 📁 `data_types/` - Data type conversion nodes
  - 📁 `video_processing/` - Video processing nodes
  - 📁 `io_nodes/` - Input/output nodes

### ⚙️ API Key Management System Upgrade
- **Real-time Sync**: ComfyUI settings interface and local configuration files sync in real-time
- **Multi-platform Support**: Zhipu GLM, Moonshot, Volcengine, Alibaba Dashscope, Siliconflow, and Tencent Cloud - six major platforms
- **Smart Priority**: Settings UI → Environment variables → Local files multi-tier management
- **Offline Friendly**: Local storage support, no repeated configuration needed

### 🌐 Internationalization Support
- **Multi-language Settings**: Support for Chinese and English settings interface
- **Node Category Translation**: All node categories support multi-language display
- **Settings Translation**: API key settings support multi-language tooltips and descriptions



## ✨ Core Highlights  
- **🎨QING Smart Settings System**  
  Brand new real-time bidirectional sync settings management, supporting API keys for six major platforms (Zhipu GLM, Moonshot, Volcengine, Alibaba Dashscope, Siliconflow, Tencent Cloud), automatically sync between ComfyUI settings interface and local configuration files, supporting multi-language interface with smart frequency adjustment, one-click configuration for all AI model nodes.

- **Full SVG Workflow Solution**  
  Seamless management of SVG materials from local file loading to high-quality format conversion, perfectly integrating with image generation workflows.  

- **Precision Mask Engineering**  
  Intelligently split, scale, blend, and expand complex masks containing text/graphics, supporting multi-strategy processing while preserving details.  

- **Bidirectional Image-Mask Conversion**  
  Independent conversion system enabling image channel extraction to masks and mask visualization as grayscale images, with each input corresponding to specific outputs.  

- **Text Interaction Engine**  
  Multi-group text comparison and conditional judgment enable workflows to branch intelligently based on content, easily implementing scenarios like template switching and content review.  

- **Professional Video Synthesis**  
  Supports formats including mp4/webm/avi/gif/mkv/flv, with built-in encoders (H.264/H.265/AV1/ProRes, etc.) and customizable compression rates and quality parameters.  


## 🎯 Use Cases  
- **Creative Design Workflows**: Integrate SVG materials into image generation for seamless vector-raster integration.  
- **Fine Mask Processing**: Split, blend, and expand complex text-containing masks for image editing and region replacement.  
- **Image Channel Operations**: Extract specific color channels to create masks, or convert masks to visualized images.  
- **Smart Text Branching**: Automatically switch workflows based on text matching results (e.g., content compliance review, template selection).  
- **Video Creation Pipelines**: Sequence frame animation synthesis, multi-format export, and encoder optimization, covering needs from draft to publication.  
- **Intelligent Cache Management**: Batch collect generated images, real-time preview, automatic saving, and multi-instance project management.


## 📊 Node Overview  
ComfyUI-QING provides **32 professional nodes** covering 11 major functional areas:

| Category | Node Count | Main Functions |
|----------|------------|----------------|
| 🎨 **SVG Processing** | 5 nodes | Load, convert, save, format interchange |
| 🎭 **Mask Engineering** | 7 nodes | Split, scale, blend, expand, judge, convert, preview |
| 📝 **Text Processing** | 1 node | Multi-group comparison, conditional branching |
| 🤖 **API Calls** | 4 nodes | GLM language/vision models, DeepSeek language models, Kimi language models, multi-turn dialogue, intelligent generation |
| 🔄 **Data Type Conversion** | 6 nodes | Integer, string, boolean interconversion, inversion |
| 🔄 **Image Transformation** | 3 nodes | Scaling, rotation, flipping, multiple interpolation algorithms |
| 🎬 **Video Synthesis** | 1 node | Frame sequence to video, multi-format support |
| 📦 **Cache Management** | 1 node | Smart image caching, preview, auto-save |
| 📊 **Data Analysis** | 2 nodes | Image data analysis, mask data analysis |
| 🔧 **Debug Tools** | 2 nodes | Data viewer, system monitor, pure content display |

---

## 🛠️ Detailed Node Documentation  

### 1. SVG Full-Process Toolchain (5 nodes)

| Node Name | Function Description | Key Features |
|-----------|---------------------|--------------|
| **Load SVG File** | Read local SVG file content | • Supports absolute/relative paths<br>• Automatic format validation<br>• Outputs raw SVG content |
| **Load Image (SVG Supported)** | Unified loading of multiple image formats | • Supports PNG/JPG/SVG formats<br>• Simultaneous output of images, masks, metadata<br>• Simplified multi-format asset management |
| **SVG To Image** | High-quality SVG to raster image conversion | • Lossless conversion to PNG/JPG<br>• Custom size and scaling strategies<br>• Configurable background color and interpolation |
| **Image To SVG** | Convert raster images to vector SVG | • Multiple conversion modes (edge detection/color quantization/silhouette)<br>• Preset modes (simple/detailed/artistic)<br>• Intelligent parameter optimization |
| **Save SVG** | Save SVG content to file system | • Custom save directory and overwrite policies<br>• Auto-generate preview images<br>• Adapts to ComfyUI output directory structure |

### 2. Advanced Mask Processing Suite (6 nodes)

| Node Name | Function Description | Key Features |
|-----------|---------------------|--------------|
| **Mask Splitter** | Intelligently split complex multi-element masks | • Preserves text/graphic integrity<br>• Auto-grouping and aggressive merging modes<br>• Small region processing and structure protection |
| **Mask Scale** | Multi-strategy mask size adjustment | • Scale by width/height/long side/short side/pixel count<br>• Multiple interpolation algorithms (nearest/bilinear/lanczos)<br>• Maintains detail clarity |
| **Mask Blend** | Advanced multi-mask blending processing | • 8 blend modes (add/subtract/intersect/XOR, etc.)<br>• Edge effects (feathering/gradient/stroke)<br>• Expert mode and threshold control |
| **Mask Expansion** | Directional mask region expansion | • Independent control for four directions<br>• Configurable expansion distance and feathering<br>• Maintains smooth edge transitions |
| **Mask Judgment** | Mask validity detection and analysis | • Detects if mask is valid<br>• Outputs ratio and statistical information<br>• Provides boolean and numerical results |
| **Image Mask Converter** | Bidirectional conversion between images and masks | • Independent conversion: image1→mask1, mask1→image1<br>• Extract specified channels from images to masks<br>• Convert masks to grayscale images |

### 3. Text Processing Engine (1 node)

| Node Name | Function Description | Key Features |
|-----------|---------------------|--------------|
| **Text Compare** | Multi-group text comparison and conditional judgment | • Supports 3 independent text comparisons<br>• Configurable case sensitivity<br>• Outputs boolean results for conditional branching |

### 4. API Calls (4 nodes)

| Node Name | Function Description | Key Features |
|-----------|---------------------|--------------|
| **GLM_Language丨API** | Zhipu GLM language model API calls and text generation | • Supports 16 GLM language models (GLM-4.5/4/3 series)<br>• Smart multi-turn conversation memory (up to 18 rounds)<br>• Fine-grained parameter control (temperature, top_p, max_tokens)<br>• Complete error handling and intelligent classification<br>• Real-time token statistics and conversation info<br>• Based on official zai-sdk, fully compatible |
| **GLM_Vision丨API** | Zhipu GLM vision model API calls and image understanding | • Supports 5 GLM vision models (GLM-4.5V/4.1V/4V series)<br>• Smart parameter adaptation, auto-solves 1210 compatibility issues<br>• Image + text multi-modal input<br>• Smart image analysis and description generation<br>• Three image quality modes (auto/low/high)<br>• Multi-turn visual conversation memory<br>• Multi-layer parameter retry mechanism, ensures all models work |
| **DeepSeek_Language丨API** | DeepSeek language model API calls and reasoning generation | • Supports 3 DeepSeek models (V3.1/R1/V3 series)<br>• Multi-platform support (Volcengine/Alibaba Dashscope/Siliconflow/Tencent Cloud)<br>• Smart multi-turn conversation memory (up to 25 rounds)<br>• Fine-grained parameter control (temperature, top_p, max_tokens)<br>• Complete error handling and retry mechanism<br>• Detailed token statistics (input/output/total/limit)<br>• Based on OpenAI-compatible API, stable and reliable |
| **Kimi_Language丨API** | Kimi language model API calls and intelligent conversation | • Supports 3 Kimi models (kimi-k2-0905/0711/turbo series)<br>• Multi-platform support (Moonshot/Volcengine/Alibaba Dashscope/Siliconflow)<br>• Ultra-long context capability (2M characters) and web search features<br>• Optimized parameters: max_tokens 4096, history 25 rounds<br>• Creative parameter tuning: temperature 0.8, top_p 0.95<br>• Detailed token statistics (input/output/total/limit)<br>• Specially suited for long document analysis, complex reasoning, and deep conversation |

### 5. Data Type Conversion Tools (6 nodes)

| Node Name | Function Description | Key Features |
|-----------|---------------------|--------------|
| **Integer to String** | Convert integer to string format | • Supports full range integer conversion<br>• Exception handling mechanism<br>• Simple and efficient type conversion |
| **String to Integer** | Convert string to integer | • Auto-handles spaces and formatting<br>• Supports standard mathematical rounding (0.5 rounds up)<br>• Returns default value 0 on conversion failure |
| **String to Boolean** | Convert string to boolean value | • Smart recognition of multiple true/false formats<br>• Supports "true/false", "1/0", "yes/no", etc.<br>• Numeric strings judged by non-zero |
| **Boolean to Integer** | Convert boolean value to integer | • True converts to 1, False converts to 0<br>• Standard boolean logic conversion<br>• Useful for conditional calculations |
| **Integer to Boolean** | Convert integer to boolean value | • 0 converts to False, non-zero converts to True<br>• Standard C-style boolean conversion<br>• Supports conditional branch logic |
| **Boolean Invert** | Perform logical inversion of boolean values | • True inverts to False, False inverts to True<br>• Simple logical NOT operation<br>• Used for conditional logic inversion |

### 6. Image Transformation Tools (3 nodes)

| Node Name | Function Description | Key Features |
|-----------|---------------------|--------------|
| **Image Scale** | Advanced image and mask scaling processing | • 4 scaling modes (keep ratio/stretch/crop/pad)<br>• 6 interpolation algorithms (lanczos/bicubic/bilinear etc.)<br>• 7 scale definitions (longest/shortest side/width/height/percentage/total pixels)<br>• Smart multiple constraints (nearest rounding reduces black borders)<br>• Unlimited value support (for high resolution)<br>• **Outputs both scaled image and mask** |
| **Image Rotation** | Perform precise image rotation operations | • Supports forward/reverse rotation modes<br>• 0-360 degree free angle control<br>• 6 interpolation algorithms (lanczos/bicubic/hamming, etc.)<br>• Optional color fill or transparent fill<br>• 9 fill color options |
| **Image Flipping** | Perform image flipping transformations | • Supports horizontal and vertical flipping<br>• 6 high-quality interpolation algorithms<br>• Precise transformations maintaining image quality<br>• Batch processing support |

### 7. Video Synthesis Tool (1 node)

| Node Name | Function Description | Key Features |
|-----------|---------------------|--------------|
| **Synthetic Video** | Professional frame sequence to video conversion | • Supported formats: mp4/webm/avi/mov/gif/mkv/flv<br>• Encoders: H.264/H.265/AV1/ProRes/VP9<br>• Custom compression rate, frame rate, quality parameters |

### 8. Smart Cache Management System (1 node)

| Node Name | Function Description | Key Features |
|-----------|---------------------|--------------|
| **Image Cache** | Smart image caching and batch management | • Supports up to 99 image cache limit<br>• Real-time preview of all cached images<br>• Auto-save to dedicated directory when limit reached<br>• Manual cache clearing and preview support<br>• Complete isolation for multi-instance operation |

### 9. Debug Tools (2 nodes)

| Node Name | Function Description | Key Features |
|-----------|---------------------|--------------|
| **Let Me See** | Universal data viewer and system monitor | • Supports any data type display<br>• Real-time data type, size, runtime display<br>• Memory and GPU usage monitoring<br>• Pass-through output without modifying original data<br>• Zero-CSS pure architecture based on HTML standards |
| **Show Me Pure** | Minimal pure content display tool | • Direct output of raw data content without formatting<br>• No additional analysis info, focus on content itself<br>• Supports any data type with auto-adaptive display<br>• Pass-through output without modifying original data<br>• Zero-CSS pure architecture with lightweight design |

---

## 💡 Usage Examples  

### 🎨 SVG Workflow Example
```
1. Load SVG File → Read vector icons
2. SVG To Image → Convert to PNG format
3. Image To SVG → Re-vectorize after optimization
4. Save SVG → Output to specified directory
```

### 🎭 Mask Processing Pipeline  
```
1. Mask Splitter → Separate complex elements
2. Mask Scale → Resize to target dimensions
3. Mask Blend → Multi-mask combination processing
4. Mask Expansion → Extend selection range
5. Image Mask Converter → Visualize results
```

### 📝 Conditional Branching Workflow
```
1. Text Compare → Detect keyword matches
2. Based on boolean results → Switch different processing branches
3. Implement intelligent content filtering and template selection
```

### 🤖 AI Conversation Workflow
```
1. GLM_Language丨API → Connect to Zhipu GLM language models
2. Select model → GLM-4.5-flash (fast) or GLM-4-long (long documents)
3. Input prompts → Creative writing, document analysis, code generation
4. Multi-turn dialogue → Maintain context for continuous conversation
5. Get results → Generated text + token statistics + conversation info
```

### 👁️ AI Visual Understanding Workflow
```
1. GLM_Vision丨API → Connect to Zhipu GLM vision models
2. Input image → Upload image to analyze
3. Select model → GLM-4.5V (recommended)/4.1V-thinking/4V series
4. Input question → "Describe image content", "What text is in the image?"
5. Set quality → auto/low/high
6. Get results → Image analysis text + conversation info + token statistics
```

### 🚀 DeepSeek Reasoning Workflow
```
1. DeepSeek_Language丨API → Connect to DeepSeek language models
2. Select platform → Volcengine/Alibaba Dashscope/Siliconflow
3. Select model → DeepSeek-V3.1 (latest)/R1 (reasoning)/V3 (stable)
4. Input prompts → Complex reasoning, mathematical calculations, code analysis
5. Adjust parameters → temperature, top_p, frequency penalty, max tokens
6. Multi-turn dialogue → Support up to 20 rounds of continuous reasoning conversation
7. Get results → Reasoning text + token statistics + cost information
```

### 🔄 Data Type Conversion Pipeline
```
1. String to Integer → Convert user input to numeric values
2. Integer to Boolean → Use for conditional judgment
3. Boolean to Integer → Convert to numeric for calculations
4. Integer to String → Format output results
```

### 🔄 Image Transformation Processing Flow
```
1. Load Image → Input original image
2. Image Scale → Choose scaling mode and target dimensions, outputs both scaled image and mask
3. Image Rotation → Set angle and fill options
4. Image Flipping → Horizontal or vertical flip
5. Output processed image and mask information
```

### 🎬 Video Production Pipeline
```
1. Prepare frame sequence images
2. Synthetic Video → Select encoder and parameters
3. Output multi-format video files
```

---

## 🚀 Quick Start  

### ⚙️ 🎨QING Smart Settings Configuration

Brand new intelligent settings system with real-time bidirectional sync and multi-language interface:

1. **Open Settings Interface**
   - Navigate to ComfyUI Menu → Settings → 🎨QING → API Configuration
   - Supports automatic Chinese/English interface switching

2. **Configure API Keys** (Six Major AI Platforms Supported)
   - **Zhipu GLM**: For all GLM language and vision models
   - **Moonshot**: For Kimi series model calls
   - **Volcengine**: For DeepSeek, Kimi, and Doubao series model calls
   - **Alibaba Dashscope**: For DeepSeek and Kimi series model calls
   - **Siliconflow**: For DeepSeek and Kimi series model calls
   - **Tencent Cloud**: For DeepSeek series model calls
   - **Real-time Sync**: Interface and configuration files sync automatically

3. **Get API Keys**
   - Zhipu GLM: [Zhipu AI Open Platform](https://open.bigmodel.cn/)
   - Moonshot: [Moonshot Open Platform](https://platform.moonshot.cn/)
   - Volcengine: [Volcengine Open Platform](https://www.volcengine.com/)
   - Alibaba Dashscope: [Alibaba Cloud Dashscope](https://dashscope.aliyun.com/)
   - Siliconflow: [Siliconflow Platform](https://siliconflow.cn/)
   - Tencent Cloud: [Tencent Cloud Platform](https://cloud.tencent.com/)

4. **Configuration File Location**
   - Local configuration file: `nodes/api/config/config.json`
   - Supports manual editing and automatic backup

After configuration, all AI nodes will automatically use the API keys from settings, supporting multi-tier priority and offline usage!

### Installation Steps  
1. Clone the repository to ComfyUI's `custom_nodes` directory:  
   ```bash  
   cd ComfyUI/custom_nodes  
   git clone https://github.com/GAOSHI-QING/ComfyUI-QING.git  
   ```  

2. Install dependencies (choose one method):  
   
   **Method 1: Automated Installation (Recommended)**
   ```bash  
   cd ComfyUI-QING  
   python install_dependencies.py  
   ```  
   
   **Method 2: Manual Installation**
   ```bash  
   cd ComfyUI-QING  
   pip install -r requirements.txt  
   ```  

3. Restart ComfyUI. Nodes will load automatically, found under "🎨QING" categories with multi-language support.

### ⚠️ Important Notes
- **Video synthesis** requires system-level FFmpeg installation
- **SVG processing** recommends cairosvg for best results
- **API functionality** requires corresponding platform API keys (Zhipu GLM, Moonshot, Volcengine, Alibaba Dashscope, Siliconflow, Tencent Cloud) with real-time sync management
- If installation issues occur, use the automated installation script for diagnosis


## 📦 Dependencies  

### Core Dependencies (Required)
| Library | Version | Purpose | Related Nodes |
|---------|---------|---------|---------------|
| **Pillow** | ≥9.0.0 | Basic image processing | All image-related nodes |
| **opencv-python** | ≥4.5.0 | Computer vision processing | Mask Splitter, Image To SVG, Mask Expansion |
| **scipy** | ≥1.7.0 | Scientific computing | Mask Splitter, Mask Expansion |
| **scikit-image** | ≥0.18.0 | Image analysis | Mask Splitter |
| **cairosvg** | ≥2.5.0 | SVG conversion | SVG To Image, Save SVG preview |

### ComfyUI Built-in Dependencies (No installation needed)
- **torch**: Core tensor computing
- **numpy**: Basic array processing

### Optional Dependencies (Enhanced features)
| Library | Version | Purpose | Description |
|---------|---------|---------|-------------|
| **svglib** | ≥1.4.0 | Alternative SVG processing | Fallback when cairosvg unavailable |
| **reportlab** | ≥3.6.0 | PDF/graphics generation | Dependency for svglib |

### System-level Dependencies
- **FFmpeg**: Video processing core (required for Synthetic Video node)
  - Windows: [Download from official site](https://ffmpeg.org/download.html)
  - Linux: `sudo apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`


## 🌟 Contribute  
Welcome to submit Issues for feedback or PRs to contribute new features! Whether node optimization, format support expansion, or documentation improvement, your participation makes this tool more powerful.  

Let ComfyUI-QING be your media processing tool, simplifying workflows and unlocking creativity! 🚀
