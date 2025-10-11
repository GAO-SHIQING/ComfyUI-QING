/**
 * 节点对齐工具 - 统一设置配置
 */

export const DEFAULT_CONFIG = {
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
        maxHistorySize: 20
    },
    hotkey: {
        key: 'a',
        modifiers: ['alt']
    }
};

/**
 * ComfyUI设置项定义
 */
export const SETTINGS_DEFINITIONS = [
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
                window.QINGAlignMenu.historyManager.setMaxHistorySize(newVal);
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
];

/**
 * 从ComfyUI设置中加载用户配置
 */
export function loadUserSettings(app, config) {
    try {
        if (!app.extensionManager?.setting) return;
        
        const outerRadius = app.extensionManager.setting.get('🎨QING.节点对齐.外圈半径');
        if (outerRadius !== undefined) config.outerRadius = outerRadius;
        
        const innerRadius = app.extensionManager.setting.get('🎨QING.节点对齐.内圈半径');
        if (innerRadius !== undefined) config.innerRadius = innerRadius;
        
        const primaryColor = app.extensionManager.setting.get('🎨QING.节点对齐.主色调');
        if (primaryColor && /^[0-9a-fA-F]{6}$/.test(primaryColor)) {
            const alpha = 0.75;
            const r = parseInt(primaryColor.substring(0, 2), 16);
            const g = parseInt(primaryColor.substring(2, 4), 16);
            const b = parseInt(primaryColor.substring(4, 6), 16);
            config.colors.primary = `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        
        const secondaryColor = app.extensionManager.setting.get('🎨QING.节点对齐.次色调');
        if (secondaryColor && /^[0-9a-fA-F]{6}$/.test(secondaryColor)) {
            const alpha = 0.75;
            const r = parseInt(secondaryColor.substring(0, 2), 16);
            const g = parseInt(secondaryColor.substring(2, 4), 16);
            const b = parseInt(secondaryColor.substring(4, 6), 16);
            config.colors.secondary = `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        
        const animationSpeed = app.extensionManager.setting.get('🎨QING.节点对齐.动画速度');
        const speeds = {
            "快速": { fadeIn: 200, fadeOut: 150, popup: 250 },
            "标准": { fadeIn: 450, fadeOut: 350, popup: 600 },
            "慢速": { fadeIn: 600, fadeOut: 450, popup: 800 }
        };
        if (animationSpeed && speeds[animationSpeed]) {
            Object.assign(config.animation, speeds[animationSpeed]);
        }
        
        const tooltipOffset = app.extensionManager.setting.get('🎨QING.节点对齐.Tooltip偏移');
        if (tooltipOffset !== undefined) config.uiOffsets.tooltipOffsetX = tooltipOffset;
        
        const messageDuration = app.extensionManager.setting.get('🎨QING.节点对齐.消息持续时间');
        if (messageDuration !== undefined) config.uiOffsets.messageDuration = messageDuration;
        
        const maxHistory = app.extensionManager.setting.get('🎨QING.节点对齐.撤回历史记录');
        if (maxHistory !== undefined) {
            config.undo.maxHistorySize = maxHistory;
        }
        
        const hotkeyConfig = app.extensionManager.setting.get('🎨QING.节点对齐.快捷键');
        if (hotkeyConfig) {
            try {
                config.hotkey = JSON.parse(hotkeyConfig);
            } catch (e) {
                console.warn('快捷键配置解析失败:', e);
            }
        }
        
    } catch (error) {
        console.warn('⚠️ 节点对齐设置加载失败，使用默认值:', error);
    }
}

