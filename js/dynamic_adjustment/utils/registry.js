/**
 * 节点配置注册工具
 */

import { KIMI_CONFIGS } from '../config/kimi.js';
import { DOUBAO_CONFIGS } from '../config/doubao.js';
import { GLM_CONFIGS } from '../config/glm.js';
import { DEEPSEEK_CONFIGS } from '../config/deepseek.js';
import { QWEN_CONFIGS } from '../config/qwen.js';
import { GEMINI_CONFIGS } from '../config/gemini.js';

/**
 * 合并所有节点配置
 * @returns {object} 合并后的节点配置对象
 */
export function buildNodeConfigurations() {
    return {
        ...KIMI_CONFIGS,
        ...DOUBAO_CONFIGS,
        ...GLM_CONFIGS,
        ...DEEPSEEK_CONFIGS,
        ...QWEN_CONFIGS,
        ...GEMINI_CONFIGS
    };
}

/**
 * 获取所有支持的节点列表
 * @param {object} configurations - 节点配置对象
 * @returns {string[]} 节点名称数组
 */
export function getSupportedNodes(configurations) {
    return Object.keys(configurations);
}

