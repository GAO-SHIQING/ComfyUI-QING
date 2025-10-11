/**
 * 定时器服务
 * 管理同步定时器和自适应间隔
 */

export class TimerService {
    constructor() {
        this.syncInterval = null;
        this.reevaluateInterval = null;
        this.checkCount = 0; // 用于智能调节检查频率
        this.baseInterval = 2000; // 基础间隔2秒
        this.maxInterval = 10000; // 最大间隔10秒
        this.increaseStep = 1000; // 每次增加1秒
    }
    
    /**
     * 启动定期同步
     */
    start(syncCallback) {
        this.stop(); // 先停止已有的定时器
        
        // 启动主同步定时器
        this.syncInterval = setInterval(() => {
            syncCallback();
        }, this.getAdaptiveInterval());
        
        // 定期重新评估检查间隔（每30秒）
        this.reevaluateInterval = setInterval(() => {
            this.reevaluate(syncCallback);
        }, 30000);
    }
    
    /**
     * 停止定时器
     */
    stop() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
        
        if (this.reevaluateInterval) {
            clearInterval(this.reevaluateInterval);
            this.reevaluateInterval = null;
        }
    }
    
    /**
     * 重新评估并调整间隔
     */
    reevaluate(syncCallback) {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = setInterval(() => {
                syncCallback();
            }, this.getAdaptiveInterval());
        }
    }
    
    /**
     * 获取自适应检查间隔
     */
    getAdaptiveInterval() {
        // 基础间隔2秒，如果长时间无变更，逐渐增加到最大10秒
        const adaptiveInterval = Math.min(
            this.baseInterval + (Math.floor(this.checkCount / 10) * this.increaseStep),
            this.maxInterval
        );
        
        return adaptiveInterval;
    }
    
    /**
     * 增加检查计数（无变更时调用）
     */
    incrementCheckCount() {
        this.checkCount++;
    }
    
    /**
     * 重置检查计数（发现变更时调用）
     */
    resetCheckCount() {
        this.checkCount = 0;
    }
    
    /**
     * 获取当前检查计数
     */
    getCheckCount() {
        return this.checkCount;
    }
}

