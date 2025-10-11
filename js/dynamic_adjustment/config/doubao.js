/**
 * Doubao API 节点配置
 */

export const DOUBAO_CONFIGS = {
    // Doubao Vision API节点配置
    "DoubaoVisionAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "火山引擎": [
                "Doubao-Seed-1.6", 
                "Doubao-Seed-1.6-thinking", 
                "Doubao-Seed-1.6-flash", 
                "Doubao-Seed-1.6-vision", 
                "Doubao-1.5-vision-pro", 
                "Doubao-1.5-vision-lite", 
                "Doubao-1.5-thinking-vision-pro",
                "Doubao-1.5-UI-TARS",
                "Doubao-Seed-Translation"
            ]
        },
        defaultModel: {
            "火山引擎": "Doubao-1.5-vision-pro"
        }
    }
};

