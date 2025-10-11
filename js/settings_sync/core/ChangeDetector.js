/**
 * 变更检测器
 * 检测配置是否发生变更
 */

import { getApiKeyMappings } from '../config/api_keys.js';

export class ChangeDetector {
    constructor(configStore, apiClient) {
        this.store = configStore;
        this.api = apiClient;
    }
    
    /**
     * 检测配置是否有变更
     */
    hasChanged(remoteConfig) {
        const remoteTimestamp = this.api.extractTimestamp(remoteConfig);
        const cachedTimestamp = this.store.getCachedTimestamp();
        
        // 首先检查时间戳
        if (remoteTimestamp !== cachedTimestamp) {
            return true;
        }
        
        // 然后逐一比较每个API密钥
        const mappings = getApiKeyMappings();
        
        for (const mapping of mappings) {
            const remoteValue = this.api.extractValue(remoteConfig, mapping.configKey);
            const cachedValue = this.store.getCachedValue(mapping.configKey);
            
            if (remoteValue !== cachedValue) {
                return true;
            }
        }
        
        return false;
    }
    
    /**
     * 获取所有变更的配置项
     */
    getChangedKeys(remoteConfig) {
        const changed = [];
        const mappings = getApiKeyMappings();
        
        for (const mapping of mappings) {
            const remoteValue = this.api.extractValue(remoteConfig, mapping.configKey);
            const cachedValue = this.store.getCachedValue(mapping.configKey);
            
            if (remoteValue !== cachedValue) {
                changed.push({
                    configKey: mapping.configKey,
                    settingId: mapping.settingId,
                    oldValue: cachedValue,
                    newValue: remoteValue
                });
            }
        }
        
        return changed;
    }
}

