/**
 * 节点对齐工具 - 验证工具
 */

/**
 * 验证节点数量是否满足最小要求
 */
export function validateNodeCount(nodes, minCount, actionName, showMessageFn) {
    if (nodes.length < minCount) {
        const message = minCount === 1 
            ? `请先选择节点` 
            : `${actionName}需要至少${minCount}个节点（当前${nodes.length}个）`;
        if (showMessageFn) {
            showMessageFn(message);
        }
        return false;
    }
    return true;
}

/**
 * 获取选中的节点
 */
export function getSelectedNodes(app) {
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
                if (!processedIds.has(node.id) && isNodeInGroup(node, group)) {
                    selectedNodes.push(node);
                    processedIds.add(node.id);
                }
            });
        }
    }
    
    return selectedNodes;
}

/**
 * 检查节点是否在组内
 */
function isNodeInGroup(node, group) {
    return node.pos[0] >= group._pos[0] &&
           node.pos[1] >= group._pos[1] &&
           node.pos[0] + node.size[0] <= group._pos[0] + group._size[0] &&
           node.pos[1] + node.size[1] <= group._pos[1] + group._size[1];
}

