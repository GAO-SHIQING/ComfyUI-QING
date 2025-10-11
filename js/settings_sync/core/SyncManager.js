/**
 * 同步管理器
 * 协调配置同步的核心逻辑
 */

import { getApiKeyMappings } from '../config/api_keys.js';

export class SyncManager {
    constructor(app, apiClient, configStore, changeDetector, timerService) {
        this.app = app;
        this.api = apiClient;
        this.store = configStore;
        this.detector = changeDetector;
        this.timer = timerService;
        this.isSyncing = false; // 防止同步冲突
    }
    
    /**
     * 初始化同步
     */
    async initialize() {
        // 延迟初始化，确保ComfyUI设置系统已加载
        setTimeout(async () => {
            await this.performInitialSync();
            this.startPeriodicSync();
        }, 2000);
    }
    
    /**
     * 执行初始同步
     */
    async performInitialSync() {
        try {
            const remoteConfig = await this.api.getConfig();
            
            if (remoteConfig) {
                // 初始化缓存
                this.store.updateCache(remoteConfig);
                
                // 从远程配置同步到ComfyUI设置
                await this.syncFromRemote(remoteConfig, true);
            } else {
                // 无法获取远程配置，尝试将ComfyUI设置同步到远程
                const firstMapping = getApiKeyMappings()[0];
                const localValue = this.app.extensionManager.setting.get(firstMapping.settingId) || "";
                
                if (localValue) {
                    await this.syncToRemote(localValue, firstMapping.configKey);
                }
            }
        } catch (error) {
            console.error("❌ 初始同步失败:", error);
        }
    }
    
    /**
     * 从远程同步到ComfyUI设置
     */
    async syncFromRemote(remoteConfig, forceSync = false) {
        if (this.isSyncing && !forceSync) {
            return;
        }
        
        try {
            this.isSyncing = true;
            
            const mappings = getApiKeyMappings();
            let hasUpdates = false;
            
            for (const mapping of mappings) {
                const remoteValue = this.api.extractValue(remoteConfig, mapping.configKey);
                const currentValue = this.app.extensionManager.setting.get(mapping.settingId) || "";
                
                // 只有当值真的不同时才更新
                if (remoteValue !== currentValue) {
                    this.app.extensionManager.setting.set(mapping.settingId, remoteValue, false);
                    hasUpdates = true;
                }
            }
            
            if (hasUpdates || forceSync) {
                // 更新缓存
                this.store.updateCache(remoteConfig);
                // 重置检查计数
                this.timer.resetCheckCount();
            } else {
                // 增加检查计数
                this.timer.incrementCheckCount();
            }
            
        } finally {
            // 延迟重置同步标志
            setTimeout(() => {
                this.isSyncing = false;
            }, 100);
        }
    }
    
    /**
     * 从ComfyUI设置同步到远程
     */
    async syncToRemote(apiKey, configKey) {
        if (this.isSyncing) {
            return;
        }
        
        try {
            this.isSyncing = true;
            
            const result = await this.api.updateApiKey(apiKey, configKey);
            
            if (result) {
                // 更新单个配置项的缓存
                this.store.updateSingleCache(configKey, apiKey);
            }
            
        } finally {
            this.isSyncing = false;
        }
    }
    
    /**
     * 定期检查并同步
     */
    async periodicSync() {
        if (this.isSyncing) {
            return;
        }
        
        try {
            const remoteConfig = await this.api.getConfig();
            
            if (remoteConfig && this.detector.hasChanged(remoteConfig)) {
                await this.syncFromRemote(remoteConfig);
            } else if (remoteConfig) {
                // 无变更，增加检查计数
                this.timer.incrementCheckCount();
            }
        } catch (error) {
            // 静默处理错误
            this.timer.incrementCheckCount();
        }
    }
    
    /**
     * 启动定期同步
     */
    startPeriodicSync() {
        this.timer.start(() => {
            this.periodicSync();
        });
    }
    
    /**
     * 停止同步
     */
    stopSync() {
        this.timer.stop();
    }
    
    /**
     * 获取是否正在同步
     */
    getIsSyncing() {
        return this.isSyncing;
    }
}

