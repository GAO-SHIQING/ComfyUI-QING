/**
 * Qwen API 节点配置
 */

export const QWEN_CONFIGS = {
    // Qwen Vision API节点配置
    "QwenVisionAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "阿里云百炼": [
                "qwen3-vl-plus", 
                "qwen3-vl-235b-a22b-instruct", 
                "qwen-vl-max-latest", 
                "qwen2.5-vl-72b-instruct"
            ],
            "硅基流动": ["qwen2.5-vl-72b-instruct"]
        },
        defaultModel: {
            "阿里云百炼": "qwen3-vl-plus",
            "硅基流动": "qwen2.5-vl-72b-instruct"
        }
    },
    
    // Qwen Language API节点配置
    "QwenLanguageAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "阿里云百炼": [
                "qwen3-max", 
                "qwen3-235b-a22b-instruct-2507", 
                "qwen3-30b-a3b-instruct-2507", 
                "qwen-plus", 
                "qwen-max", 
                "qwq-plus", 
                "qwen-turbo"
            ],
            "硅基流动": [
                "qwen3-next-80b-a3b-instruct", 
                "qwen3-235b-a22b-instruct-2507", 
                "qwen3-30b-a3b-instruct-2507", 
                "qwen3-8b"
            ]
        },
        defaultModel: {
            "阿里云百炼": "qwen3-max",
            "硅基流动": "qwen3-next-80b-a3b-instruct"
        }
    }
};

