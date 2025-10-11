/**
 * Align Nodes - 节点对齐工具
 * 快捷键: Alt+A
 * 
 * 这是原始版本的备份文件
 */

import { app } from "../../scripts/app.js";

class AlignNodesMenu {
    constructor() {
        this.menuElement = null;
        this.isVisible = false;
        this.lastMouseX = 0;
        this.lastMouseY = 0;
        this.menuCenterX = 0;
        this.menuCenterY = 0;
        this.lastHighlightedSlice = -1;
        this.rafId = null;
        this.currentMouseX = 0;
        this.currentMouseY = 0;
        this.sliceElements = [];
        this.currentMessageElement = null;
        this.messageTimeout = null;
        this.hasSelectedNodes = false;
        this.menuMouseMoved = false;
        
        this.historyStack = [];
        this.maxHistorySize = 20;
        
        this.config = {
            outerRadius: 160,
            innerRadius: 72,
            sliceCount: 10,
            colors: {
                primary: 'rgba(80, 80, 80, 0.75)',
                secondary: 'rgba(26, 68, 46, 0.75)'
            },
            animation: {
                fadeIn: 450,
                fadeOut: 350,
                popup: 600
            },
            uiOffsets: {
                innerThreshold: 10,
                tooltipOffsetX: 15,
                fadeDelay: 10,
                messageDuration: 2000,
                messageFadeOut: 300,
                angleTolerance: 3
            },
            undo: {
                enabled: true,
                maxHistorySize: 20
            },
            hotkey: {
                key: 'a',
                modifiers: ['alt']
            }
        };
        
        this.loadUserSettings();
        
        this.actions = [];
        this.init();
    }
    
    loadUserSettings() {
        try {
            if (!app.extensionManager?.setting) return;
            
            const outerRadius = app.extensionManager.setting.get('🎨QING.节点对齐.外圈半径');
            if (outerRadius !== undefined) this.config.outerRadius = outerRadius;
            
            const innerRadius = app.extensionManager.setting.get('🎨QING.节点对齐.内圈半径');
            if (innerRadius !== undefined) this.config.innerRadius = innerRadius;
            
            const primaryColor = app.extensionManager.setting.get('🎨QING.节点对齐.主色调');
            if (primaryColor && /^[0-9a-fA-F]{6}$/.test(primaryColor)) {
                const alpha = 0.75;
                const r = parseInt(primaryColor.substring(0, 2), 16);
                const g = parseInt(primaryColor.substring(2, 4), 16);
                const b = parseInt(primaryColor.substring(4, 6), 16);
                this.config.colors.primary = `rgba(${r}, ${g}, ${b}, ${alpha})`;
            }
            
            const secondaryColor = app.extensionManager.setting.get('🎨QING.节点对齐.次色调');
            if (secondaryColor && /^[0-9a-fA-F]{6}$/.test(secondaryColor)) {
                const alpha = 0.75;
                const r = parseInt(secondaryColor.substring(0, 2), 16);
                const g = parseInt(secondaryColor.substring(2, 4), 16);
                const b = parseInt(secondaryColor.substring(4, 6), 16);
                this.config.colors.secondary = `rgba(${r}, ${g}, ${b}, ${alpha})`;
            }
            
            const animationSpeed = app.extensionManager.setting.get('🎨QING.节点对齐.动画速度');
            const speeds = {
                "快速": { fadeIn: 200, fadeOut: 150, popup: 250 },
                "标准": { fadeIn: 450, fadeOut: 350, popup: 600 },
                "慢速": { fadeIn: 600, fadeOut: 450, popup: 800 }
            };
            if (animationSpeed && speeds[animationSpeed]) {
                Object.assign(this.config.animation, speeds[animationSpeed]);
            }
            
            const tooltipOffset = app.extensionManager.setting.get('🎨QING.节点对齐.Tooltip偏移');
            if (tooltipOffset !== undefined) this.config.uiOffsets.tooltipOffsetX = tooltipOffset;
            
            const messageDuration = app.extensionManager.setting.get('🎨QING.节点对齐.消息持续时间');
            if (messageDuration !== undefined) this.config.uiOffsets.messageDuration = messageDuration;
            
            const maxHistory = app.extensionManager.setting.get('🎨QING.节点对齐.撤回历史记录');
            if (maxHistory !== undefined) {
                this.config.undo.maxHistorySize = maxHistory;
                this.maxHistorySize = maxHistory;
            }
            
            const hotkeyConfig = app.extensionManager.setting.get('🎨QING.节点对齐.快捷键');
            if (hotkeyConfig) {
                try {
                    this.config.hotkey = JSON.parse(hotkeyConfig);
                } catch (e) {
                    console.warn('快捷键配置解析失败:', e);
                }
            }
            
        } catch (error) {
            console.warn('⚠️ 节点对齐设置加载失败，使用默认值:', error);
        }
    }
    
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
    
    undo() {
        if (this.historyStack.length === 0) {
            this.showTempMessage('没有可撤销的操作');
            return false;
        }
        
        const snapshot = this.historyStack.pop();
        
        let restoredCount = 0;
        for (const nodeData of snapshot.nodes) {
            const node = app.graph.getNodeById(nodeData.id);
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
            app.graph.setDirtyCanvas(true, true);
            this.showTempMessage(`已撤销：${snapshot.actionName} (${restoredCount}个节点)`);
            return true;
        } else {
            this.showTempMessage('撤销失败：节点不存在');
            return false;
        }
    }
    
    clearHistory() {
        this.historyStack = [];
    }
    
    init() {
        this.actions = [
            { name: '上对齐', handler: () => this.alignTop(), color: 'primary' },
            { name: '上下拉伸', handler: () => this.stretchVertical(), color: 'secondary' },
            { name: '右对齐', handler: () => this.alignRight(), color: 'primary' },
            { name: '垂直居中', handler: () => this.verticalCenter(), color: 'secondary' },
            { name: '下对齐', handler: () => this.alignBottom(), color: 'primary' },
            { name: '垂直分布', handler: () => this.distributeVertical(), color: 'primary' },
            { name: '水平居中', handler: () => this.horizontalCenter(), color: 'secondary' },
            { name: '左对齐', handler: () => this.alignLeft(), color: 'primary' },
            { name: '左右拉伸', handler: () => this.stretchHorizontal(), color: 'secondary' },
            { name: '水平分布', handler: () => this.distributeHorizontal(), color: 'primary' }
        ];
        
        this.createMenuElement();
        this.setupKeyboardShortcuts();
        this.trackMousePosition();
    }
    
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
                            this.updateHighlightByDirection(this.currentMouseX, this.currentMouseY);
                        }
                    this.rafId = null;
                    });
            } else {
                this.lastMouseX = e.clientX;
                this.lastMouseY = e.clientY;
            }
        });
    }
    
    calculateSliceIndex(mouseX, mouseY) {
        const dx = mouseX - this.menuCenterX;
        const dy = mouseY - this.menuCenterY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        const innerThreshold = this.config.innerRadius + this.config.uiOffsets.innerThreshold;
        if (distance < innerThreshold) {
            return -1;
        }
        
        const angleRad = Math.atan2(dy, dx);
        
        let angleDeg = angleRad * 180 / Math.PI;
        if (angleDeg < 0) angleDeg += 360;
        
        const sliceAngle = 360 / this.config.sliceCount;
        const tolerance = this.config.uiOffsets.angleTolerance;
        let sliceIndex = -1;
        
        if (this.lastHighlightedSlice >= 0 && distance >= innerThreshold) {
            const currentSlice = this.lastHighlightedSlice;
            const currentStartAngle = (currentSlice * sliceAngle - 90 - tolerance + 720) % 360;
            const currentEndAngle = (currentSlice * sliceAngle - 90 + sliceAngle + tolerance + 720) % 360;
            
            let stillInCurrent = false;
            if (currentEndAngle > currentStartAngle) {
                stillInCurrent = angleDeg >= currentStartAngle && angleDeg < currentEndAngle;
            } else {
                stillInCurrent = angleDeg >= currentStartAngle || angleDeg < currentEndAngle;
            }
            
            if (stillInCurrent) {
                sliceIndex = currentSlice;
            }
        }
        
        if (sliceIndex < 0) {
            for (let i = 0; i < this.config.sliceCount; i++) {
                const sliceStartAngle = (i * sliceAngle - 90 + 360) % 360;
                const sliceEndAngle = (sliceStartAngle + sliceAngle) % 360;
                
                let isInSlice = false;
                if (sliceEndAngle > sliceStartAngle) {
                    isInSlice = angleDeg >= sliceStartAngle && angleDeg < sliceEndAngle;
                } else {
                    isInSlice = angleDeg >= sliceStartAngle || angleDeg < sliceEndAngle;
                }
                
                if (isInSlice) {
                    sliceIndex = i;
                    break;
                }
            }
        }
        
        if (sliceIndex < 0) sliceIndex = 0;
        
        return sliceIndex;
    }
    
    updateHighlightByDirection(mouseX, mouseY) {
        const dx = mouseX - this.menuCenterX;
        const dy = mouseY - this.menuCenterY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        const innerThreshold = this.config.innerRadius + this.config.uiOffsets.innerThreshold;
        if (distance < innerThreshold) {
            this.sliceElements.forEach(slice => {
                this.applySliceStyle(slice, false);
            });
            this.hideTooltip();
            this.lastHighlightedSlice = -1;
            return;
        }
        
        const sliceIndex = this.calculateSliceIndex(mouseX, mouseY);
        
        if (this.lastHighlightedSlice !== sliceIndex) {
            this.highlightSlice(sliceIndex, mouseX, mouseY);
            this.lastHighlightedSlice = sliceIndex;
        }
    }
    
    highlightSlice(index, mouseX, mouseY) {
        const dx = mouseX - this.menuCenterX;
        const dy = mouseY - this.menuCenterY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const innerThreshold = this.config.innerRadius + this.config.uiOffsets.innerThreshold;
        
        if (distance < innerThreshold) {
            this.sliceElements.forEach(slice => {
                this.applySliceStyle(slice, false);
            });
            this.hideTooltip();
            return;
        }
        
        this.sliceElements.forEach((slice, i) => {
            this.applySliceStyle(slice, i === index);
        });
        
        if (!this.hasSelectedNodes) {
            this.hideTooltip();
            return;
        }
        
        if (index >= 0 && index < this.actions.length) {
            const action = this.actions[index];
            this.tooltipElement.textContent = action.name;
            this.tooltipElement.style.left = (mouseX + this.config.uiOffsets.tooltipOffsetX) + 'px';
            this.tooltipElement.style.top = mouseY + 'px';
            this.applyTooltipStyle(this.tooltipElement, true);
        } else {
            this.hideTooltip();
        }
    }
    
    createMenuElement() {
        this.menuElement = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.menuElement.setAttribute('width', this.config.outerRadius * 2);
        this.menuElement.setAttribute('height', this.config.outerRadius * 2);
        
        this.applyMenuStyle(this.menuElement, 'initial');
        
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        filter.setAttribute('id', 'edgeBlur');
        filter.setAttribute('x', '-20%');
        filter.setAttribute('y', '-20%');
        filter.setAttribute('width', '140%');
        filter.setAttribute('height', '140%');
        const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur.setAttribute('stdDeviation', '2.5');
        filter.appendChild(feGaussianBlur);
        defs.appendChild(filter);
        this.menuElement.appendChild(defs);
        
        const angleStep = 360 / this.config.sliceCount;
        
        this.actions.forEach((action, index) => {
            const startAngle = index * angleStep - 90;
            const endAngle = startAngle + angleStep;
            
            const slice = this.createSlice(
                startAngle, 
                endAngle, 
                action.color === 'primary' ? this.config.colors.primary : this.config.colors.secondary,
                action,
                index
            );
            
            this.menuElement.appendChild(slice);
            this.sliceElements.push(slice);
        });
        
        document.body.appendChild(this.menuElement);
        
        this.tooltipElement = document.createElement('div');
        this.applyTooltipStyle(this.tooltipElement);
        document.body.appendChild(this.tooltipElement);
    }
    
    applyMenuStyle(element, state = 'initial') {
        const baseStyle = {
            position: 'fixed',
            zIndex: '10000',
            transformOrigin: '50% 50%',
            willChange: 'transform, opacity, filter'
        };
        
        if (state === 'initial') {
            Object.assign(element.style, baseStyle, {
                pointerEvents: 'none',
                opacity: '0',
                transform: 'scale(0.5) translateZ(0)',
                filter: 'blur(10px)',
                transition: `opacity ${this.config.animation.fadeIn}ms cubic-bezier(0.34, 1.56, 0.64, 1), transform ${this.config.animation.popup}ms cubic-bezier(0.34, 1.56, 0.64, 1), filter ${this.config.animation.fadeIn}ms ease`
            });
        } else if (state === 'visible') {
            Object.assign(element.style, baseStyle, {
                opacity: '1',
                transform: 'scale(1) translateZ(0)',
                filter: 'blur(0px)',
                pointerEvents: 'auto',
                transition: `opacity ${this.config.animation.fadeIn}ms cubic-bezier(0.34, 1.56, 0.64, 1), transform ${this.config.animation.popup}ms cubic-bezier(0.34, 1.56, 0.64, 1), filter ${this.config.animation.fadeIn}ms ease`
            });
        } else if (state === 'hiding') {
            Object.assign(element.style, baseStyle, {
                opacity: '0',
                filter: 'blur(4px)',
                pointerEvents: 'none',
                transition: `opacity ${this.config.animation.fadeOut}ms ease, filter ${this.config.animation.fadeOut}ms ease`
            });
        }
    }
    
    applySliceStyle(element, isHovering = false) {
        element.style.cursor = 'pointer';
        element.style.transition = 'filter 0.2s ease';
        
        if (isHovering) {
            element.style.filter = 'drop-shadow(0 0 16px currentColor) brightness(1.5)';
        } else {
            element.style.filter = '';
        }
    }
    
    applyTooltipStyle(element, visible = false) {
        Object.assign(element.style, {
            position: 'fixed',
            background: 'rgba(0, 0, 0, 0.85)',
            color: 'white',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            pointerEvents: 'none',
            whiteSpace: 'nowrap',
            transform: 'translateY(-50%)',
            transition: 'opacity 0.2s ease',
            zIndex: '10001',
            opacity: visible ? '1' : '0'
        });
    }
    
    createSlice(startAngle, endAngle, color, action, index) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.style.color = color;
        
        this.applySliceStyle(group, false);
        
        const centerX = this.config.outerRadius;
        const centerY = this.config.outerRadius;
        
        const startRad = startAngle * Math.PI / 180;
        const endRad = endAngle * Math.PI / 180;
        
        const x1 = centerX + this.config.innerRadius * Math.cos(startRad);
        const y1 = centerY + this.config.innerRadius * Math.sin(startRad);
        const x2 = centerX + this.config.outerRadius * Math.cos(startRad);
        const y2 = centerY + this.config.outerRadius * Math.sin(startRad);
        const x3 = centerX + this.config.outerRadius * Math.cos(endRad);
        const y3 = centerY + this.config.outerRadius * Math.sin(endRad);
        const x4 = centerX + this.config.innerRadius * Math.cos(endRad);
        const y4 = centerY + this.config.innerRadius * Math.sin(endRad);
        
        const largeArc = (endAngle - startAngle) > 180 ? 1 : 0;
        
        const path = `
            M ${x1} ${y1}
            L ${x2} ${y2}
            A ${this.config.outerRadius} ${this.config.outerRadius} 0 ${largeArc} 1 ${x3} ${y3}
            L ${x4} ${y4}
            A ${this.config.innerRadius} ${this.config.innerRadius} 0 ${largeArc} 0 ${x1} ${y1}
            Z
        `;
        
        const slicePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        slicePath.setAttribute('d', path);
        slicePath.setAttribute('fill', color);
        slicePath.setAttribute('stroke', 'rgba(255, 255, 255, 0.15)');
        slicePath.setAttribute('stroke-width', '1');
        slicePath.setAttribute('filter', 'url(#edgeBlur)');
        
        group.appendChild(slicePath);
        
        const midAngle = (startAngle + endAngle) / 2;
        const iconDistance = (this.config.innerRadius + this.config.outerRadius) / 2;
        const iconX = centerX + iconDistance * Math.cos(midAngle * Math.PI / 180);
        const iconY = centerY + iconDistance * Math.sin(midAngle * Math.PI / 180);
        
        const iconSize = 40;
        const iconScale = iconSize / 1024;
        
        const iconGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        iconGroup.setAttribute('transform', `translate(${iconX}, ${iconY}) scale(${iconScale}) translate(-512, -512)`);
        iconGroup.style.pointerEvents = 'none';
        iconGroup.setAttribute('filter', 'none');
        
        const iconSymbol = this.createSimpleIconSymbol(action.name);
        iconGroup.innerHTML = iconSymbol;
        
        group.appendChild(iconGroup);
        
        return group;
    }
    
    hideTooltip() {
        this.applyTooltipStyle(this.tooltipElement, false);
    }
    
    matchHotkey(event, hotkey) {
        const keyMatches = event.key.toLowerCase() === hotkey.key.toLowerCase() || 
                          event.code.toLowerCase() === `key${hotkey.key.toLowerCase()}`;
        
        const modifiers = hotkey.modifiers || [];
        const altMatch = modifiers.includes('alt') ? event.altKey : !event.altKey;
        const ctrlMatch = modifiers.includes('ctrl') ? (event.ctrlKey || event.metaKey) : !(event.ctrlKey || event.metaKey);
        const shiftMatch = modifiers.includes('shift') ? event.shiftKey : !event.shiftKey;
        
        return keyMatches && altMatch && ctrlMatch && shiftMatch;
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                if (!this.isVisible) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.undo();
                    return;
                }
            }
            
            if (this.matchHotkey(e, this.config.hotkey)) {
                e.preventDefault();
                e.stopPropagation();
                if (!this.isVisible) {
                this.show();
                }
            }
        }, true);
        
        document.addEventListener('keyup', (e) => {
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
                const sliceIndex = this.calculateSliceIndex(this.currentMouseX, this.currentMouseY);
                const action = (sliceIndex >= 0 && this.menuMouseMoved) ? this.actions[sliceIndex] : null;
                
                this.hide();
                
                if (action && action.handler) {
                    requestAnimationFrame(() => {
                        try {
                            action.handler();
                        } catch (error) {
                            console.error('❌ 节点对齐功能执行失败:', error);
                        }
                    });
                }
            }
        }, true);
    }
    
    show() {
        this.menuCenterX = this.lastMouseX;
        this.menuCenterY = this.lastMouseY;
        this.currentMouseX = this.lastMouseX;
        this.currentMouseY = this.lastMouseY;
        this.menuMouseMoved = false;
        
        const selectedNodes = this.getSelectedNodes();
        this.hasSelectedNodes = selectedNodes.length > 0;
        
        this.menuElement.style.left = (this.menuCenterX - this.config.outerRadius) + 'px';
        this.menuElement.style.top = (this.menuCenterY - this.config.outerRadius) + 'px';
        
        this.applyMenuStyle(this.menuElement, 'visible');
        this.isVisible = true;
        this.lastHighlightedSlice = -1;
    }
    
    showTempMessage(message) {
        if (this.currentMessageElement) {
            if (this.currentMessageElement.parentNode) {
                document.body.removeChild(this.currentMessageElement);
            }
            this.currentMessageElement = null;
        }
        if (this.messageTimeout) {
            clearTimeout(this.messageTimeout);
            this.messageTimeout = null;
        }
        
        const msgElement = document.createElement('div');
        msgElement.textContent = message;
        this.currentMessageElement = msgElement;
        
        Object.assign(msgElement.style, {
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(0, 0, 0, 0.85)',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '8px',
            fontSize: '14px',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            zIndex: '10002',
            pointerEvents: 'none',
            opacity: '0',
            transition: 'opacity 0.3s ease'
        });
        
        document.body.appendChild(msgElement);
        
        setTimeout(() => {
            if (msgElement === this.currentMessageElement) {
                msgElement.style.opacity = '1';
            }
        }, this.config.uiOffsets.fadeDelay);
        
        this.messageTimeout = setTimeout(() => {
            if (msgElement === this.currentMessageElement) {
                msgElement.style.opacity = '0';
                setTimeout(() => {
                    if (msgElement.parentNode && msgElement === this.currentMessageElement) {
                        document.body.removeChild(msgElement);
                        this.currentMessageElement = null;
                    }
                }, this.config.uiOffsets.messageFadeOut);
            }
        }, this.config.uiOffsets.messageDuration);
    }
    
    hide() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        
        this.sliceElements.forEach(slice => {
            this.applySliceStyle(slice, false);
        });
        this.hideTooltip();
        this.lastHighlightedSlice = -1;
        this.hasSelectedNodes = false;
        this.isVisible = false;
        
        this.applyMenuStyle(this.menuElement, 'hiding');
        
        setTimeout(() => {
            this.applyMenuStyle(this.menuElement, 'initial');
        }, this.config.animation.fadeOut);
    }
    
    getSelectedNodes() {
        const selectedNodes = [];
        const processedIds = new Set();
        
        if (app.canvas.selected_nodes) {
            for (const nodeId in app.canvas.selected_nodes) {
                const nodeIdNum = parseInt(nodeId);
                if (isNaN(nodeIdNum)) continue;
                
                const node = app.graph.getNodeById(nodeIdNum);
                if (node && !processedIds.has(node.id)) {
                    selectedNodes.push(node);
                    processedIds.add(node.id);
                }
            }
        }
        
        if (app.canvas.selected_group) {
            const group = app.canvas.selected_group;
            if (app.graph._nodes) {
                app.graph._nodes.forEach(node => {
                    if (!processedIds.has(node.id) && this.isNodeInGroup(node, group)) {
                        selectedNodes.push(node);
                        processedIds.add(node.id);
                    }
                });
            }
        }
        
        return selectedNodes;
    }
    
    isNodeInGroup(node, group) {
        return node.pos[0] >= group._pos[0] &&
               node.pos[1] >= group._pos[1] &&
               node.pos[0] + node.size[0] <= group._pos[0] + group._size[0] &&
               node.pos[1] + node.size[1] <= group._pos[1] + group._size[1];
    }
    
    getNodesBounds(nodes) {
        if (!nodes || nodes.length === 0) {
            return {
                minX: 0, minY: 0, maxX: 0, maxY: 0,
                centerX: 0, centerY: 0,
                width: 0, height: 0
            };
        }
        
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        for (const node of nodes) {
            if (!node || !node.pos || !node.size) continue;
            const nodeRight = node.pos[0] + node.size[0];
            const nodeBottom = node.pos[1] + node.size[1];
            
            if (node.pos[0] < minX) minX = node.pos[0];
            if (node.pos[1] < minY) minY = node.pos[1];
            if (nodeRight > maxX) maxX = nodeRight;
            if (nodeBottom > maxY) maxY = nodeBottom;
        }
        
        return {
            minX, minY, maxX, maxY,
            centerX: (minX + maxX) / 2,
            centerY: (minY + maxY) / 2,
            width: maxX - minX,
            height: maxY - minY
        };
    }
    
    validateNodeCount(nodes, minCount, actionName) {
        if (nodes.length < minCount) {
            const message = minCount === 1 
                ? `请先选择节点` 
                : `${actionName}需要至少${minCount}个节点（当前${nodes.length}个）`;
            this.showTempMessage(message);
            return false;
        }
        return true;
    }
    
    alignLeft() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 1, '左对齐')) return;
        
        this.saveNodesState(nodes, '左对齐');
        
        let minX = Infinity;
        for (const node of nodes) {
            if (node.pos[0] < minX) minX = node.pos[0];
        }
        
        for (const node of nodes) {
            node.pos[0] = minX;
        }
        
        app.graph.setDirtyCanvas(true, true);
    }
    
    alignRight() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 1, '右对齐')) return;
        
        this.saveNodesState(nodes, '右对齐');
        
        let maxRight = -Infinity;
        for (const node of nodes) {
            const right = node.pos[0] + node.size[0];
            if (right > maxRight) maxRight = right;
        }
        
        for (const node of nodes) {
            node.pos[0] = maxRight - node.size[0];
        }
        
        app.graph.setDirtyCanvas(true, true);
    }
    
    alignTop() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 1, '上对齐')) return;
        
        this.saveNodesState(nodes, '上对齐');
        
        let minY = Infinity;
        for (const node of nodes) {
            if (node.pos[1] < minY) minY = node.pos[1];
        }
        
        for (const node of nodes) {
            node.pos[1] = minY;
        }
        
        app.graph.setDirtyCanvas(true, true);
    }
    
    alignBottom() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 1, '下对齐')) return;
        
        this.saveNodesState(nodes, '下对齐');
        
        let maxBottom = -Infinity;
        for (const node of nodes) {
            const bottom = node.pos[1] + node.size[1];
            if (bottom > maxBottom) maxBottom = bottom;
        }
        
        for (const node of nodes) {
            node.pos[1] = maxBottom - node.size[1];
        }
        
        app.graph.setDirtyCanvas(true, true);
    }
    
    horizontalCenter() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 1, '水平居中')) return;
        
        this.saveNodesState(nodes, '水平居中');
        
        const bounds = this.getNodesBounds(nodes);
        nodes.forEach(node => {
            node.pos[0] = bounds.centerX - node.size[0] / 2;
        });
        
        app.graph.setDirtyCanvas(true, true);
    }
    
    verticalCenter() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 1, '垂直居中')) return;
        
        this.saveNodesState(nodes, '垂直居中');
        
        const bounds = this.getNodesBounds(nodes);
        nodes.forEach(node => {
            node.pos[1] = bounds.centerY - node.size[1] / 2;
        });
        
        app.graph.setDirtyCanvas(true, true);
    }
    
    distributeHorizontal() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 3, '水平分布')) return;
        
        this.saveNodesState(nodes, '水平分布');
        
        nodes.sort((a, b) => a.pos[0] - b.pos[0]);
        
        const bounds = this.getNodesBounds(nodes);
        const totalNodeWidth = nodes.reduce((sum, n) => sum + n.size[0], 0);
        const gap = (bounds.width - totalNodeWidth) / (nodes.length - 1);
        
        let currentX = nodes[0].pos[0];
        nodes.forEach(node => {
            node.pos[0] = currentX;
            currentX += node.size[0] + gap;
        });
        
        app.graph.setDirtyCanvas(true, true);
    }
    
    distributeVertical() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 3, '垂直分布')) return;
        
        this.saveNodesState(nodes, '垂直分布');
        
        nodes.sort((a, b) => a.pos[1] - b.pos[1]);
        
        const bounds = this.getNodesBounds(nodes);
        const totalNodeHeight = nodes.reduce((sum, n) => sum + n.size[1], 0);
        const gap = (bounds.height - totalNodeHeight) / (nodes.length - 1);
        
        let currentY = nodes[0].pos[1];
        nodes.forEach(node => {
            node.pos[1] = currentY;
            currentY += node.size[1] + gap;
        });
        
        app.graph.setDirtyCanvas(true, true);
    }
    
    createSimpleIconSymbol(actionName) {
        const iconMap = {
            '上对齐': `
                <path d="M200 200 L824 200 M280 280 L380 280 L380 480 L280 480 Z M462 280 L562 280 L562 580 L462 580 Z M644 280 L744 280 L744 680 L644 680 Z" 
                      fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
            `,
            '下对齐': `
                <path d="M200 824 L824 824 M280 744 L380 744 L380 544 L280 544 Z M462 744 L562 744 L562 444 L462 444 Z M644 744 L744 744 L744 344 L644 344 Z" 
                      fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
            `,
            '左对齐': `
                <path d="M200 200 L200 824 M280 280 L480 280 L480 380 L280 380 Z M280 462 L580 462 L580 562 L280 562 Z M280 644 L680 644 L680 744 L280 744 Z" 
                      fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
            `,
            '右对齐': `
                <path d="M824 200 L824 824 M744 280 L544 280 L544 380 L744 380 Z M744 462 L444 462 L444 562 L744 562 Z M744 644 L344 644 L344 744 L744 744 Z" 
                      fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
            `,
            '水平居中': `
                <path d="M512 200 L512 824 M280 380 L380 380 L380 644 L280 644 Z M644 380 L744 380 L744 644 L644 644 Z" 
                      fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
            `,
            '垂直居中': `
                <path d="M200 512 L824 512 M380 280 L644 280 L644 380 L380 380 Z M380 644 L644 644 L644 744 L380 744 Z" 
                      fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
            `,
            '左右拉伸': `
                <path d="M200 512 L824 512 M200 512 L280 450 M200 512 L280 574 M824 512 L744 450 M824 512 L744 574 M350 380 L674 380 L674 644 L350 644 Z" 
                      fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
            `,
            '上下拉伸': `
                <path d="M512 200 L512 824 M512 200 L450 280 M512 200 L574 280 M512 824 L450 744 M512 824 L574 744 M380 350 L644 350 L644 674 L380 674 Z" 
                      fill="white" stroke="white" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>
            `,
            '水平分布': `
                <path d="M220 400 L320 400 L320 624 L220 624 Z M462 400 L562 400 L562 624 L462 624 Z M704 400 L804 400 L804 624 L704 624 Z" 
                      fill="white" stroke="white" stroke-width="20" stroke-linejoin="round"/>
                <path d="M340 512 L442 512 M582 512 L684 512" 
                      stroke="white" stroke-width="20" stroke-linecap="round"/>
                <path d="M360 490 L340 512 L360 534 M422 490 L442 512 L422 534 M602 490 L582 512 L602 534 M664 490 L684 512 L664 534" 
                      fill="none" stroke="white" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
            `,
            '垂直分布': `
                <path d="M400 220 L624 220 L624 320 L400 320 Z M400 462 L624 462 L624 562 L400 562 Z M400 704 L624 704 L624 804 L400 804 Z" 
                      fill="white" stroke="white" stroke-width="20" stroke-linejoin="round"/>
                <path d="M512 340 L512 442 M512 582 L512 684" 
                      stroke="white" stroke-width="20" stroke-linecap="round"/>
                <path d="M490 360 L512 340 L534 360 M490 422 L512 442 L534 422 M490 602 L512 582 L534 602 M490 664 L512 684 L534 664" 
                      fill="none" stroke="white" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
            `
        };
        
        return iconMap[actionName] || `<circle cx="512" cy="512" r="200" fill="white"/>`;
    }
    
    stretchHorizontal() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 2, '左右拉伸')) return;
        
        this.saveNodesState(nodes, '左右拉伸');
        
        const bounds = this.getNodesBounds(nodes);
        nodes.forEach(node => {
            node.pos[0] = bounds.minX;
            node.size[0] = bounds.width;
        });
        
        app.graph.setDirtyCanvas(true, true);
    }
    
    stretchVertical() {
        const nodes = this.getSelectedNodes();
        if (!this.validateNodeCount(nodes, 2, '上下拉伸')) return;
        
        this.saveNodesState(nodes, '上下拉伸');
        
        const bounds = this.getNodesBounds(nodes);
        nodes.forEach(node => {
            node.pos[1] = bounds.minY;
            node.size[1] = bounds.height;
        });
        
        app.graph.setDirtyCanvas(true, true);
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
        } catch (error) {
            console.error("❌ 节点对齐工具加载失败:", error);
        }
    },
    settings: [
        {
            id: "🎨QING.节点对齐.外圈半径",
            name: "菜单外圈半径",
            type: "slider",
            defaultValue: 160,
            attrs: {
                min: 100,
                max: 300,
                step: 10
            },
            tooltip: "调整对齐菜单的外圈大小（像素）。较大的菜单更容易选择，但占用更多屏幕空间。",
            onChange: (newVal) => {
                if (window.QINGAlignMenu) {
                    window.QINGAlignMenu.config.outerRadius = newVal;
                }
            }
        },
        {
            id: "🎨QING.节点对齐.内圈半径",
            name: "菜单内圈半径",
            type: "slider",
            defaultValue: 72,
            attrs: {
                min: 40,
                max: 150,
                step: 4
            },
            tooltip: "调整对齐菜单的内圈大小（像素）。内圈是取消区域，鼠标在此区域释放不会执行对齐操作。",
            onChange: (newVal) => {
                if (window.QINGAlignMenu) {
                    window.QINGAlignMenu.config.innerRadius = newVal;
                }
            }
        },
        {
            id: "🎨QING.节点对齐.主色调",
            name: "主色调",
            type: "color",
            defaultValue: "505050",
            tooltip: "设置菜单扇区的主色调（上对齐、右对齐、下对齐、左对齐、垂直分布、水平分布）。",
            onChange: (newVal) => {
                if (window.QINGAlignMenu && newVal && /^[0-9a-fA-F]{6}$/.test(newVal)) {
                    const alpha = 0.75;
                    const r = parseInt(newVal.substring(0, 2), 16);
                    const g = parseInt(newVal.substring(2, 4), 16);
                    const b = parseInt(newVal.substring(4, 6), 16);
                    window.QINGAlignMenu.config.colors.primary = `rgba(${r}, ${g}, ${b}, ${alpha})`;
                }
            }
        },
        {
            id: "🎨QING.节点对齐.次色调",
            name: "次色调",
            type: "color",
            defaultValue: "1a442e",
            tooltip: "设置菜单扇区的次色调（垂直居中、水平居中、上下拉伸、左右拉伸）。",
            onChange: (newVal) => {
                if (window.QINGAlignMenu && newVal && /^[0-9a-fA-F]{6}$/.test(newVal)) {
                    const alpha = 0.75;
                    const r = parseInt(newVal.substring(0, 2), 16);
                    const g = parseInt(newVal.substring(2, 4), 16);
                    const b = parseInt(newVal.substring(4, 6), 16);
                    window.QINGAlignMenu.config.colors.secondary = `rgba(${r}, ${g}, ${b}, ${alpha})`;
                }
            }
        },
        {
            id: "🎨QING.节点对齐.动画速度",
            name: "动画速度",
            type: "combo",
            defaultValue: "标准",
            options: [
                { text: "快速（响应优先）", value: "快速" },
                { text: "标准（平衡）", value: "标准" },
                { text: "慢速（优雅动画）", value: "慢速" }
            ],
            tooltip: "调整菜单显示和隐藏的动画速度。快速模式响应更迅速，慢速模式动画更优雅。",
            onChange: (newVal) => {
                if (window.QINGAlignMenu) {
                    const speeds = {
                        "快速": { fadeIn: 200, fadeOut: 150, popup: 250 },
                        "标准": { fadeIn: 450, fadeOut: 350, popup: 600 },
                        "慢速": { fadeIn: 600, fadeOut: 450, popup: 800 }
                    };
                    if (speeds[newVal]) {
                        Object.assign(window.QINGAlignMenu.config.animation, speeds[newVal]);
                    }
                }
            }
        },
        {
            id: "🎨QING.节点对齐.Tooltip偏移",
            name: "提示框偏移",
            type: "slider",
            defaultValue: 15,
            attrs: {
                min: 0,
                max: 50,
                step: 5
            },
            tooltip: "调整鼠标旁边提示框的横向偏移距离（像素）。",
            onChange: (newVal) => {
                if (window.QINGAlignMenu) {
                    window.QINGAlignMenu.config.uiOffsets.tooltipOffsetX = newVal;
                }
            }
        },
        {
            id: "🎨QING.节点对齐.消息持续时间",
            name: "消息持续时间",
            type: "slider",
            defaultValue: 2000,
            attrs: {
                min: 1000,
                max: 5000,
                step: 500
            },
            tooltip: "调整操作提示消息的显示时间（毫秒）。",
            onChange: (newVal) => {
                if (window.QINGAlignMenu) {
                    window.QINGAlignMenu.config.uiOffsets.messageDuration = newVal;
                }
            }
        },
        {
            id: "🎨QING.节点对齐.撤回历史记录",
            name: "撤回历史记录",
            type: "slider",
            defaultValue: 20,
            attrs: {
                min: 5,
                max: 100,
                step: 5
            },
            tooltip: "可撤销的对齐操作数量（Ctrl+Z）。值越大占用内存越多，但可以撤回更多步骤。",
            onChange: (newVal) => {
                if (window.QINGAlignMenu) {
                    window.QINGAlignMenu.config.undo.maxHistorySize = newVal;
                    window.QINGAlignMenu.maxHistorySize = newVal;
                    
                    while (window.QINGAlignMenu.historyStack.length > newVal) {
                        window.QINGAlignMenu.historyStack.shift();
                    }
                }
            }
        },
        {
            id: "🎨QING.节点对齐.快捷键",
            name: "菜单快捷键",
            type: "combo",
            defaultValue: JSON.stringify({ key: 'a', modifiers: ['alt'] }),
            options: [
                { text: "Alt + A（默认）", value: JSON.stringify({ key: 'a', modifiers: ['alt'] }) },
                { text: "Alt + Q", value: JSON.stringify({ key: 'q', modifiers: ['alt'] }) },
                { text: "Alt + W", value: JSON.stringify({ key: 'w', modifiers: ['alt'] }) },
                { text: "Ctrl + Alt + A", value: JSON.stringify({ key: 'a', modifiers: ['ctrl', 'alt'] }) },
                { text: "Shift + Alt + A", value: JSON.stringify({ key: 'a', modifiers: ['shift', 'alt'] }) }
            ],
            tooltip: "设置打开对齐菜单的快捷键组合。修改后刷新页面生效。",
            onChange: (newVal) => {
                if (window.QINGAlignMenu) {
                    try {
                        window.QINGAlignMenu.config.hotkey = JSON.parse(newVal);
                    } catch (e) {
                        console.warn('快捷键配置解析失败:', e);
                    }
                }
            }
        }
    ]
});


