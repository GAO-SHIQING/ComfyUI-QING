import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "comfy.qing.letMeSee",

        async beforeRegisterNodeDef(nodeType, nodeData, app) {
            // 处理我们的调试节点
            if (nodeData.name === 'LetMeSee' || nodeData.name === 'ShowMePure') {
            
            function populate(text) {
                // 清理现有的text widgets
                if (this.widgets) {
                    const pos = this.widgets.findIndex((w) => w.name === "text");
                    if (pos !== -1) {
                        for (let i = pos; i < this.widgets.length; i++) {
                            this.widgets[i].onRemove?.();
                        }
                        this.widgets.length = pos;
                    }
                }

                // 为每个文本项创建widget 
                for (const list of text) {
                    const w = ComfyWidgets["STRING"](this, "text", ["STRING", { multiline: true }], app).widget;
                    w.inputEl.readOnly = true;
                    w.inputEl.disabled = true;
                    w.value = list;
                }

                // 更新节点大小
                requestAnimationFrame(() => {
                    const sz = this.computeSize();
                    if (sz[0] < this.size[0]) {
                        sz[0] = this.size[0];
                    }
                    if (sz[1] < this.size[1]) {
                        sz[1] = this.size[1];
                    }
                    this.onResize?.(sz);
                    app.graph.setDirtyCanvas(true, false);
                });
            }

            // 当节点执行时接收UI数据并显示
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);
                
                // 处理从Python返回的ui.text数据
                if (message.text) {
                    populate.call(this, message.text);
                }
            };

            // 当节点配置时也要恢复显示
            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function () {
                onConfigure?.apply(this, arguments);
                if (this.widgets_values?.length) {
                    populate.call(this, this.widgets_values);
                }
            };
        }
    }
});