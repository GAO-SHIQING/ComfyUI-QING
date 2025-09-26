# 🎨QING API配置说明

## 📍 配置文件说明

本目录包含🎨QING项目的API密钥配置文件：`config.json`

初次使用将config_simple.json.example的“.example”后缀去掉!!!

## 🚀 快速配置

### 📝 配置步骤
1. 打开 `config.json` 文件
2. 找到需要配置的平台，将 `value` 字段中的示例文本替换为您的真实API密钥
3. 不需要的平台可以保持原样（留空或不修改）
4. 保存文件，系统会自动同步到ComfyUI设置

### 🎯 填写示例
**修改前：**
```json
"glm_api_key": {
  "value": "在此填写智谱AI密钥 (格式: glm-xxxxxx)"
}
```

**修改后：**
```json
"glm_api_key": {
  "value": "glm-your-actual-api-key-here"
}
```

### 📋 配置文件格式
当前的 `config.json` 文件格式如下：
```json
{
  "api_settings": {
    "glm_api_key": {
      "// ": "🤖 智谱AI (获取: https://open.bigmodel.cn/usercenter/apikeys)",
      "value": "在此填写智谱AI密钥 (格式: glm-xxxxxx)"
    },
    "volcengine_api_key": {
      "// ": "🌋 火山引擎 (获取: https://console.volcengine.com/ark)",
      "value": "在此填写火山引擎密钥 (格式: ak-xxxxxx)"
    },
    "dashscope_api_key": {
      "// ": "☁️ 阿里云百炼 (获取: https://bailian.console.aliyun.com)",
      "value": "在此填写阿里云百炼密钥 (格式: sk-xxxxxx)"
    },
    "siliconflow_api_key": {
      "// ": "💎 硅基流动 (获取: https://cloud.siliconflow.cn/account/ak)",
      "value": "在此填写硅基流动密钥 (格式: sk-xxxxxx)"
    }
  }
}
```

**💡 重要提示：只需要修改 `value` 字段的内容，其他注释和说明请保留！**

### 💡 配置技巧
- ✅ **必要平台**：您只需要配置实际使用的平台，不用的可以留空
- ✅ **格式检查**：配置文件内已包含各平台密钥的格式提示
- ✅ **获取地址**：每个平台都提供了直接的获取链接
- ✅ **即时生效**：保存配置文件后立即生效，无需重启ComfyUI

## 🔑 API密钥获取地址

| 平台 | 获取地址 | 密钥格式 |
|------|----------|----------|
| 🤖 智谱AI | https://open.bigmodel.cn/usercenter/apikeys | `glm-xxxxxx...` |
| 🌋 火山引擎 | https://console.volcengine.com/ark | `ak-xxxxxx...` |
| ☁️ 阿里云百炼 | https://bailian.console.aliyun.com | `sk-xxxxxx...` |
| 💎 硅基流动 | https://cloud.siliconflow.cn/account/ak | `sk-xxxxxx...` |

## 🔄 同步机制

### 双向同步支持
- **配置文件 → ComfyUI设置**：修改配置文件后自动同步到ComfyUI设置面板
- **ComfyUI设置 → 配置文件**：在ComfyUI设置面板修改后自动同步到配置文件

### 使用ComfyUI设置面板
如果您更喜欢图形界面操作：
1. 打开ComfyUI设置
2. 找到"🎨QING"分组
3. 在"API配置"下填写各平台的API密钥
4. 系统会自动保存到本配置文件

## ✨ 功能特性

- 🔄 **实时双向同步**：配置文件与ComfyUI设置完全同步
- 📋 **多平台支持**：支持智谱AI、火山引擎、阿里云百炼、硅基流动
- 🛡️ **向后兼容**：自动兼容旧版配置格式
- 📖 **清晰易懂**：配置文件包含详细说明和获取地址
- 🎯 **精准定位**：明确指示API密钥填写位置

## 🔧 故障排除

### 配置文件不生效？
1. 确认JSON格式正确（可使用在线JSON验证工具）
2. 确认API密钥填写在 `value` 字段中
3. 确认文件保存后重启ComfyUI

### API调用失败？
1. **检查密钥格式**：确认密钥格式符合各平台要求
2. **验证密钥有效性**：在对应平台官网测试密钥是否有效
3. **检查账户余额**：确认各平台账户有足够余额
4. **网络连接**：确认网络可正常访问各平台API

### 同步问题？
1. 重启ComfyUI重新加载配置
2. 检查控制台是否有错误信息
3. 确认配置文件读写权限正常

## 📞 技术支持

### 配置相关
- 配置文件格式问题：检查JSON语法
- 密钥获取问题：参考上方各平台官方链接
- 同步问题：重启ComfyUI

### API调用相关
- 查看ComfyUI控制台错误信息
- 确认选择正确的平台和模型
- 验证API密钥权限和余额

## 🎮 使用流程

配置完成后，您就可以在ComfyUI中使用🎨QING的AI节点了：

1. **加载节点**：在ComfyUI中添加 `DeepSeek_语言丨API` 节点
2. **选择平台**：从"服务端"下拉菜单选择已配置的平台
3. **选择模型**：选择DeepSeek-V3.1、DeepSeek-R1或DeepSeek-V3
4. **开始对话**：输入文本，享受AI对话体验

## 📊 支持的模型

| 平台 | 支持的DeepSeek模型 | 状态 |
|------|-------------------|------|
| 🤖 智谱AI | GLM系列模型 | ✅ 完全支持 |
| 🌋 火山引擎 | DeepSeek-V3.1, DeepSeek-R1, DeepSeek-V3 | ✅ 完全支持 |
| ☁️ 阿里云百炼 | DeepSeek-V3.1, DeepSeek-R1, DeepSeek-V3 | ✅ 完全支持 |
| 💎 硅基流动 | DeepSeek-V3.1, DeepSeek-R1, DeepSeek-V3 | ✅ 完全支持 |

---

**🎯 核心提醒：配置成功的关键是在各平台的 `value` 字段正确填写有效的API密钥！**

**🚀 开始使用：配置完成后，在ComfyUI中搜索"DeepSeek"即可找到相关节点！**
