import { app } from "../../scripts/app.js";
import { DEFAULT_CONFIG, SETTINGS_DEFINITIONS, loadUserSettings } from "./config/settings.js";
import { HistoryManager } from "./core/HistoryManager.js";
import { AlignmentEngine } from "./core/AlignmentEngine.js";
import { RadialMenuUI } from "./core/RadialMenuUI.js";
import { EventManager } from "./core/EventManager.js";
import { validateNodeCount, getSelectedNodes } from "./utils/validators.js";
import { HotkeyCapture } from "./utils/hotkey_input.js";

class AlignNodesMenu {
    constructor() {
        this.config = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
        loadUserSettings(app, this.config);
        
        this.historyManager = new HistoryManager(app, this.config.undo.maxHistorySize);
        this.alignmentEngine = new AlignmentEngine(app);
        
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
        
        this.ui = new RadialMenuUI(this.config, this.actions);
        this.eventManager = new EventManager(
            this.config,
            this.ui,
            (sliceIndex) => this.handleActionTrigger(sliceIndex),
            () => this.handleUndo()
        );
        
        this.eventManager.setShowMenuCallback((x, y) => {
            const selectedNodes = getSelectedNodes(app);
            const hasSelectedNodes = selectedNodes.length > 0;
            this.ui.show(x, y, hasSelectedNodes);
        });
        
        this.historyStack = this.historyManager.historyStack;
        this.maxHistorySize = this.historyManager.maxHistorySize;
    }
    
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
    
    handleActionTrigger(sliceIndex) {
        if (sliceIndex >= 0 && sliceIndex < this.actions.length) {
            const action = this.actions[sliceIndex];
            if (action && action.handler) {
                action.handler();
            }
        }
    }
    
    handleUndo() {
        const result = this.historyManager.undo();
        this.ui.showTempMessage(result.message);
    }
    
    setEnabled(enabled) {
        this.config.enabled = enabled;
    }
    
    updateHotkeyFromDisplay(displayText) {
        const parsed = HotkeyCapture.parseHotkeyDisplay(displayText);
        if (parsed) {
            this.config.hotkey = {
                key: parsed.key,
                modifiers: parsed.modifiers
            };
            
            const hotkeyInput = document.querySelector('input[id*="节点对齐.快捷键"]');
            if (hotkeyInput && hotkeyInput.value !== displayText && document.activeElement !== hotkeyInput) {
                hotkeyInput.removeAttribute('readonly');
                hotkeyInput.value = displayText;
                hotkeyInput.setAttribute('readonly', 'true');
            }
        }
    }
    
    setupHotkeyInput() {
        const waitForInput = (attempt = 0) => {
            if (attempt > 20) return;
            
            const hotkeyInput = document.querySelector('input[placeholder*="点击后按下快捷键"]');
            
            if (!hotkeyInput) {
                setTimeout(() => waitForInput(attempt + 1), 100);
                return;
            }
            
            if (hotkeyInput.dataset.qingBound === 'true') return;
            
            try {
                let currentDisplay = HotkeyCapture.formatHotkeyDisplay(
                    this.config.hotkey.modifiers,
                    this.config.hotkey.key
                );
                
                if (!hotkeyInput.value || hotkeyInput.value === '') {
                    hotkeyInput.value = currentDisplay;
                }
                
                hotkeyInput.dataset.qingBound = 'true';
                let errorTimeoutId = null;
                
                const setInputValue = (value, color = '') => {
                    hotkeyInput.removeAttribute('readonly');
                    hotkeyInput.value = value;
                    hotkeyInput.style.color = color;
                    hotkeyInput.setAttribute('readonly', 'true');
                };
                
                hotkeyInput.addEventListener('focus', () => {
                    if (errorTimeoutId) {
                        clearTimeout(errorTimeoutId);
                        errorTimeoutId = null;
                    }
                    hotkeyInput.dataset.originalValue = hotkeyInput.value;
                    setInputValue('按下快捷键...', '#888');
                });
                
                hotkeyInput.addEventListener('keydown', (e) => {
                    if (errorTimeoutId) {
                        clearTimeout(errorTimeoutId);
                        errorTimeoutId = null;
                    }
                    
                    const captured = HotkeyCapture.captureHotkey(e);
                    
                    if (captured) {
                        setInputValue(captured.display);
                        currentDisplay = captured.display;
                        
                        this.config.hotkey = {
                            key: captured.key,
                            modifiers: captured.modifiers
                        };
                        
                        try {
                            const settingId = '🎨QING.节点对齐.快捷键';
                            if (app.ui?.settings?.setSettingValue) {
                                app.ui.settings.setSettingValue(settingId, captured.display);
                            } else {
                                localStorage.setItem(`Comfy.Settings.${settingId}`, captured.display);
                            }
                        } catch (err) {
                            console.warn('⚠️ 保存快捷键失败:', err);
                        }
                        
                        hotkeyInput.blur();
                    } else {
                        const original = hotkeyInput.dataset.originalValue || currentDisplay;
                        setInputValue('❌ 无效按键', '#f44');
                        errorTimeoutId = setTimeout(() => {
                            setInputValue(original);
                            hotkeyInput.blur();
                            errorTimeoutId = null;
                        }, 800);
                    }
                });
                
                hotkeyInput.addEventListener('blur', () => {
                    const value = hotkeyInput.value;
                    if (value === '按下快捷键...' || value === '❌ 无效按键' || value === '') {
                        setInputValue(hotkeyInput.dataset.originalValue || currentDisplay);
                    }
                });
            } catch (error) {
                console.error('❌ 快捷键输入设置失败:', error);
            }
        };
        
        waitForInput();
    }
}

window.QINGAlignMenu = null;

app.registerExtension({
    name: "🎨QING.AlignNodes",
    async setup() {
        try {
            const alignMenu = new AlignNodesMenu();
            window.QINGAlignMenu = alignMenu;
            
            console.log("✅ 节点对齐工具加载成功");
            
            // 使用 MutationObserver 监听快捷键输入框出现
            let lastCheckTime = 0;
            let observerActive = true;
            let removalObserver = null;
            
            const observer = new MutationObserver(() => {
                if (!observerActive) return;
                
                const now = Date.now();
                if (now - lastCheckTime < 500) return;
                lastCheckTime = now;
                
                const hotkeyInput = document.querySelector('input[placeholder*="点击后按下快捷键"]');
                if (hotkeyInput && !hotkeyInput.dataset.qingBound) {
                    alignMenu.setupHotkeyInput();
                    
                    setTimeout(() => {
                        if (hotkeyInput.dataset.qingBound === 'true') {
                            observerActive = false;
                            
                            if (removalObserver) {
                                removalObserver.disconnect();
                            }
                            
                            removalObserver = new MutationObserver((mutations) => {
                                for (const mutation of mutations) {
                                    if (mutation.removedNodes) {
                                        for (const node of mutation.removedNodes) {
                                            if (node === hotkeyInput || node.contains?.(hotkeyInput)) {
                                                observerActive = true;
                                                removalObserver.disconnect();
                                                removalObserver = null;
                                                break;
                                            }
                                        }
                                    }
                                }
                            });
                            
                            removalObserver.observe(document.body, {
                                childList: true,
                                subtree: true
                            });
                        }
                    }, 300);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        } catch (error) {
            console.error("❌ 节点对齐工具加载失败:", error);
        }
    },
    settings: SETTINGS_DEFINITIONS
});
