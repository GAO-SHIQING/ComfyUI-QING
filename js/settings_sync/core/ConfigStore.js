/**
 * 配置状态管理
 * 管理配置的缓存状态
 */

import { getApiKeyMappings } from '../config/api_keys.js';

export class ConfigStore {
    constructor(apiClient) {
        this.api = apiClient;
        this.cache = {}; // 存储API密钥的缓存状态
        this.timestamp = ""; // 存储时间戳
    }
    
    /**
     * 从远程配置提取所有API密钥
     */
    extractApiKeys(remoteConfig) {
        const mappings = getApiKeyMappings();
        const extracted = {};
        
        for (const mapping of mappings) {
            extracted[mapping.configKey] = this.api.extractValue(remoteConfig, mapping.configKey);
        }
        
        return extracted;
    }
    
    /**
     * 更新缓存
     */
    updateCache(remoteConfig) {
        this.cache = this.extractApiKeys(remoteConfig);
        this.timestamp = this.api.extractTimestamp(remoteConfig);
    }
    
    /**
     * 更新单个配置项的缓存
     */
    updateSingleCache(configKey, value) {
        this.cache[configKey] = value;
        this.timestamp = new Date().toISOString();
    }
    
    /**
     * 获取缓存的配置值
     */
    getCachedValue(configKey) {
        return this.cache[configKey] || "";
    }
    
    /**
     * 获取缓存的时间戳
     */
    getCachedTimestamp() {
        return this.timestamp;
    }
    
    /**
     * 清空缓存
     */
    clearCache() {
        this.cache = {};
        this.timestamp = "";
    }
}

