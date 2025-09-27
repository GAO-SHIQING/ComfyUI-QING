# -*- coding: utf-8 -*-
"""
DeepSeek Language API节点
调用DeepSeek语言模型API进行文本推理
支持多平台：火山引擎、阿里云百炼、硅基流动、腾讯云
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path

# 定义服务平台配置
SERVICE_PLATFORMS = {
    "火山引擎": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key_env": "VOLCENGINE_API_KEY",
        "config_key": "volcengine_api_key",
        "platform_key": "volcengine",
        "models": [
            "DeepSeek-V3.1",
            "DeepSeek-R1",
            "DeepSeek-V3"
        ],
        "model_mapping": {
            "DeepSeek-V3.1": "deepseek-v3-1-250821",
            "DeepSeek-R1": "deepseek-r1-250528",
            "DeepSeek-V3": "deepseek-v3-250324"
        }
    },
    "阿里云百炼": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY", 
        "config_key": "dashscope_api_key",
        "platform_key": "dashscope",
        "models": [
            "DeepSeek-V3.1",
            "DeepSeek-R1",
            "DeepSeek-V3"
        ],
        "model_mapping": {
            "DeepSeek-V3.1": "deepseek-v3.1",        
            "DeepSeek-R1": "deepseek-r1-0528",       
            "DeepSeek-V3": "deepseek-v3"             
        }
    },
    "硅基流动": {
        "base_url": "https://api.siliconflow.cn/v1",
        "api_key_env": "SILICONFLOW_API_KEY",
        "config_key": "siliconflow_api_key",
        "platform_key": "siliconflow",
        "models": [
            "DeepSeek-V3.1",
            "DeepSeek-R1",
            "DeepSeek-V3"
        ],
        "model_mapping": {
            "DeepSeek-V3.1": "deepseek-ai/DeepSeek-V3.1",
            "DeepSeek-R1": "deepseek-ai/DeepSeek-R1",
            "DeepSeek-V3": "deepseek-ai/DeepSeek-V3"
        }
    },
    "腾讯云": {
        "base_url": "https://api.lkeap.cloud.tencent.com/v1",
        "api_key_env": "TENCENT_LKEAP_API_KEY",
        "config_key": "tencent_lkeap_api_key",
        "platform_key": "tencent",
        "models": [
            "DeepSeek-V3.1",
            "DeepSeek-R1",
            "DeepSeek-V3"
        ],
        "model_mapping": {
            "DeepSeek-V3.1": "deepseek-v3.1",
            "DeepSeek-R1": "deepseek-r1-0528",
            "DeepSeek-V3": "deepseek-v3-0324"
        }
    }
}

# 支持的DeepSeek模型（按照需求顺序）
DEEPSEEK_MODELS = [
    "DeepSeek-V3.1",
    "DeepSeek-R1", 
    "DeepSeek-V3"
]


class DeepSeekLanguageAPI:
    """
    DeepSeek语言模型API调用节点
    支持多个服务平台的DeepSeek模型调用
    """
    
    # 类属性
    SERVICE_PLATFORMS = SERVICE_PLATFORMS
    DEEPSEEK_MODELS = DEEPSEEK_MODELS
    
    def __init__(self):
        """初始化节点"""
        self.conversation_history = {}
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_input": ("STRING", {
                    "default": "请进行深度推理分析，提供详细的思考过程和结论。",
                    "multiline": True,
                    "tooltip": "输入要发送给DeepSeek模型的文本内容，DeepSeek擅长复杂推理和深度分析"
                }),
                "platform": (list(cls.SERVICE_PLATFORMS.keys()), {
                    "default": "硅基流动",
                    "tooltip": "选择DeepSeek API服务提供商"
                }),
                "model": (cls.DEEPSEEK_MODELS, {
                    "default": "DeepSeek-V3.1",
                    "tooltip": "选择要使用的DeepSeek模型\n📋 模型特点：\n🔸 DeepSeek-V3.1：最新版本，推理能力最强，适合复杂分析\n🔸 DeepSeek-R1：推理专用模型，逻辑思维强，适合数学和编程\n🔸 DeepSeek-V3：稳定版本，平衡性能，适合通用任务\n💡 推荐使用V3.1或R1获得最佳推理效果"
                }),
                "max_tokens": ("INT", {
                    "default": 6144,
                    "min": 1,
                    "max": 32768,
                    "step": 1,
                    "tooltip": "模型生成文本时最多能使用的token数量，DeepSeek推理模型建议较高值"
                }),
                "history": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 25,
                    "step": 1,
                    "tooltip": "保持的历史对话轮数，DeepSeek模型支持超长上下文，适合复杂推理链"
                }),
            },
            "optional": {
                "temperature": ("FLOAT", {
                    "default": 0.6,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "控制生成文本的随机性，DeepSeek推理模型建议0.4-0.8以保证逻辑严谨性"
                }),
                "top_p": ("FLOAT", {
                    "default": 0.92,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "tooltip": "控制生成文本的多样性，DeepSeek模型建议高值以支持创造性推理"
                }),
                "clear_history": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否清除历史对话记录"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("generated_text", "conversation_info", "total_tokens")
    FUNCTION = "generate_text"
    CATEGORY = "🎨QING/API调用"
    OUTPUT_NODE = False
    
    def _get_api_key(self, platform_config: Dict[str, str]) -> str:
        """获取API密钥（支持多平台）"""
        final_api_key = ""
        config_key = platform_config["config_key"]

        # 策略1: 从环境变量获取
        final_api_key = os.getenv(platform_config["api_key_env"], '')

        # 策略2: 从🎨QING配置系统获取（支持多平台）
        if not final_api_key:
            try:
                from .config_server import get_api_key_by_platform
                final_api_key = get_api_key_by_platform(config_key)
            except ImportError:
                try:
                    # 尝试从新的配置管理器获取
                    from .settings_approach import get_qing_api_key_improved
                    final_api_key = get_qing_api_key_improved(config_key)
                except ImportError:
                    pass

        # 策略3: 回退到旧版API密钥服务（仅支持GLM）
        if not final_api_key and config_key in ["glm_api_key", "zhipuai_api_key"]:
            try:
                from .api_key_server import get_qing_api_key
                final_api_key = get_qing_api_key()
            except ImportError:
                pass

        # 策略4: 从临时文件获取（兼容性）
        if not final_api_key:
            try:
                import tempfile
                temp_file = Path(tempfile.gettempdir()) / f"qing_{config_key}_temp.txt"
                if temp_file.exists():
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        temp_key = f.read().strip()
                        if temp_key:
                            final_api_key = temp_key
            except Exception:
                pass

        return final_api_key
    
    def generate_text(self, text_input: str, platform: str, model: str, max_tokens: int, history: int,
                     temperature: Optional[float] = 0.7, top_p: Optional[float] = 0.9, 
                     clear_history: Optional[bool] = False):
        """
        调用DeepSeek API生成文本
        
        Args:
            text_input: 输入文本
            platform: 服务平台
            model: 模型名称
            max_tokens: 最大token数
            history: 保持的历史轮数
            temperature: 温度参数
            top_p: top_p参数
            clear_history: 是否清除历史
            
        Returns:
            tuple: (生成的文本,)
        """
        try:
            # 清除历史记录
            if clear_history:
                self.conversation_history.clear()
            
            # 获取平台配置
            platform_config = self.SERVICE_PLATFORMS.get(platform)
            if not platform_config:
                return (f"错误：不支持的平台 '{platform}'", "错误状态", 0)
            
            # 获取API密钥
            api_key = self._get_api_key(platform_config)
            if not api_key:
                error_msg = f"""错误：未提供{platform}的API密钥。请尝试以下方法之一：

1. 设置环境变量：{platform_config['api_key_env']}
2. 在🎨QING设置中配置API密钥
3. 使用临时文件设置密钥

请配置后重试。"""
                return (error_msg, "API密钥缺失", 0)
            
            # 导入openai库
            try:
                from openai import OpenAI
            except ImportError:
                return ("错误：未安装openai库。请运行：pip install openai", "依赖缺失", 0)
            
            # 初始化客户端
            client = OpenAI(
                base_url=platform_config["base_url"],
                api_key=api_key
            )
            
            # 获取对话历史 - 使用英文平台键避免编码问题
            platform_key = platform_config.get("platform_key", platform)
            conversation_key = f"{platform_key}_{model}"
            if conversation_key not in self.conversation_history:
                self.conversation_history[conversation_key] = []
            
            current_history = self.conversation_history[conversation_key]
            
            # 添加当前输入到历史
            current_history.append({"role": "user", "content": text_input})
            
            # 限制历史长度
            if len(current_history) > history * 2:
                current_history = current_history[-(history * 2):]
                self.conversation_history[conversation_key] = current_history
            
            # 根据平台获取对应的模型名称
            platform_model_mapping = platform_config.get("model_mapping", {})
            api_model_name = platform_model_mapping.get(model, model.lower())
            
            # 调用API
            response = client.chat.completions.create(
                model=api_model_name,
                messages=current_history,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            
            # 提取回复
            reply = response.choices[0].message.content
            
            # 添加回复到历史
            current_history.append({"role": "assistant", "content": reply})
            
            # 计算token使用情况
            if hasattr(response, 'usage') and response.usage:
                total_tokens = response.usage.total_tokens
                prompt_tokens = getattr(response.usage, 'prompt_tokens', 0)
                completion_tokens = getattr(response.usage, 'completion_tokens', 0)
                token_count = total_tokens
            else:
                total_tokens = completion_tokens = prompt_tokens = token_count = 0
            
            # 生成对话信息
            conversation_info = f"平台: {platform} | 模型: {model} | 历史轮数: {len(current_history)//2} | 总Tokens: {total_tokens} (输入: {prompt_tokens}, 输出: {completion_tokens}, 限制: {max_tokens})"
            
            return (reply, conversation_info, total_tokens)
            
        except Exception as e:
            error_message = f"DeepSeek API调用失败 ({platform}): {str(e)}"
            return (error_message, "错误状态", 0)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # 每次都重新执行，因为是API调用
        return float("nan")


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "DeepSeekLanguageAPI": DeepSeekLanguageAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DeepSeekLanguageAPI": "DeepSeek_语言丨API"
}