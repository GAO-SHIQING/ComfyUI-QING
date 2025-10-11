/**
 * Dynamic Adjustment - 动态调整组件
 * 主入口文件 - 协调所有模块
 */

import { app } from "../../scripts/app.js";
import { DynamicModelManager } from './core/DynamicModelManager.js';
import { buildNodeConfigurations, getSupportedNodes } from './utils/registry.js';

// 构建节点配置
const NODE_CONFIGURATIONS = buildNodeConfigurations();

// 创建动态模型管理器实例
const dynamicModelManager = new DynamicModelManager(NODE_CONFIGURATIONS);

// 注册ComfyUI扩展
app.registerExtension({
    name: "🎨QING.DynamicAdjustment",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 检查是否支持该节点
        if (!dynamicModelManager.isSupported(nodeData.name)) {
            return;
        }
        
        const config = dynamicModelManager.getNodeConfig(nodeData.name);
        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        
        nodeType.prototype.onNodeCreated = function() {
            // 调用原始方法
            if (originalOnNodeCreated) {
                originalOnNodeCreated.apply(this, arguments);
            }
            
            // 设置动态模型功能
            dynamicModelManager.setupDynamicModels(this, config);
        };
    }
});

// 导出全局接口供其他模块使用
export const QINGDynamicAdjustment = {
    /**
     * 注册新节点的动态模型支持
     * @param {string} nodeName - 节点名称
     * @param {object} config - 配置对象
     */
    registerNode: (nodeName, config) => {
        dynamicModelManager.registerNode(nodeName, config);
    },
    
    /**
     * 检查节点是否已支持
     * @param {string} nodeName - 节点名称
     * @returns {boolean}
     */
    isSupported: (nodeName) => {
        return dynamicModelManager.isSupported(nodeName);
    },
    
    /**
     * 获取所有支持的节点列表
     * @returns {string[]}
     */
    getSupportedNodes: () => {
        return getSupportedNodes(NODE_CONFIGURATIONS);
    }
};

// 挂载到window对象（保持向后兼容）
window.QINGDynamicAdjustment = QINGDynamicAdjustment;

