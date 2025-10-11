/**
 * 🎨QING设置同步模块（重构版）
 * 实现ComfyUI设置与本地配置文件的双向同步
 * 
 * 架构：
 * - config/api_keys.js: API Key配置中心
 * - services/ApiClient.js: HTTP请求封装
 * - core/ConfigStore.js: 配置状态管理
 * - core/ChangeDetector.js: 变更检测
 * - services/TimerService.js: 定时器管理
 * - core/SyncManager.js: 同步管理器
 */

import { app } from "../../../scripts/app.js";
import { generateSettingsDefinitions } from "./config/api_keys.js";
import { ApiClient } from "./services/ApiClient.js";
import { ConfigStore } from "./core/ConfigStore.js";
import { ChangeDetector } from "./core/ChangeDetector.js";
import { TimerService } from "./services/TimerService.js";
import { SyncManager } from "./core/SyncManager.js";

/**
 * 设置同步类（简化版）
 * 只提供对外接口，内部逻辑由各个模块负责
 */
class QingSettingsSync {
    constructor() {
        // 初始化各个模块
        this.apiClient = new ApiClient("/api/qing/config");
        this.configStore = new ConfigStore(this.apiClient);
        this.changeDetector = new ChangeDetector(this.configStore, this.apiClient);
        this.timerService = new TimerService();
        this.syncManager = new SyncManager(
            app,
            this.apiClient,
            this.configStore,
            this.changeDetector,
            this.timerService
        );
        
        // 启动同步
        this.syncManager.initialize();
    }
    
    /**
     * 同步到本地配置文件
     * （提供给settings onChange使用）
     */
    async syncToLocalConfig(apiKey, configKey) {
        if (!this.syncManager.getIsSyncing()) {
            await this.syncManager.syncToRemote(apiKey, configKey);
        }
    }
    
    /**
     * 停止同步
     */
    stopSync() {
        this.syncManager.stopSync();
    }
    
    /**
     * 获取是否正在同步
     */
    get isSyncing() {
        return this.syncManager.getIsSyncing();
    }
}

// 创建全局实例
window.qingSettingsSync = new QingSettingsSync();

// 注册ComfyUI扩展
app.registerExtension({
    name: "🎨QING.API配置",
    async setup() {
        // Extension setup code
        console.log("✅ 🎨QING API配置同步模块加载成功（重构版）");
    },
    settings: generateSettingsDefinitions((newVal, configKey) => {
        // onChange回调
        if (window.qingSettingsSync && !window.qingSettingsSync.isSyncing) {
            window.qingSettingsSync.syncToLocalConfig(newVal, configKey);
        }
    })
});

// 导出类供其他模块使用
export { QingSettingsSync };

