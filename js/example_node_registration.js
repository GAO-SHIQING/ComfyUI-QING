/**
 * 示例：如何注册新的API节点到动态调整系统
 * 这个文件展示了如何轻松扩展支持更多API节点
 */

// 等待动态调整系统加载
setTimeout(() => {
    if (window.QINGDynamicAdjustment) {
        
        // 示例1: 注册DeepSeek API节点
        window.QINGDynamicAdjustment.registerNode("DeepSeekLanguageAPI", {
            platformWidget: "platform",
            modelWidget: "model",
            platformModels: {
                "火山引擎": ["deepseek-v3.1", "deepseek-r1", "deepseek-v3"],
                "阿里云百炼": ["deepseek-v3.1", "deepseek-v3"],
                "硅基流动": ["deepseek-v3.1", "deepseek-r1"],
                "腾讯云": ["deepseek-v3.1", "deepseek-r1"]
            },
            defaultModel: {
                "火山引擎": "deepseek-v3.1",
                "阿里云百炼": "deepseek-v3.1", 
                "硅基流动": "deepseek-v3.1",
                "腾讯云": "deepseek-v3.1"
            }
        });
        
        // 示例2: 注册GLM API节点
        window.QINGDynamicAdjustment.registerNode("GLMLanguageAPI", {
            platformWidget: "platform",
            modelWidget: "model", 
            platformModels: {
                "智谱AI": ["glm-4.5", "glm-4", "glm-3-turbo"],
                "智谱开放平台": ["glm-4.5", "glm-4"]
            },
            defaultModel: {
                "智谱AI": "glm-4.5",
                "智谱开放平台": "glm-4.5"
            }
        });
        
        // 示例3: 注册自定义API节点（不同的widget名称）
        window.QINGDynamicAdjustment.registerNode("CustomAPINode", {
            platformWidget: "service_provider",  // 不同的widget名称
            modelWidget: "ai_model",             // 不同的widget名称
            platformModels: {
                "OpenAI": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
                "Anthropic": ["claude-3-opus", "claude-3-sonnet"],
                "Google": ["gemini-pro", "gemini-1.5-pro"]
            },
            defaultModel: {
                "OpenAI": "gpt-4",
                "Anthropic": "claude-3-opus", 
                "Google": "gemini-pro"
            }
        });
        
        // 检查注册状态
        console.log("🎨QING: 已注册的动态模型节点:", 
                   window.QINGDynamicAdjustment.getSupportedNodes());
        
    } else {
        console.warn("🎨QING: 动态调整系统未加载");
    }
}, 1000);

/**
 * 使用说明:
 * 
 * 1. 只需要调用 registerNode() 方法即可添加新节点支持
 * 2. 配置对象包含四个必要字段:
 *    - platformWidget: 平台选择器的widget名称
 *    - modelWidget: 模型选择器的widget名称
 *    - platformModels: 每个平台支持的模型列表
 *    - defaultModel: 每个平台的默认模型
 * 
 * 3. 系统会自动处理:
 *    - 节点创建时的初始化
 *    - 平台切换时的模型列表更新
 *    - 模型的智能选择和回退
 *    - 界面重绘和事件处理
 * 
 * 4. 支持任意widget名称，不限于"platform"和"model"
 * 
 * 5. 可以同时支持无限数量的不同API节点
 */
