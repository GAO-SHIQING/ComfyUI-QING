/**
 * DeepSeek API 节点配置
 */

export const DEEPSEEK_CONFIGS = {
    // DeepSeek Language API节点配置
    "DeepSeekLanguageAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "火山引擎": ["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            "阿里云百炼": ["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            "硅基流动": ["DeepSeek-V3.1-Terminus", "DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            "腾讯云": ["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"]
        },
        defaultModel: {
            "火山引擎": "DeepSeek-V3.1",
            "阿里云百炼": "DeepSeek-V3.1",
            "硅基流动": "DeepSeek-V3.1",
            "腾讯云": "DeepSeek-V3.1"
        }
    }
};

