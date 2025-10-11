/**
 * 节点对齐工具 - 历史记录管理
 */

export class HistoryManager {
    constructor(app, maxHistorySize = 20) {
        this.app = app;
        this.historyStack = [];
        this.maxHistorySize = maxHistorySize;
    }
    
    /**
     * 保存节点状态到历史记录
     */
    saveNodesState(nodes, actionName) {
        if (!nodes || nodes.length === 0) return;
        
        const snapshot = {
            actionName: actionName,
            timestamp: Date.now(),
            nodes: nodes.filter(node => node && node.pos && node.size).map(node => ({
                id: node.id,
                pos: [...node.pos],
                size: [...node.size]
            }))
        };
        
        this.historyStack.push(snapshot);
        
        if (this.historyStack.length > this.maxHistorySize) {
            this.historyStack.shift();
        }
    }
    
    /**
     * 撤销上一次操作
     */
    undo() {
        if (this.historyStack.length === 0) {
            return { success: false, message: '没有可撤销的操作' };
        }
        
        const snapshot = this.historyStack.pop();
        
        let restoredCount = 0;
        for (const nodeData of snapshot.nodes) {
            const node = this.app.graph.getNodeById(nodeData.id);
            if (node && node.pos && node.size && 
                nodeData.pos && nodeData.pos.length >= 2 &&
                nodeData.size && nodeData.size.length >= 2) {
                node.pos[0] = nodeData.pos[0];
                node.pos[1] = nodeData.pos[1];
                node.size[0] = nodeData.size[0];
                node.size[1] = nodeData.size[1];
                restoredCount++;
            }
        }
        
        if (restoredCount > 0) {
            this.app.graph.setDirtyCanvas(true, true);
            return { 
                success: true, 
                message: `已撤销：${snapshot.actionName} (${restoredCount}个节点)` 
            };
        } else {
            return { success: false, message: '撤销失败：节点不存在' };
        }
    }
    
    /**
     * 清空历史记录
     */
    clearHistory() {
        this.historyStack = [];
    }
    
    /**
     * 更新最大历史记录数量
     */
    setMaxHistorySize(newSize) {
        this.maxHistorySize = newSize;
        while (this.historyStack.length > newSize) {
            this.historyStack.shift();
        }
    }
    
    /**
     * 获取历史记录数量
     */
    getHistoryCount() {
        return this.historyStack.length;
    }
}

