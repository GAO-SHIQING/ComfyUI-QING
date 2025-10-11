/**
 * Kimi API 节点配置
 */

export const KIMI_CONFIGS = {
    // Kimi Language API节点配置
    "KimiLanguageAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "月之暗面": ["kimi-k2-0905", "kimi-k2-0711", "kimi-k2-turbo"],
            "火山引擎": ["kimi-k2-0905"],
            "阿里云百炼": ["kimi-k2-0905"], 
            "硅基流动": ["kimi-k2-0905"]
        },
        defaultModel: {
            "月之暗面": "kimi-k2-0905",
            "火山引擎": "kimi-k2-0905",
            "阿里云百炼": "kimi-k2-0905",
            "硅基流动": "kimi-k2-0905"
        }
    },
    
    // Kimi Vision API节点配置
    "KimiVisionAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "月之暗面": ["kimi-latest-8k", "kimi-latest-32k", "kimi-latest-128k"]
        },
        defaultModel: {
            "月之暗面": "kimi-latest-32k"
        }
    }
};

