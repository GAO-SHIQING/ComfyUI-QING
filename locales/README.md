# 🌍 ComfyUI-QING 国际化支持

本目录包含ComfyUI-QING项目的多语言支持文件，基于[ComfyUI官方国际化文档](https://docs.comfy.org/zh-CN/custom-nodes/i18n)实现。

## 📁 目录结构

```
locales/
├── en/                    # 英语翻译
│   ├── main.json          # 所有翻译内容（节点分类、设置分类、设置项）
│   └── nodeDefs.json      # 节点定义翻译  
├── zh/                    # 中文翻译
│   ├── main.json          # 所有翻译内容（节点分类、设置分类、设置项）
│   └── nodeDefs.json      # 节点定义翻译
└── README.md              # 本说明文档
```

## 🔧 已实现的国际化功能

### ⚙️ 设置项翻译

#### 🎨 节点对齐设置（9个）
- **菜单外圈半径** / **Menu Outer Radius** - 调整菜单大小
- **菜单内圈半径** / **Menu Inner Radius** - 调整取消区域
- **主色调** / **Primary Color** - 对齐/分布操作颜色
- **次色调** / **Secondary Color** - 居中/拉伸操作颜色
- **动画速度** / **Animation Speed** - 菜单动画速度
- **提示框偏移** / **Tooltip Offset** - 提示框位置
- **消息持续时间** / **Message Duration** - 消息显示时长
- **撤回历史记录** / **Undo History** - 可撤销步数
- **菜单快捷键** / **Menu Shortcut** - 快捷键组合

#### 🤖 API密钥设置（7个）
- **智谱GLM API Key** - 智谱AI平台密钥
- **月之暗面 API Key** / **Moonshot API Key** - Kimi模型密钥
- **火山引擎 API Key** / **Volcengine API Key** - DeepSeek/Doubao模型密钥
- **阿里云百炼 API Key** / **Alibaba Dashscope API Key** - Qwen模型密钥
- **硅基流动 API Key** / **Siliconflow API Key** - 多模型平台密钥
- **腾讯云 API Key** / **Tencent Cloud API Key** - DeepSeek模型密钥
- **Google Gemini API Key** - Gemini视觉模型密钥

### 📂 设置分类翻译
- **🎨QING** - 主分类
- **节点对齐** / **Node Alignment** - 节点对齐工具分类
- **API配置** / **API Configuration** - API配置分类

### 🎯 节点分类翻译
- 🖼️ **图像处理** / **Image Processing**
- 🎭 **遮罩处理** / **Mask Processing**
- 🎨 **SVG处理** / **SVG Processing**
- 📊 **数据类型** / **Data Types**
- 🎬 **视频处理** / **Video Processing**
- 📁 **输入输出** / **Input/Output**
- ⚙️ **配置管理** / **Config Management**
- 🤖 **API调用** / **API Calls**
- 🔧 **调试** / **Debug**

## 📋 文件说明

### main.json
包含所有翻译内容（统一文件）：
- **`nodeCategories`**: 节点分类翻译（🖼️图像处理、🎭遮罩处理等）
- **`settingsCategories`**: 设置分类翻译（节点对齐、API配置等）
- **`settings`**: 设置项详细翻译
  - 设置项名称（`name`）
  - 提示信息（`tooltip`）
  - 支持16个设置项（9个节点对齐 + 7个API密钥）

### nodeDefs.json
包含节点定义的翻译（由现有翻译系统维护）：
- 节点名称翻译
- 输入输出参数翻译
- 节点描述翻译

**注意**: `settings.json` 已废弃，所有设置翻译现在统一在 `main.json` 中

## 🚀 使用方式

国际化功能会在ComfyUI启动时自动加载：

1. 主`__init__.py`调用`load_translation(__file__)`
2. ComfyUI根据用户语言设置自动选择对应翻译
3. 设置界面和节点分类会显示本地化文本

## 🔄 添加新翻译

### 方式一：手动添加（推荐用于少量翻译）

在 `locales/zh/main.json` 和 `locales/en/main.json` 中添加：

#### 1. 添加设置项翻译
```json
{
  "settings": {
    "🎨QING.设置分类.设置项名称": {
      "name": "显示名称",
      "tooltip": "提示信息"
    }
  }
}
```

#### 2. 添加设置分类翻译
```json
{
  "settingsCategories": {
    "设置分类": "Settings Category"
  }
}
```

#### 3. 添加节点分类翻译
```json
{
  "nodeCategories": {
    "🎨QING/新分类": "🎨QING/New Category"
  }
}
```

### 方式二：通过模块化系统（推荐用于API密钥）

对于API密钥设置，现在使用模块化系统自动管理：

1. **在 `js/settings_sync/config/api_keys.js` 中添加配置**：
```javascript
{
    id: "🎨QING.API配置.NewPlatform_API_Key",
    provider: "新平台",
    configKey: "newplatform_api_key",
    tooltip: "新平台的API密钥说明"
}
```

2. **在 locales 中添加翻译**（同方式一）

3. **自动生成**：设置定义会自动生成，无需手动编写

### 注意事项
- ⚠️ 设置项ID使用 `.` 分隔（如 `🎨QING.API配置.GLM_API_Key`）
- ⚠️ 分类名称保持一致（如 `节点对齐`、`API配置`）
- ⚠️ 中英文都要添加对应翻译
- ✅ 使用有意义的 tooltip 帮助用户理解

## 📊 翻译覆盖统计

### 当前支持的翻译（v1.2.0）
- **节点分类**: 8个（中英文）
- **设置分类**: 3个（中英文）
- **设置项**: 16个（中英文）
  - 节点对齐：9个
  - API密钥：7个
- **语言**: 2种（中文、英文）

### 文件大小
- `zh/main.json`: ~83行
- `en/main.json`: ~83行

## 📚 参考文档

- [ComfyUI官方国际化文档](https://docs.comfy.org/zh-CN/custom-nodes/i18n)
- [ComfyUI国际化演示项目](https://github.com/comfyui-wiki/ComfyUI-i18n-demo)
- [项目JavaScript模块文档](../js/README.md) - settings_sync模块化架构

---
*🎨QING项目 - 让ComfyUI更强大、更易用、更国际化*
