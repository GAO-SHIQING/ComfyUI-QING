/**
 * 节点对齐工具 - 事件管理
 */

import { calculateSliceIndex } from '../utils/geometry.js';

export class EventManager {
    constructor(config, ui, onActionTrigger, onUndo) {
        this.config = config;
        this.ui = ui;
        this.onActionTrigger = onActionTrigger;
        this.onUndo = onUndo;
        
        this.isVisible = false;
        this.lastMouseX = 0;
        this.lastMouseY = 0;
        this.currentMouseX = 0;
        this.currentMouseY = 0;
        this.menuMouseMoved = false;
        this.rafId = null;
        
        this.setupEventListeners();
    }
    
    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        this.trackMousePosition();
        this.setupKeyboardShortcuts();
    }
    
    /**
     * 追踪鼠标位置
     */
    trackMousePosition() {
        document.addEventListener('mousemove', (e) => {
            if (this.isVisible) {
                this.currentMouseX = e.clientX;
                this.currentMouseY = e.clientY;
                this.menuMouseMoved = true;
                
                if (this.rafId) {
                    cancelAnimationFrame(this.rafId);
                }
                
                this.rafId = requestAnimationFrame(() => {
                    if (this.isVisible) {
                        this.ui.updateHighlight(this.currentMouseX, this.currentMouseY);
                    }
                    this.rafId = null;
                });
            } else {
                this.lastMouseX = e.clientX;
                this.lastMouseY = e.clientY;
            }
        });
    }
    
    /**
     * 设置键盘快捷键
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // 检查是否启用
            if (this.config.enabled === false) {
                return;
            }
            
            // Ctrl+Z 撤销
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                if (!this.isVisible) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.onUndo();
                    return;
                }
            }
            
            // 打开菜单快捷键
            if (this.matchHotkey(e, this.config.hotkey)) {
                e.preventDefault();
                e.stopPropagation();
                if (!this.isVisible) {
                    this.showMenu();
                }
            }
        }, true);
        
        document.addEventListener('keyup', (e) => {
            // 检查是否启用
            if (this.config.enabled === false) {
                return;
            }
            
            const modifiers = this.config.hotkey.modifiers || [];
            let shouldTrigger = false;
            
            if (modifiers.includes('alt') && e.key === 'Alt') {
                shouldTrigger = true;
            } else if (modifiers.includes('ctrl') && (e.key === 'Control' || e.key === 'Meta')) {
                shouldTrigger = true;
            } else if (modifiers.includes('shift') && e.key === 'Shift') {
                shouldTrigger = true;
            }
            
            if (shouldTrigger && this.isVisible) {
                const sliceIndex = calculateSliceIndex(
                    this.currentMouseX, this.currentMouseY,
                    this.ui.menuCenterX, this.ui.menuCenterY,
                    this.config,
                    this.ui.lastHighlightedSlice
                );
                
                const shouldExecute = sliceIndex >= 0 && this.menuMouseMoved;
                
                this.hideMenu();
                
                if (shouldExecute) {
                    requestAnimationFrame(() => {
                        try {
                            this.onActionTrigger(sliceIndex);
                        } catch (error) {
                            console.error('❌ 节点对齐功能执行失败:', error);
                        }
                    });
                }
            }
        }, true);
    }
    
    /**
     * 匹配快捷键
     */
    matchHotkey(event, hotkey) {
        const keyMatches = event.key.toLowerCase() === hotkey.key.toLowerCase() || 
                          event.code.toLowerCase() === `key${hotkey.key.toLowerCase()}`;
        
        const modifiers = hotkey.modifiers || [];
        const altMatch = modifiers.includes('alt') ? event.altKey : !event.altKey;
        const ctrlMatch = modifiers.includes('ctrl') ? (event.ctrlKey || event.metaKey) : !(event.ctrlKey || event.metaKey);
        const shiftMatch = modifiers.includes('shift') ? event.shiftKey : !event.shiftKey;
        
        return keyMatches && altMatch && ctrlMatch && shiftMatch;
    }
    
    /**
     * 显示菜单
     */
    showMenu() {
        this.currentMouseX = this.lastMouseX;
        this.currentMouseY = this.lastMouseY;
        this.menuMouseMoved = false;
        
        // 通知UI显示菜单（hasSelectedNodes由外部传入）
        if (this.onShowMenu) {
            this.onShowMenu(this.lastMouseX, this.lastMouseY);
        }
        
        this.isVisible = true;
    }
    
    /**
     * 隐藏菜单
     */
    hideMenu() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        
        this.ui.hide();
        this.isVisible = false;
    }
    
    /**
     * 设置菜单显示回调
     */
    setShowMenuCallback(callback) {
        this.onShowMenu = callback;
    }
    
    /**
     * 获取是否可见
     */
    getIsVisible() {
        return this.isVisible;
    }
}

