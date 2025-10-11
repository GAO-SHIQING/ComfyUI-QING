/**
 * 快捷键捕获工具
 * 用于捕获用户按下的键盘组合并转换为配置格式
 */

export class HotkeyCapture {
    /**
     * 捕获键盘事件并解析为快捷键配置
     * @param {KeyboardEvent} event - 键盘事件
     * @returns {Object|null} 快捷键配置对象或 null（如果按键无效）
     */
    static captureHotkey(event) {
        event.preventDefault();
        event.stopPropagation();
        
        // 收集修饰键
        const modifiers = [];
        if (event.ctrlKey) modifiers.push('ctrl');
        if (event.altKey) modifiers.push('alt');
        if (event.shiftKey) modifiers.push('shift');
        
        // 获取主按键
        const key = event.key.toLowerCase();
        
        // 只接受字母和数字键
        if (!/^[a-z0-9]$/.test(key)) {
            return null;
        }
        
        // 至少需要一个修饰键（避免单独字母/数字键冲突）
        if (modifiers.length === 0) {
            return null;
        }
        
        return {
            key: key,
            modifiers: modifiers,
            display: this.formatHotkeyDisplay(modifiers, key)
        };
    }
    
    /**
     * 格式化快捷键显示文本
     * @param {Array<string>} modifiers - 修饰键数组
     * @param {string} key - 主按键
     * @returns {string} 格式化的显示文本
     */
    static formatHotkeyDisplay(modifiers, key) {
        const parts = [];
        if (modifiers.includes('ctrl')) parts.push('Ctrl');
        if (modifiers.includes('alt')) parts.push('Alt');
        if (modifiers.includes('shift')) parts.push('Shift');
        parts.push(key.toUpperCase());
        return parts.join(' + ');
    }
    
    /**
     * 从显示文本解析快捷键配置
     * @param {string} display - 显示文本（如 "Ctrl + Alt + A"）
     * @returns {Object|null} 快捷键配置对象或 null
     */
    static parseHotkeyDisplay(display) {
        if (!display || typeof display !== 'string') {
            return null;
        }
        
        const parts = display.split('+').map(p => p.trim().toLowerCase());
        if (parts.length === 0) {
            return null;
        }
        
        const modifiers = [];
        let key = '';
        
        for (const part of parts) {
            if (part === 'ctrl') {
                modifiers.push('ctrl');
            } else if (part === 'alt') {
                modifiers.push('alt');
            } else if (part === 'shift') {
                modifiers.push('shift');
            } else if (/^[a-z0-9]$/.test(part)) {
                key = part;
            }
        }
        
        if (!key || modifiers.length === 0) {
            return null;
        }
        
        return {
            key: key,
            modifiers: modifiers
        };
    }
    
    /**
     * 从旧的 JSON 格式迁移
     * @param {string} jsonStr - JSON 字符串
     * @returns {string} 显示文本格式
     */
    static migrateFromJSON(jsonStr) {
        try {
            const config = JSON.parse(jsonStr);
            if (config.key && Array.isArray(config.modifiers)) {
                return this.formatHotkeyDisplay(config.modifiers, config.key);
            }
        } catch (e) {
            // 如果已经是显示文本格式，直接返回
            if (typeof jsonStr === 'string' && jsonStr.includes('+')) {
                return jsonStr;
            }
        }
        return 'Alt + A'; // 默认值
    }
}

