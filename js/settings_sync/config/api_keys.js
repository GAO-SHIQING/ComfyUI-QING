/**
 * API Key配置中心
 * 统一管理所有API密钥的配置定义
 */

/**
 * API Key配置列表
 */
export const API_KEY_CONFIGS = [
    {
        id: "GLM_API_Key",
        provider: "智谱GLM",
        configKey: "glm_api_key",
        models: ["GLM-4", "GLM-4V", "GLM-3-Turbo"],
        tooltip: "智谱AI的API密钥，用于GLM语言和视觉模型调用。修改后会实时同步到本地配置文件。"
    },
    {
        id: "Volcengine_API_Key",
        provider: "火山引擎",
        configKey: "volcengine_api_key",
        models: ["Doubao", "Kimi", "DeepSeek"],
        tooltip: "火山引擎平台的API密钥，用于各类模型调用。修改后会实时同步到本地配置文件。"
    },
    {
        id: "Dashscope_API_Key",
        provider: "阿里云百炼",
        configKey: "dashscope_api_key",
        models: ["Qwen", "DeepSeek", "Kimi"],
        tooltip: "阿里云百炼平台的API密钥，用于各类模型调用。修改后会实时同步到本地配置文件。"
    },
    {
        id: "Siliconflow_API_Key",
        provider: "硅基流动",
        configKey: "siliconflow_api_key",
        models: ["GLM", "Qwen", "DeepSeek", "Kimi"],
        tooltip: "硅基流动平台的API密钥，用于各类模型调用。修改后会实时同步到本地配置文件。"
    },
    {
        id: "TencentLkeap_API_Key",
        provider: "腾讯云",
        configKey: "tencent_lkeap_api_key",
        models: ["DeepSeek"],
        tooltip: "腾讯云知识引擎平台的API密钥，用于DeepSeek模型调用。修改后会实时同步到本地配置文件。"
    },
    {
        id: "Moonshot_API_Key",
        provider: "月之暗面",
        configKey: "moonshot_api_key",
        models: ["Kimi"],
        tooltip: "月之暗面平台的API密钥，用于Kimi模型调用。修改后会实时同步到本地配置文件。"
    },
    {
        id: "Gemini_API_Key",
        provider: "Google Gemini",
        configKey: "gemini_api_key",
        models: ["Gemini-2.5", "Gemini-2.0"],
        tooltip: "Google AI Studio平台的API密钥，用于Gemini视觉模型调用。修改后会实时同步到本地配置文件。"
    }
];

/**
 * 生成API Key映射（用于同步逻辑）
 */
export function getApiKeyMappings() {
    return API_KEY_CONFIGS.map(cfg => ({
        settingId: `🎨QING.API配置.${cfg.id}`,
        configKey: cfg.configKey
    }));
}

/**
 * 自动生成ComfyUI设置定义
 * @param {Function} onChangeFn - onChange回调函数
 */
export function generateSettingsDefinitions(onChangeFn) {
    return API_KEY_CONFIGS.map(cfg => ({
        id: `🎨QING.API配置.${cfg.id}`,
        name: `${cfg.provider} API Key`,
        type: "text",
        defaultValue: "",
        tooltip: cfg.tooltip,
        attrs: {
            type: "password",
            placeholder: "请输入API Key..."
        },
        onChange: (newVal, oldVal) => {
            if (onChangeFn) {
                onChangeFn(newVal, cfg.configKey);
            }
        }
    }));
}

/**
 * 根据configKey获取配置
 */
export function getConfigByKey(configKey) {
    return API_KEY_CONFIGS.find(cfg => cfg.configKey === configKey);
}

/**
 * 根据settingId获取配置
 */
export function getConfigBySettingId(settingId) {
    const id = settingId.replace('🎨QING.API配置.', '');
    return API_KEY_CONFIGS.find(cfg => cfg.id === id);
}

