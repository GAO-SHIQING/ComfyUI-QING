/**
 * 节点对齐工具 - 对齐算法引擎
 */

import { getNodesBounds } from '../utils/geometry.js';

export class AlignmentEngine {
    constructor(app) {
        this.app = app;
    }
    
    /**
     * 左对齐
     */
    alignLeft(nodes) {
        if (!nodes || nodes.length === 0) return;
        
        let minX = Infinity;
        for (const node of nodes) {
            if (node.pos[0] < minX) minX = node.pos[0];
        }
        
        for (const node of nodes) {
            node.pos[0] = minX;
        }
        
        this.app.graph.setDirtyCanvas(true, true);
    }
    
    /**
     * 右对齐
     */
    alignRight(nodes) {
        if (!nodes || nodes.length === 0) return;
        
        let maxRight = -Infinity;
        for (const node of nodes) {
            const right = node.pos[0] + node.size[0];
            if (right > maxRight) maxRight = right;
        }
        
        for (const node of nodes) {
            node.pos[0] = maxRight - node.size[0];
        }
        
        this.app.graph.setDirtyCanvas(true, true);
    }
    
    /**
     * 上对齐
     */
    alignTop(nodes) {
        if (!nodes || nodes.length === 0) return;
        
        let minY = Infinity;
        for (const node of nodes) {
            if (node.pos[1] < minY) minY = node.pos[1];
        }
        
        for (const node of nodes) {
            node.pos[1] = minY;
        }
        
        this.app.graph.setDirtyCanvas(true, true);
    }
    
    /**
     * 下对齐
     */
    alignBottom(nodes) {
        if (!nodes || nodes.length === 0) return;
        
        let maxBottom = -Infinity;
        for (const node of nodes) {
            const bottom = node.pos[1] + node.size[1];
            if (bottom > maxBottom) maxBottom = bottom;
        }
        
        for (const node of nodes) {
            node.pos[1] = maxBottom - node.size[1];
        }
        
        this.app.graph.setDirtyCanvas(true, true);
    }
    
    /**
     * 水平居中
     */
    horizontalCenter(nodes) {
        if (!nodes || nodes.length === 0) return;
        
        const bounds = getNodesBounds(nodes);
        nodes.forEach(node => {
            node.pos[0] = bounds.centerX - node.size[0] / 2;
        });
        
        this.app.graph.setDirtyCanvas(true, true);
    }
    
    /**
     * 垂直居中
     */
    verticalCenter(nodes) {
        if (!nodes || nodes.length === 0) return;
        
        const bounds = getNodesBounds(nodes);
        nodes.forEach(node => {
            node.pos[1] = bounds.centerY - node.size[1] / 2;
        });
        
        this.app.graph.setDirtyCanvas(true, true);
    }
    
    /**
     * 水平分布
     */
    distributeHorizontal(nodes) {
        if (!nodes || nodes.length < 3) return;
        
        nodes.sort((a, b) => a.pos[0] - b.pos[0]);
        
        const bounds = getNodesBounds(nodes);
        const totalNodeWidth = nodes.reduce((sum, n) => sum + n.size[0], 0);
        const gap = (bounds.width - totalNodeWidth) / (nodes.length - 1);
        
        let currentX = nodes[0].pos[0];
        nodes.forEach(node => {
            node.pos[0] = currentX;
            currentX += node.size[0] + gap;
        });
        
        this.app.graph.setDirtyCanvas(true, true);
    }
    
    /**
     * 垂直分布
     */
    distributeVertical(nodes) {
        if (!nodes || nodes.length < 3) return;
        
        nodes.sort((a, b) => a.pos[1] - b.pos[1]);
        
        const bounds = getNodesBounds(nodes);
        const totalNodeHeight = nodes.reduce((sum, n) => sum + n.size[1], 0);
        const gap = (bounds.height - totalNodeHeight) / (nodes.length - 1);
        
        let currentY = nodes[0].pos[1];
        nodes.forEach(node => {
            node.pos[1] = currentY;
            currentY += node.size[1] + gap;
        });
        
        this.app.graph.setDirtyCanvas(true, true);
    }
    
    /**
     * 左右拉伸
     */
    stretchHorizontal(nodes) {
        if (!nodes || nodes.length < 2) return;
        
        const bounds = getNodesBounds(nodes);
        nodes.forEach(node => {
            node.pos[0] = bounds.minX;
            node.size[0] = bounds.width;
        });
        
        this.app.graph.setDirtyCanvas(true, true);
    }
    
    /**
     * 上下拉伸
     */
    stretchVertical(nodes) {
        if (!nodes || nodes.length < 2) return;
        
        const bounds = getNodesBounds(nodes);
        nodes.forEach(node => {
            node.pos[1] = bounds.minY;
            node.size[1] = bounds.height;
        });
        
        this.app.graph.setDirtyCanvas(true, true);
    }
}

