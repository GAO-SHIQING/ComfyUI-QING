/**
 * Align Nodes - 节点对齐工具（重构版）
 * 快捷键: Alt+A（可配置）
 */

import { app } from "../../scripts/app.js";
import { DEFAULT_CONFIG, SETTINGS_DEFINITIONS, loadUserSettings } from "./config/settings.js";
import { HistoryManager } from "./core/HistoryManager.js";
import { AlignmentEngine } from "./core/AlignmentEngine.js";
import { RadialMenuUI } from "./core/RadialMenuUI.js";
import { EventManager } from "./core/EventManager.js";
import { validateNodeCount, getSelectedNodes } from "./utils/validators.js";

class AlignNodesMenu {
    constructor() {
        // 深拷贝默认配置
        this.config = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
        
        // 加载用户设置
        loadUserSettings(app, this.config);
        
        // 初始化各个管理器
        this.historyManager = new HistoryManager(app, this.config.undo.maxHistorySize);
        this.alignmentEngine = new AlignmentEngine(app);
        
        // 定义动作列表
        this.actions = [
            { name: '上对齐', handler: () => this.executeAlignment('alignTop', 1), color: 'primary' },
            { name: '上下拉伸', handler: () => this.executeAlignment('stretchVertical', 2), color: 'secondary' },
            { name: '右对齐', handler: () => this.executeAlignment('alignRight', 1), color: 'primary' },
            { name: '垂直居中', handler: () => this.executeAlignment('verticalCenter', 1), color: 'secondary' },
            { name: '下对齐', handler: () => this.executeAlignment('alignBottom', 1), color: 'primary' },
            { name: '垂直分布', handler: () => this.executeAlignment('distributeVertical', 3), color: 'primary' },
            { name: '水平居中', handler: () => this.executeAlignment('horizontalCenter', 1), color: 'secondary' },
            { name: '左对齐', handler: () => this.executeAlignment('alignLeft', 1), color: 'primary' },
            { name: '左右拉伸', handler: () => this.executeAlignment('stretchHorizontal', 2), color: 'secondary' },
            { name: '水平分布', handler: () => this.executeAlignment('distributeHorizontal', 3), color: 'primary' }
        ];
        
        // 初始化UI
        this.ui = new RadialMenuUI(this.config, this.actions);
        
        // 初始化事件管理器
        this.eventManager = new EventManager(
            this.config,
            this.ui,
            (sliceIndex) => this.handleActionTrigger(sliceIndex),
            () => this.handleUndo()
        );
        
        // 设置菜单显示回调
        this.eventManager.setShowMenuCallback((x, y) => {
            const selectedNodes = getSelectedNodes(app);
            const hasSelectedNodes = selectedNodes.length > 0;
            this.ui.show(x, y, hasSelectedNodes);
        });
        
        // 暴露历史管理器给外部（用于设置更新）
        this.historyStack = this.historyManager.historyStack;
        this.maxHistorySize = this.historyManager.maxHistorySize;
    }
    
    /**
     * 执行对齐操作
     */
    executeAlignment(methodName, minCount) {
        const nodes = getSelectedNodes(app);
        const actionName = this.actions.find(a => a.handler.toString().includes(methodName))?.name || methodName;
        
        if (!validateNodeCount(nodes, minCount, actionName, (msg) => this.ui.showTempMessage(msg))) {
            return;
        }
        
        // 保存历史
        this.historyManager.saveNodesState(nodes, actionName);
        
        // 执行对齐
        this.alignmentEngine[methodName](nodes);
    }
    
    /**
     * 处理动作触发
     */
    handleActionTrigger(sliceIndex) {
        if (sliceIndex >= 0 && sliceIndex < this.actions.length) {
            const action = this.actions[sliceIndex];
                    if (action && action.handler) {
                                action.handler();
            }
        }
    }
    
    /**
     * 处理撤销
     */
    handleUndo() {
        const result = this.historyManager.undo();
        this.ui.showTempMessage(result.message);
    }
}

// 全局引用，供设置onChange使用
window.QINGAlignMenu = null;

app.registerExtension({
    name: "🎨QING.AlignNodes",
    async setup() {
        try {
            const alignMenu = new AlignNodesMenu();
            window.QINGAlignMenu = alignMenu;
            console.log("✅ 节点对齐工具加载成功（重构版）");
        } catch (error) {
            console.error("❌ 节点对齐工具加载失败:", error);
        }
    },
    settings: SETTINGS_DEFINITIONS
});
