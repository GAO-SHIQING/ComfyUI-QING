/**
 * Dynamic Adjustment - 动态调整组件
 * 支持多个API节点的动态模型切换
 * 可扩展支持任意数量的不同API节点
 */

import { app } from "../../scripts/app.js";

// 节点配置注册表
const NODE_CONFIGURATIONS = {
    // Kimi Language API节点配置
    "KimiLanguageAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "月之暗面": ["kimi-k2-0905", "kimi-k2-0711", "kimi-k2-turbo"],
            "火山引擎": ["kimi-k2-0905"],
            "阿里云百炼": ["kimi-k2-0905"], 
            "硅基流动": ["kimi-k2-0905"]
        },
        defaultModel: {
            "月之暗面": "kimi-k2-0905",
            "火山引擎": "kimi-k2-0905",
            "阿里云百炼": "kimi-k2-0905",
            "硅基流动": "kimi-k2-0905"
        }
    },
    
    // Kimi Vision API节点配置
    "KimiVisionAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "月之暗面": ["kimi-latest-8k", "kimi-latest-32k", "kimi-latest-128k"]
        },
        defaultModel: {
            "月之暗面": "kimi-latest-32k"
        }
    },
    
    // Doubao Vision API节点配置
    "DoubaoVisionAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "火山引擎": [
                "Doubao-Seed-1.6", 
                "Doubao-Seed-1.6-thinking", 
                "Doubao-Seed-1.6-flash", 
                "Doubao-Seed-1.6-vision", 
                "Doubao-1.5-vision-pro", 
                "Doubao-1.5-vision-lite", 
                "Doubao-1.5-thinking-vision-pro",
                "Doubao-1.5-UI-TARS",
                "Doubao-Seed-Translation"
            ]
        },
        defaultModel: {
            "火山引擎": "Doubao-1.5-vision-pro"
        }
    },
    
    // DeepSeek Language API节点配置
    "DeepSeekLanguageAPI": {
        platformWidget: "platform",
        modelWidget: "model",
        platformModels: {
            "火山引擎": ["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            "阿里云百炼": ["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            "硅基流动": ["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            "腾讯云": ["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"]
        },
        defaultModel: {
            "火山引擎": "DeepSeek-V3.1",
            "阿里云百炼": "DeepSeek-V3.1",
            "硅基流动": "DeepSeek-V3.1",
            "腾讯云": "DeepSeek-V3.1"
        }
    },
    
    // "AnotherAPINode": {
    //     platformWidget: "service_provider",
    //     modelWidget: "ai_model",
    //     platformModels: {
    //         "OpenAI": ["gpt-4", "gpt-3.5-turbo"],
    //         "Anthropic": ["claude-3"],
    //         // ...
    //     },
    //     defaultModel: {
    //         "OpenAI": "gpt-4",
    //         "Anthropic": "claude-3",
    //         // ...
    //     }
    // }
};

/**
 * 通用动态模型处理器
 */
class UniversalDynamicModels {
    constructor() {
        this.registeredNodes = new Set();
    }
    
    /**
     * 注册新的节点配置
     * @param {string} nodeName - 节点名称
     * @param {object} config - 节点配置
     */
    registerNode(nodeName, config) {
        NODE_CONFIGURATIONS[nodeName] = config;
        // console.log(`🎨QING: 注册动态模型支持 - ${nodeName}`);
    }
    
    /**
     * 检查节点是否支持动态模型
     * @param {string} nodeName - 节点名称
     * @returns {boolean}
     */
    isSupported(nodeName) {
        return nodeName in NODE_CONFIGURATIONS;
    }
    
    /**
     * 获取节点配置
     * @param {string} nodeName - 节点名称
     * @returns {object|null}
     */
    getNodeConfig(nodeName) {
        return NODE_CONFIGURATIONS[nodeName] || null;
    }
    
    /**
     * 为节点设置动态模型功能
     * @param {object} node - ComfyUI节点实例
     * @param {object} config - 节点配置
     */
    setupDynamicModels(node, config) {
        const platformWidget = node.widgets?.find(w => w.name === config.platformWidget);
        const modelWidget = node.widgets?.find(w => w.name === config.modelWidget);
        
        if (!platformWidget || !modelWidget) {
            return false;
        }
        
        // 初始化时设置模型列表
        const initialPlatform = platformWidget.value || Object.keys(config.platformModels)[0];
        this.updateModelOptions(node, modelWidget, initialPlatform, config);
        
        // 保存原始回调
        const originalPlatformCallback = platformWidget.callback;
        
        // 设置平台切换回调
        platformWidget.callback = (value, widget, node, pos, event) => {
            // 调用原始回调
            if (originalPlatformCallback) {
                originalPlatformCallback.call(this, value, widget, node, pos, event);
            }
            
            // 延迟执行模型更新，确保DOM已准备好
            setTimeout(() => {
                // 更新模型选项
                this.updateModelOptions(node, modelWidget, value, config);
                
                // 强制重绘节点
                if (node.onResize) {
                    node.onResize();
                }
                
                // 强制重新计算节点大小
                if (node.computeSize) {
                    node.computeSize();
                }
                
                // 强制标记画布为dirty
                if (app.graph) {
                    app.graph.setDirtyCanvas(true, true);
                }
                
                // 强制重绘整个应用
                if (app.canvas) {
                    app.canvas.draw(true, true);
                }
            }, 10);
        };
        
        return true;
    }
    
    /**
     * 更新模型选项
     * @param {object} node - 节点实例
     * @param {object} modelWidget - 模型widget
     * @param {string} platform - 选择的平台
     * @param {object} config - 节点配置
     */
    updateModelOptions(node, modelWidget, platform, config) {
        const availableModels = config.platformModels[platform] || [];
        const defaultModel = config.defaultModel[platform] || (availableModels[0] || "");
        
        // 确保模型列表存在且不为空
        if (!modelWidget || !modelWidget.options || availableModels.length === 0) {
            return;
        }
        
        const currentValue = modelWidget.value;
        
        // 强制更新可选值列表
        modelWidget.options.values = [...availableModels]; // 创建新数组避免引用问题
        
        // 触发ComfyUI的widget更新机制
        if (modelWidget.computeSize) {
            modelWidget.computeSize();
        }
        
        // 智能选择模型
        if (!availableModels.includes(currentValue)) {
            modelWidget.value = defaultModel;
            
            // 触发模型widget回调
            if (modelWidget.callback) {
                modelWidget.callback(modelWidget.value, modelWidget, node, null, null);
            }
        }
        
        // 强制界面更新
        if (modelWidget.element) {
            // 如果是select元素，更新选项
            if (modelWidget.element.tagName === 'SELECT') {
                modelWidget.element.innerHTML = '';
                availableModels.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    option.selected = model === modelWidget.value;
                    modelWidget.element.appendChild(option);
                });
            }
        }
    }
}

// 创建全局实例
const universalDynamicModels = new UniversalDynamicModels();

// 注册ComfyUI扩展
app.registerExtension({
    name: "🎨QING.DynamicAdjustment",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 检查是否支持该节点
        if (!universalDynamicModels.isSupported(nodeData.name)) {
            return;
        }
        
        const config = universalDynamicModels.getNodeConfig(nodeData.name);
        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        
        nodeType.prototype.onNodeCreated = function() {
            // 调用原始方法
            if (originalOnNodeCreated) {
                originalOnNodeCreated.apply(this, arguments);
            }
            
            // 设置动态模型功能
            universalDynamicModels.setupDynamicModels(this, config);
        };
    }
});

// 导出接口供其他模块使用
window.QINGDynamicAdjustment = {
    /**
     * 注册新节点的动态模型支持
     * @param {string} nodeName - 节点名称
     * @param {object} config - 配置对象
     * @param {string} config.platformWidget - 平台选择widget名称
     * @param {string} config.modelWidget - 模型选择widget名称  
     * @param {object} config.platformModels - 平台模型映射
     * @param {object} config.defaultModel - 默认模型映射
     */
    registerNode: (nodeName, config) => {
        universalDynamicModels.registerNode(nodeName, config);
    },
    
    /**
     * 检查节点是否已支持
     * @param {string} nodeName - 节点名称
     * @returns {boolean}
     */
    isSupported: (nodeName) => {
        return universalDynamicModels.isSupported(nodeName);
    },
    
    /**
     * 获取所有支持的节点列表
     * @returns {string[]}
     */
    getSupportedNodes: () => {
        return Object.keys(NODE_CONFIGURATIONS);
    }
};
