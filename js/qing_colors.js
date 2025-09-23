import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "QING.Colors",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        // 检查节点的category是否以"QING"开头
        if (nodeData.category && nodeData.category.startsWith("QING")) {
            // 在节点创建时设置颜色
            const originalNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (originalNodeCreated) {
                    originalNodeCreated.apply(this, arguments);
                }
                
                // 只设置节点标题的颜色为深紫色 #1F0434
                this.color = "#1A442E";  // 标题文字颜色为绿色
                // 不设置 bgcolor，保持节点主体的默认颜色
            };
        }
    }
});
