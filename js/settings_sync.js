/**
 * 改进的🎨QING设置同步模块
 * 参考comfyui_prompt_assistant项目的最佳实践
 * 实现ComfyUI设置与本地配置文件的双向同步
 */

import { app } from "../../scripts/app.js";


class QingSettingsSync {
    constructor() {
        this.configEndpoint = "/api/qing/config";
        this.syncInterval = null;
        this.lastKnownConfig = {}; // 存储完整的配置状态
        this.lastKnownTimestamp = "";
        this.isSyncing = false; // 防止同步冲突
        this.syncCheckCount = 0; // 用于智能调节检查频率
        
        this.init();
    }
    
    async init() {
        // 延迟初始化，确保ComfyUI设置系统已加载
        setTimeout(() => {
            this.setupSettingsSync();
            this.startPeriodicSync();
        }, 2000);
    }
    
    /**
     * 设置ComfyUI设置同步
     */
    setupSettingsSync() {
        try {
            // 执行初始同步
            this.performInitialSync();
            
        } catch (error) {
            console.error("❌ 🎨QING设置同步启动失败:", error);
        }
    }
    
    /**
     * 执行初始同步
     */
    async performInitialSync() {
        try {
            // 先从本地配置获取当前状态
            const response = await fetch(this.configEndpoint, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const config = await response.json();
                const localTimestamp = config.api_settings?.last_updated || "";
                
                // 初始化状态
                this.lastKnownTimestamp = localTimestamp;
                this.lastKnownConfig = this.extractApiKeysConfig(config);
                
                // 同步所有API密钥设置（排除标题项）
                const apiKeyMappings = this.getApiKeyMappings();
                
                for (const mapping of apiKeyMappings) {
                    const localValue = this.getConfigValue(config, mapping.configKey);
                    const comfyuiValue = app.extensionManager.setting.get(mapping.settingId) || "";
                    
                    // 无论本地值是否为空，都以本地配置为准（这样删除密钥会正确同步）
                    if (localValue !== comfyuiValue) {
                        app.extensionManager.setting.set(mapping.settingId, localValue, false);
                    }
                }
            } else {
                // 无法获取本地配置，以ComfyUI设置为准
                const comfyuiValue = app.extensionManager.setting.get("🎨QING.API配置.GLM_API_Key") || "";
                if (comfyuiValue) {
                    await this.syncToLocalConfig(comfyuiValue, "glm_api_key");
                }
            }
        } catch (error) {
            console.error("❌ 初始同步失败:", error);
        }
    }
    
    /**
     * 获取API密钥映射配置
     */
    getApiKeyMappings() {
        return [
            { settingId: "🎨QING.API配置.GLM_API_Key", configKey: "glm_api_key" },
            { settingId: "🎨QING.API配置.Volcengine_API_Key", configKey: "volcengine_api_key" },
            { settingId: "🎨QING.API配置.Dashscope_API_Key", configKey: "dashscope_api_key" },
            { settingId: "🎨QING.API配置.Siliconflow_API_Key", configKey: "siliconflow_api_key" },
            { settingId: "🎨QING.API配置.TencentLkeap_API_Key", configKey: "tencent_lkeap_api_key" },
            { settingId: "🎨QING.API配置.Moonshot_API_Key", configKey: "moonshot_api_key" },
            { settingId: "🎨QING.API配置.Gemini_API_Key", configKey: "gemini_api_key" }
        ];
    }
    
    /**
     * 从配置中提取API密钥值
     */
    getConfigValue(config, configKey) {
        const localSetting = config.api_settings?.[configKey];
        if (typeof localSetting === 'object' && localSetting !== null) {
            return localSetting.value || "";
        } else if (typeof localSetting === 'string') {
            return localSetting;
        }
        return "";
    }
    
    /**
     * 提取API密钥配置状态用于变更检测
     */
    extractApiKeysConfig(config) {
        const apiKeyMappings = this.getApiKeyMappings();
        const extracted = {};
        
        for (const mapping of apiKeyMappings) {
            extracted[mapping.configKey] = this.getConfigValue(config, mapping.configKey);
        }
        
        return extracted;
    }
    
    /**
     * 检测配置是否有变更
     */
    hasConfigChanged(newConfig, newTimestamp) {
        // 首先检查时间戳
        if (newTimestamp !== this.lastKnownTimestamp) {
            return true;
        }
        
        // 然后逐一比较每个API密钥
        const newExtracted = this.extractApiKeysConfig(newConfig);
        const apiKeyMappings = this.getApiKeyMappings();
        
        for (const mapping of apiKeyMappings) {
            const oldValue = this.lastKnownConfig[mapping.configKey] || "";
            const newValue = newExtracted[mapping.configKey] || "";
            if (oldValue !== newValue) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * 同步到本地配置文件
     */
    async syncToLocalConfig(apiKey, configKey = "glm_api_key") {
        if (this.isSyncing) {
            return;
        }
        
        try {
            this.isSyncing = true;
            
            const response = await fetch(this.configEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'update_api_key',
                    api_key: apiKey,
                    config_key: configKey,
                    source: 'comfyui_settings'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                // 更新本地缓存状态
                this.lastKnownConfig[configKey] = apiKey;
                this.lastKnownTimestamp = new Date().toISOString();
            }
        } catch (error) {
            // 静默处理错误，避免过多日志
        } finally {
            this.isSyncing = false;
        }
    }
    
    /**
     * 从本地配置同步到ComfyUI设置
     */
    async syncFromLocalConfig() {
        if (this.isSyncing) {
            return; // 避免同步冲突
        }
        
        try {
            const response = await fetch(this.configEndpoint, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const config = await response.json();
                const localTimestamp = config.api_settings?.last_updated || "";
                
                // 使用改进的变更检测逻辑
                if (this.hasConfigChanged(config, localTimestamp)) {
                    this.isSyncing = true;
                    
                    // 更新所有API密钥设置
                    const apiKeyMappings = this.getApiKeyMappings();
                    
                    for (const mapping of apiKeyMappings) {
                        const configValue = this.getConfigValue(config, mapping.configKey);
                        const currentValue = app.extensionManager.setting.get(mapping.settingId) || "";
                        
                        // 只有当值真的不同时才更新（包括空值，确保删除操作被正确同步）
                        if (configValue !== currentValue) {
                            app.extensionManager.setting.set(mapping.settingId, configValue, false);
                        }
                    }
                    
                    // 更新本地状态缓存
                    this.lastKnownConfig = this.extractApiKeysConfig(config);
                    this.lastKnownTimestamp = localTimestamp;
                    
                    // 重置检查计数，表示发现了变更
                    this.syncCheckCount = 0;
                    
                    // 延迟重置同步标志
                    setTimeout(() => {
                        this.isSyncing = false;
                    }, 100);
                } else {
                    // 增加检查计数，用于智能调节检查频率
                    this.syncCheckCount++;
                }
            }
        } catch (error) {
            // 静默处理连接错误，避免过多日志
            this.syncCheckCount++;
        }
    }
    
    /**
     * 启动定期同步 - 智能监听
     */
    startPeriodicSync() {
        // 智能调节检查频率：初始2秒，无变更时逐渐增加到最大10秒
        this.syncInterval = setInterval(() => {
            this.syncFromLocalConfig();
        }, this.getAdaptiveInterval());
        
        // 定期重新评估检查间隔
        setInterval(() => {
            if (this.syncInterval) {
                clearInterval(this.syncInterval);
                this.syncInterval = setInterval(() => {
                    this.syncFromLocalConfig();
                }, this.getAdaptiveInterval());
            }
        }, 30000); // 每30秒重新评估一次
    }
    
    /**
     * 获取自适应检查间隔
     */
    getAdaptiveInterval() {
        // 基础间隔2秒，如果长时间无变更，逐渐增加到最大10秒
        const baseInterval = 2000;
        const maxInterval = 10000;
        const increaseStep = 1000;
        
        const adaptiveInterval = Math.min(
            baseInterval + (Math.floor(this.syncCheckCount / 10) * increaseStep),
            maxInterval
        );
        
        return adaptiveInterval;
    }
    
    /**
     * 停止同步
     */
    stopSync() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
    }
}

// 创建全局实例
window.qingSettingsSync = new QingSettingsSync();

// 注册设置项 - 使用标准的ComfyUI设置系统

// 创建一个主extension来管理所有API设置
app.registerExtension({
    name: "API配置",
    async setup() {
        // Extension setup code
    },
    settings: [
        {
            id: "🎨QING.API配置.GLM_API_Key",
            name: "智谱GLM API Key",
            type: "text",
            defaultValue: "",
            tooltip: "智谱AI的API密钥，用于GLM语言和视觉模型调用。修改后会实时同步到本地配置文件。",
            attrs: {
                type: "password",
                placeholder: "请输入API Key..."
            },
            onChange: (newVal, oldVal) => {
                if (window.qingSettingsSync && !window.qingSettingsSync.isSyncing) {
                    window.qingSettingsSync.syncToLocalConfig(newVal, "glm_api_key");
                }
            }
        },
        {
            id: "🎨QING.API配置.Volcengine_API_Key",
            name: "火山引擎 API Key",
            type: "text",
            defaultValue: "",
            tooltip: "火山引擎平台的API密钥，用于各类模型调用。修改后会实时同步到本地配置文件。",
            attrs: {
                type: "password",
                placeholder: "请输入API Key..."
            },
            onChange: (newVal, oldVal) => {
                if (window.qingSettingsSync && !window.qingSettingsSync.isSyncing) {
                    window.qingSettingsSync.syncToLocalConfig(newVal, "volcengine_api_key");
                }
            }
        },
        {
            id: "🎨QING.API配置.Dashscope_API_Key",
            name: "阿里云百炼 API Key",
            type: "text",
            defaultValue: "",
            tooltip: "阿里云百炼平台的API密钥，用于各类模型调用。修改后会实时同步到本地配置文件。",
            attrs: {
                type: "password",
                placeholder: "请输入API Key..."
            },
            onChange: (newVal, oldVal) => {
                if (window.qingSettingsSync && !window.qingSettingsSync.isSyncing) {
                    window.qingSettingsSync.syncToLocalConfig(newVal, "dashscope_api_key");
                }
            }
        },
        {
            id: "🎨QING.API配置.Siliconflow_API_Key",
            name: "硅基流动 API Key",
            type: "text",
            defaultValue: "",
            tooltip: "硅基流动平台的API密钥，用于各类模型调用。修改后会实时同步到本地配置文件。",
            attrs: {
                type: "password",
                placeholder: "请输入API Key..."
            },
            onChange: (newVal, oldVal) => {
                if (window.qingSettingsSync && !window.qingSettingsSync.isSyncing) {
                    window.qingSettingsSync.syncToLocalConfig(newVal, "siliconflow_api_key");
                }
            }
        },
        {
            id: "🎨QING.API配置.TencentLkeap_API_Key",
            name: "腾讯云 API Key",
            type: "text",
            defaultValue: "",
            tooltip: "腾讯云知识引擎平台的API密钥，用于DeepSeek模型调用。修改后会实时同步到本地配置文件。",
            attrs: {
                type: "password",
                placeholder: "请输入API Key..."
            },
            onChange: (newVal, oldVal) => {
                if (window.qingSettingsSync && !window.qingSettingsSync.isSyncing) {
                    window.qingSettingsSync.syncToLocalConfig(newVal, "tencent_lkeap_api_key");
                }
            }
        },
        {
            id: "🎨QING.API配置.Moonshot_API_Key",
            name: "月之暗面 API Key",
            type: "text",
            defaultValue: "",
            tooltip: "月之暗面平台的API密钥，用于Kimi模型调用。修改后会实时同步到本地配置文件。",
            attrs: {
                type: "password",
                placeholder: "请输入API Key..."
            },
            onChange: (newVal, oldVal) => {
                if (window.qingSettingsSync && !window.qingSettingsSync.isSyncing) {
                    window.qingSettingsSync.syncToLocalConfig(newVal, "moonshot_api_key");
                }
            }
        },
        {
            id: "🎨QING.API配置.Gemini_API_Key",
            name: "Google Gemini API Key",
            type: "text",
            defaultValue: "",
            tooltip: "Google AI Studio平台的API密钥，用于Gemini视觉模型调用。修改后会实时同步到本地配置文件。",
            attrs: {
                type: "password",
                placeholder: "请输入API Key..."
            },
            onChange: (newVal, oldVal) => {
                if (window.qingSettingsSync && !window.qingSettingsSync.isSyncing) {
                    window.qingSettingsSync.syncToLocalConfig(newVal, "gemini_api_key");
                }
            }
        }
    ]
});


export { QingSettingsSync };