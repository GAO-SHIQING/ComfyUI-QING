/**
 * GLM API 节点配置
 */

export const GLM_CONFIGS = {
    // GLM Language API节点配置
    "GLMLanguageAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "智谱AI": [
                "GLM-4.5-Flash",
                "GLM-4.5",
                "GLM-4.5-X",
                "GLM-4.5-Air",
                "GLM-4.5-AirX",
                "GLM-4-Flash",
                "GLM-4-Flash-250414",
                "GLM-4-FlashX",
                "GLM-4-Plus",
                "GLM-4",
                "GLM-4-0520",
                "GLM-4-Long",
                "GLM-4-Air",
                "GLM-4-AirX",
                "GLM-3-Turbo"
            ],
            "硅基流动": [
                "GLM-4.5",
                "GLM-4.5-Air",
                "GLM-Z1-32B-0414",
                "GLM-4-32B-0414",
                "GLM-Z1-9B-0414",
                "GLM-4-9B-0414"
            ]
        },
        defaultModel: {
            "智谱AI": "GLM-4.5-Flash",
            "硅基流动": "GLM-4.5"
        }
    },
    
    // GLM Vision API节点配置
    "GLMVisionAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "智谱AI": [
                "GLM-4.5V",
                "GLM-4.1V-Thinking-FlashX", 
                "GLM-4V-Flash",
                "GLM-4V",
                "GLM-4V-Plus"
            ],
            "硅基流动": [
                "GLM-4.5V",
                "GLM-4.1V-9B-Thinking"
            ]
        },
        defaultModel: {
            "智谱AI": "GLM-4.5V",
            "硅基流动": "GLM-4.5V"
        }
    }
};

