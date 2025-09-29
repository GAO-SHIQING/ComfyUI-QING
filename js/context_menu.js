import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "comfy.qing.contextMenu",
    
    async setup() {
        // 获取原始的getNodeMenuOptions方法
        const origGetNodeMenuOptions = LGraphCanvas.prototype.getNodeMenuOptions;
        
        // 重写getNodeMenuOptions方法来添加我们的右键菜单选项
        LGraphCanvas.prototype.getNodeMenuOptions = function(node) {
            // 先获取原始的菜单选项
            const options = origGetNodeMenuOptions ? origGetNodeMenuOptions.apply(this, arguments) : [];
            
            // 创建我们的菜单选项数组
            const qingOptions = [];
            
            // 添加"我想看看"选项
            qingOptions.push({
                content: "🔍 添加：我想看看",
                callback: () => {
                    // 创建LetMeSee节点
                    const letMeSeeNode = LiteGraph.createNode("LetMeSee");
                    if (letMeSeeNode) {
                        // 设置节点位置（在当前节点旁边）
                        letMeSeeNode.pos = [node.pos[0] + node.size[0] + 50, node.pos[1]];
                        
                        // 添加节点到图形
                        app.graph.add(letMeSeeNode);
                        
                        // 连接当前节点的第一个输出到LetMeSee节点的输入
                        if (node.outputs && node.outputs.length > 0 && letMeSeeNode.inputs && letMeSeeNode.inputs.length > 0) {
                            node.connect(0, letMeSeeNode, 0);
                        }
                        
                        // 选中新创建的节点
                        app.canvas.selectNode(letMeSeeNode);
                        app.graph.setDirtyCanvas(true, true);
                    }
                }
            });
            
            // 添加"让我看看"选项
            qingOptions.push({
                content: "👀 添加：让我看看",
                callback: () => {
                    // 创建ShowMePure节点
                    const showMePureNode = LiteGraph.createNode("ShowMePure");
                    if (showMePureNode) {
                        // 设置节点位置（在当前节点旁边）
                        showMePureNode.pos = [node.pos[0] + node.size[0] + 50, node.pos[1] + 100];
                        
                        // 添加节点到图形
                        app.graph.add(showMePureNode);
                        
                        // 连接当前节点的第一个输出到ShowMePure节点的输入
                        if (node.outputs && node.outputs.length > 0 && showMePureNode.inputs && showMePureNode.inputs.length > 0) {
                            node.connect(0, showMePureNode, 0);
                        }
                        
                        // 选中新创建的节点
                        app.canvas.selectNode(showMePureNode);
                        app.graph.setDirtyCanvas(true, true);
                    }
                }
            });
            
            // 添加分隔符
            qingOptions.push(null);
            
            // 将我们的选项放在最前面，然后是原有选项
            return [...qingOptions, ...options];
        };
    }
});
