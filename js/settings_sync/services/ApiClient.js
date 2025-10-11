/**
 * API客户端 - HTTP请求封装
 * 负责所有与后端API的通信
 */

export class ApiClient {
    constructor(endpoint = "/api/qing/config") {
        this.endpoint = endpoint;
    }
    
    /**
     * 获取配置
     */
    async getConfig() {
        try {
            const response = await fetch(this.endpoint, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                return await response.json();
            }
            
            return null;
        } catch (error) {
            // 静默处理错误
            return null;
        }
    }
    
    /**
     * 更新API密钥
     */
    async updateApiKey(apiKey, configKey) {
        try {
            const response = await fetch(this.endpoint, {
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
                return await response.json();
            }
            
            return null;
        } catch (error) {
            // 静默处理错误
            return null;
        }
    }
    
    /**
     * 提取配置中的时间戳
     */
    extractTimestamp(config) {
        return config?.api_settings?.last_updated || "";
    }
    
    /**
     * 提取配置中的API密钥值
     */
    extractValue(config, configKey) {
        const localSetting = config?.api_settings?.[configKey];
        
        if (typeof localSetting === 'object' && localSetting !== null) {
            return localSetting.value || "";
        } else if (typeof localSetting === 'string') {
            return localSetting;
        }
        
        return "";
    }
}

