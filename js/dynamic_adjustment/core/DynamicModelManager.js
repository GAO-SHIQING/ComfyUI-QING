/**
 * 动态模型管理器 - 核心逻辑类
 */

import { app } from "../../../scripts/app.js";

export class DynamicModelManager {
    constructor(nodeConfigurations) {
        this.nodeConfigurations = nodeConfigurations;
        this.registeredNodes = new Set();
    }
    
    /**
     * 注册新的节点配置
     * @param {string} nodeName - 节点名称
     * @param {object} config - 节点配置
     */
    registerNode(nodeName, config) {
        this.nodeConfigurations[nodeName] = config;
    }
    
    /**
     * 检查节点是否支持动态模型
     * @param {string} nodeName - 节点名称
     * @returns {boolean}
     */
    isSupported(nodeName) {
        return nodeName in this.nodeConfigurations;
    }
    
    /**
     * 获取节点配置
     * @param {string} nodeName - 节点名称
     * @returns {object|null}
     */
    getNodeConfig(nodeName) {
        return this.nodeConfigurations[nodeName] || null;
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

