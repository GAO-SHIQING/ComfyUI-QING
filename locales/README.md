# 🌍 ComfyUI-QING 国际化支持

本目录包含ComfyUI-QING项目的多语言支持文件，基于[ComfyUI官方国际化文档](https://docs.comfy.org/zh-CN/custom-nodes/i18n)实现。

## 📁 目录结构

```
locales/
├── en/                    # 英语翻译
│   ├── main.json          # 通用翻译内容
│   ├── nodeDefs.json      # 节点定义翻译  
│   └── settings.json      # 设置界面翻译
├── zh/                    # 中文翻译
│   ├── main.json          # 通用翻译内容
│   ├── nodeDefs.json      # 节点定义翻译
│   └── settings.json      # 设置界面翻译
└── README.md              # 本说明文档
```

## 🔧 已实现的国际化功能

### ⚙️ 设置项翻译
- **智谱GLM_API_Key** - API密钥设置项
  - 支持中英双语界面
  - 包含名称、提示信息、占位符文本翻译

### 📂 设置分类翻译
- **🎨QING** - 主分类
- **API配置** / **API Configuration** - API配置分类

### 🎯 节点分类翻译
- 🖼️ **图像处理** / **Image Processing**
- 🎭 **遮罩处理** / **Mask Processing**
- 🎨 **SVG处理** / **SVG Processing**
- 📊 **数据类型** / **Data Types**
- 🎬 **视频处理** / **Video Processing**
- 📁 **输入输出** / **Input/Output**

## 📋 文件说明

### main.json
包含通用翻译内容：
- `nodeCategories`: 节点分类翻译
- `settingsCategories`: 设置分类翻译

### settings.json  
包含设置项的详细翻译：
- 设置项名称和提示信息
- 输入框占位符文本
- 按钮和选项文本

### nodeDefs.json
包含节点定义的翻译（由现有翻译系统维护）

## 🚀 使用方式

国际化功能会在ComfyUI启动时自动加载：

1. 主`__init__.py`调用`load_translation(__file__)`
2. ComfyUI根据用户语言设置自动选择对应翻译
3. 设置界面和节点分类会显示本地化文本

## 🔄 添加新翻译

要添加新的翻译内容：

1. **设置项翻译**：在`settings.json`中添加对应的翻译条目
2. **分类翻译**：在`main.json`的`settingsCategories`中添加分类翻译
3. **节点翻译**：在`nodeDefs.json`中添加节点相关翻译

### 设置项ID转换规则
设置项ID中的`.`需要转换为`_`：
```
"🎨QING.GLM_API_Key" → "🎨QING_GLM_API_Key"
```

## 📚 参考文档

- [ComfyUI官方国际化文档](https://docs.comfy.org/zh-CN/custom-nodes/i18n)
- [ComfyUI国际化演示项目](https://github.com/comfyui-wiki/ComfyUI-i18n-demo)

---
*🎨QING项目 - 让ComfyUI更强大、更易用、更国际化*
