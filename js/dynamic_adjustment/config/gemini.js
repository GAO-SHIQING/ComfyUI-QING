/**
 * Gemini API 节点配置
 */

export const GEMINI_CONFIGS = {
    // Gemini Vision API节点配置
    "GeminiVisionAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "Google AI Studio": [
                "gemini-2.5-pro",
                "gemini-2.5-flash-preview-09-2025",
                "gemini-2.5-flash-lite-preview-09-2025",
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-2.0-flash"
            ]
        },
        defaultModel: {
            "Google AI Studio": "gemini-2.5-flash-lite"
        }
    },
    
    // Gemini Edit API节点配置
    "GeminiEditAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "Google AI Studio": [
                "gemini-2.5-flash-image-preview"
            ]
        },
        defaultModel: {
            "Google AI Studio": "gemini-2.5-flash-image-preview"
        }
    }
};

