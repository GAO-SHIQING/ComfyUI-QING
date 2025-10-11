/**
 * 节点对齐工具 - 径向菜单UI
 */

import { getIconSVG } from '../icons/alignment.js';
import { calculateSliceIndex } from '../utils/geometry.js';

export class RadialMenuUI {
    constructor(config, actions) {
        this.config = config;
        this.actions = actions;
        this.menuElement = null;
        this.tooltipElement = null;
        this.sliceElements = [];
        this.currentMessageElement = null;
        this.messageTimeout = null;
        this.menuCenterX = 0;
        this.menuCenterY = 0;
        this.lastHighlightedSlice = -1;
        this.hasSelectedNodes = false;
        
        this.createMenuElement();
    }
    
    /**
     * 创建菜单元素
     */
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
    
    /**
     * 创建扇形切片
     */
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
        
        const iconSymbol = getIconSVG(action.name);
        iconGroup.innerHTML = iconSymbol;
        
        group.appendChild(iconGroup);
        
        return group;
    }
    
    /**
     * 应用菜单样式
     */
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
    
    /**
     * 应用切片样式
     */
    applySliceStyle(element, isHovering = false) {
        element.style.cursor = 'pointer';
        element.style.transition = 'filter 0.2s ease';
        
        if (isHovering) {
            element.style.filter = 'drop-shadow(0 0 16px currentColor) brightness(1.5)';
        } else {
            element.style.filter = '';
        }
    }
    
    /**
     * 应用提示框样式
     */
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
    
    /**
     * 显示菜单
     */
    show(mouseX, mouseY, hasSelectedNodes) {
        this.menuCenterX = mouseX;
        this.menuCenterY = mouseY;
        this.hasSelectedNodes = hasSelectedNodes;
        
        this.menuElement.style.left = (this.menuCenterX - this.config.outerRadius) + 'px';
        this.menuElement.style.top = (this.menuCenterY - this.config.outerRadius) + 'px';
        
        this.applyMenuStyle(this.menuElement, 'visible');
        this.lastHighlightedSlice = -1;
    }
    
    /**
     * 隐藏菜单
     */
    hide() {
        this.sliceElements.forEach(slice => {
            this.applySliceStyle(slice, false);
        });
        this.hideTooltip();
        this.lastHighlightedSlice = -1;
        this.hasSelectedNodes = false;
        
        this.applyMenuStyle(this.menuElement, 'hiding');
        
        setTimeout(() => {
            this.applyMenuStyle(this.menuElement, 'initial');
        }, this.config.animation.fadeOut);
    }
    
    /**
     * 更新高亮（根据鼠标位置）
     */
    updateHighlight(mouseX, mouseY) {
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
        
        const sliceIndex = calculateSliceIndex(
            mouseX, mouseY,
            this.menuCenterX, this.menuCenterY,
            this.config,
            this.lastHighlightedSlice
        );
        
        if (this.lastHighlightedSlice !== sliceIndex) {
            this.highlightSlice(sliceIndex, mouseX, mouseY);
            this.lastHighlightedSlice = sliceIndex;
        }
    }
    
    /**
     * 高亮特定切片
     */
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
    
    /**
     * 隐藏提示框
     */
    hideTooltip() {
        this.applyTooltipStyle(this.tooltipElement, false);
    }
    
    /**
     * 显示临时消息
     */
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
    
    /**
     * 获取最后高亮的切片索引
     */
    getLastHighlightedSlice() {
        return this.lastHighlightedSlice;
    }
}

