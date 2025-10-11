/**
 * 节点对齐工具 - 几何计算工具
 */

/**
 * 获取多个节点的边界信息
 */
export function getNodesBounds(nodes) {
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

/**
 * 检查节点是否在组内
 */
export function isNodeInGroup(node, group) {
    return node.pos[0] >= group._pos[0] &&
           node.pos[1] >= group._pos[1] &&
           node.pos[0] + node.size[0] <= group._pos[0] + group._size[0] &&
           node.pos[1] + node.size[1] <= group._pos[1] + group._size[1];
}

/**
 * 计算扇形索引（基于鼠标位置和菜单中心）
 */
export function calculateSliceIndex(mouseX, mouseY, menuCenterX, menuCenterY, config, lastHighlightedSlice) {
    const dx = mouseX - menuCenterX;
    const dy = mouseY - menuCenterY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    const innerThreshold = config.innerRadius + config.uiOffsets.innerThreshold;
    if (distance < innerThreshold) {
        return -1;
    }
    
    const angleRad = Math.atan2(dy, dx);
    
    let angleDeg = angleRad * 180 / Math.PI;
    if (angleDeg < 0) angleDeg += 360;
    
    const sliceAngle = 360 / config.sliceCount;
    const tolerance = config.uiOffsets.angleTolerance;
    let sliceIndex = -1;
    
    if (lastHighlightedSlice >= 0 && distance >= innerThreshold) {
        const currentSlice = lastHighlightedSlice;
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
        for (let i = 0; i < config.sliceCount; i++) {
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

