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
        this.lastKnownValue = "";
        this.lastKnownTimestamp = "";
        this.isSyncing = false; // 防止同步冲突
        
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
                const localApiKey = config.api_settings?.glm_api_key || "";
                const localTimestamp = config.api_settings?.last_updated || "";
                
                // 从ComfyUI设置获取当前值
                const comfyuiValue = app.extensionManager.setting.get("🎨QING.GLM_API_Key") || "";
                
                // 初始化状态
                this.lastKnownTimestamp = localTimestamp;
                
                if (localApiKey && !comfyuiValue) {
                    // 本地有值，ComfyUI设置为空 -> 同步到ComfyUI
                    app.extensionManager.setting.set("🎨QING.GLM_API_Key", localApiKey, true);
                    this.lastKnownValue = localApiKey;
                } else if (comfyuiValue && !localApiKey) {
                    // ComfyUI有值，本地为空 -> 同步到本地
                    await this.syncToLocalConfig(comfyuiValue);
                } else {
                    // 两边都有值或都为空，以本地配置为准
                    this.lastKnownValue = localApiKey;
                    if (localApiKey !== comfyuiValue) {
                        app.extensionManager.setting.set("🎨QING.GLM_API_Key", localApiKey, true);
                    }
                }
            } else {
                // 无法获取本地配置，以ComfyUI设置为准
                const comfyuiValue = app.extensionManager.setting.get("🎨QING.GLM_API_Key") || "";
                this.lastKnownValue = comfyuiValue;
                if (comfyuiValue) {
                    await this.syncToLocalConfig(comfyuiValue);
                }
            }
        } catch (error) {
            console.error("❌ 初始同步失败:", error);
        }
    }
    
    /**
     * 同步到本地配置文件
     */
    async syncToLocalConfig(apiKey) {
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
                    source: 'comfyui_settings'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.lastKnownValue = apiKey;
                this.lastKnownTimestamp = new Date().toISOString();
            } else {
                console.warn("⚠️ 同步到本地配置失败");
            }
        } catch (error) {
            console.warn("⚠️ 无法连接到配置服务:", error.message);
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
                const localApiKey = config.api_settings?.glm_api_key || "";
                const localTimestamp = config.api_settings?.last_updated || "";
                
                // 检查时间戳，只有当本地配置更新时才同步
                const shouldSync = localTimestamp !== this.lastKnownTimestamp && 
                                 localApiKey !== this.lastKnownValue;
                
                if (shouldSync) {
                    this.isSyncing = true;
                    
                    // 更新ComfyUI设置（不保存，避免触发onChange循环）
                    app.extensionManager.setting.set("🎨QING.GLM_API_Key", localApiKey, false);
                    this.lastKnownValue = localApiKey;
                    this.lastKnownTimestamp = localTimestamp;
                    
                    
                    // 延迟重置同步标志
                    setTimeout(() => {
                        this.isSyncing = false;
                    }, 100);
                }
            }
        } catch (error) {
            console.warn("⚠️ 从本地配置同步失败:", error.message);
        }
    }
    
    /**
     * 启动定期同步 - 智能监听
     */
    startPeriodicSync() {
        // 每2秒检查一次本地配置是否有变化（平衡性能和响应性）
        this.syncInterval = setInterval(() => {
            this.syncFromLocalConfig();
        }, 2000);
        
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

// 注册改进的设置项
app.registerExtension({
    name: "QING.ImprovedSettings",
    settings: [
        {
            id: "🎨QING.GLM_API_Key",
            name: "智谱GLM_API_Key",
            category: ["🎨QING", "API配置"],
            type: "text",
            defaultValue: "",
            tooltip: "智谱AI的API密钥，用于GLM语言和视觉模型调用。修改后会实时同步到本地配置文件。",
            attrs: {
                type: "password",
                placeholder: "请输入智谱AI API密钥"
            },
            onChange: (value, oldValue) => {
                // 实时同步到本地配置
                if (window.qingSettingsSync) {
                    window.qingSettingsSync.syncToLocalConfig(value || "");
                }
            }
        }
    ]
});


export { QingSettingsSync };