# -*- coding: utf-8 -*-
"""
Doubao Vision API节点
调用Doubao视觉模型API进行图像理解和分析
仅支持火山引擎平台
"""

import os
import base64
from io import BytesIO
from typing import Optional, List, Dict, Any
from pathlib import Path
import numpy as np
from PIL import Image

# 定义服务平台配置
SERVICE_PLATFORMS = {
    "火山引擎": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key_env": "VOLC_API_KEY",
        "config_key": "volcengine_api_key",
        "platform_key": "volcengine",
        "models": [
            "Doubao-Seed-1.6", 
            "Doubao-Seed-1.6-thinking", 
            "Doubao-Seed-1.6-flash", 
            "Doubao-Seed-1.6-vision", 
            "Doubao-1.5-vision-pro", 
            "Doubao-1.5-vision-lite", 
            "Doubao-1.5-thinking-vision-pro",
            "Doubao-1.5-UI-TARS",
            "Doubao-Seed-Translation"
        ],
        "model_mapping": {
            "Doubao-Seed-1.6": "doubao-seed-1-6-250615",
            "Doubao-Seed-1.6-thinking": "doubao-seed-1-6-thinking-250715",
            "Doubao-Seed-1.6-flash": "doubao-seed-1-6-flash-250828",
            "Doubao-Seed-1.6-vision": "doubao-seed-1-6-vision-250815",
            "Doubao-1.5-vision-pro": "doubao-1.5-vision-pro-250328",
            "Doubao-1.5-vision-lite": "doubao-1.5-vision-lite-250315",
            "Doubao-1.5-thinking-vision-pro": "doubao-1-5-thinking-vision-pro-250428",
            "Doubao-1.5-UI-TARS": "doubao-1-5-ui-tars-250428",
            "Doubao-Seed-Translation": "doubao-seed-translation-250915"
        }
    }
}

# 所有支持的Doubao视觉模型
ALL_DOUBAO_VISION_MODELS = [
    "Doubao-Seed-1.6", 
    "Doubao-Seed-1.6-thinking", 
    "Doubao-Seed-1.6-flash", 
    "Doubao-Seed-1.6-vision", 
    "Doubao-1.5-vision-pro", 
    "Doubao-1.5-vision-lite", 
    "Doubao-1.5-thinking-vision-pro",
    "Doubao-1.5-UI-TARS",
    "Doubao-Seed-Translation"
]


class DoubaoVisionAPI:
    """
    Doubao视觉模型API调用节点
    支持图像理解和视觉问答
    """
    
    # 类属性
    SERVICE_PLATFORMS = SERVICE_PLATFORMS
    ALL_DOUBAO_VISION_MODELS = ALL_DOUBAO_VISION_MODELS
    
    def __init__(self):
        """初始化节点"""
        self.conversation_history = {}
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "输入要分析的图像"
                }),
                "text_input": ("STRING", {
                    "default": "请详细分析这张图片的内容和细节。",
                    "multiline": True,
                    "tooltip": "输入关于图像的问题或指令"
                }),
                "platform": (["火山引擎"], {
                    "default": "火山引擎",
                    "tooltip": "Doubao视觉API服务提供商（仅支持火山引擎）"
                }),
                "model": (cls.ALL_DOUBAO_VISION_MODELS, {
                    "default": "Doubao-1.5-vision-pro",
                    "tooltip": "选择要使用的Doubao视觉模型\n📋 模型说明：\n🔸 Doubao-Seed-1.6：最新种子模型\n🔸 Doubao-Seed-1.6-thinking：思维链推理\n🔸 Doubao-Seed-1.6-flash：快速响应\n🔸 Doubao-Seed-1.6-vision：专业视觉\n🔸 Doubao-1.5-vision-pro：高质量视觉分析\n🔸 Doubao-1.5-vision-lite：轻量级视觉\n🔸 Doubao-1.5-thinking-vision-pro：思维链视觉专业版\n🔸 Doubao-1.5-UI-TARS：UI界面分析专用\n🔸 Doubao-Seed-Translation：翻译专用模型"
                }),
                "max_tokens": ("INT", {
                    "default": 2048,
                    "min": 1,
                    "max": 8192,
                    "step": 1,
                    "tooltip": "模型生成文本时最多能使用的token数量"
                }),
                "history": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 10,
                    "step": 1,
                    "tooltip": "保持的历史对话轮数（视觉模型建议较少轮数）"
                }),
            },
            "optional": {
                "temperature": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "tooltip": "控制生成文本的随机性，视觉任务建议较低值"
                }),
                "top_p": ("FLOAT", {
                    "default": 0.8,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "tooltip": "控制生成文本的多样性"
                }),
                "image_quality": (["auto", "low", "high"], {
                    "default": "auto",
                    "tooltip": "图像质量设置：auto自动，low低质量快速，high高质量精确"
                }),
                "clear_history": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否清除历史对话记录"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("analysis_result", "conversation_info", "total_tokens")
    FUNCTION = "analyze_image"
    CATEGORY = "🎨QING/API调用"
    OUTPUT_NODE = False

    def _get_api_key(self, platform_config: Dict[str, str]) -> str:
        """获取API密钥（优化版本 - 减少延迟）"""
        config_key = platform_config["config_key"]
        
        # 缓存导入的模块以避免重复导入
        if not hasattr(self, '_config_modules_loaded'):
            self._config_server = None
            self._settings_approach = None
            try:
                from .config_server import get_api_key_by_platform
                self._config_server = get_api_key_by_platform
            except ImportError:
                try:
                    from .settings_approach import get_qing_api_key_improved
                    self._settings_approach = get_qing_api_key_improved
                except ImportError:
                    pass
            self._config_modules_loaded = True

        # 策略1: 从环境变量获取（最快）
        api_key = os.getenv(platform_config["api_key_env"], '')
        if api_key:
            return api_key

        # 策略2: 从🎨QING配置系统获取
        if self._config_server:
            try:
                api_key = self._config_server(config_key)
                if api_key:
                    return api_key
            except Exception:
                pass
        
        if self._settings_approach:
            try:
                api_key = self._settings_approach(config_key)
                if api_key:
                    return api_key
            except Exception:
                pass

        # 策略3: 从临时文件获取（最慢，最后尝试）
        try:
            import tempfile
            temp_file = Path(tempfile.gettempdir()) / f"qing_{config_key}_temp.txt"
            if temp_file.exists():
                with open(temp_file, 'r', encoding='utf-8') as f:
                    temp_key = f.read().strip()
                    if temp_key:
                        return temp_key
        except Exception:
            pass

        return ""

    def _image_to_base64(self, image, quality: str = "auto") -> str:
        """将ComfyUI图像转换为base64格式"""
        try:
            # 将PyTorch tensor转换为numpy array
            if hasattr(image, 'cpu'):
                image = image.cpu().numpy()
            elif hasattr(image, 'numpy'):
                image = image.numpy()
            elif not isinstance(image, np.ndarray):
                image = np.array(image)
            
            # ComfyUI图像格式转换 (batch, height, width, channels) -> PIL Image
            if len(image.shape) == 4:
                image = image[0]  # 取第一张图片
            
            # 确保值在0-255范围内
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            else:
                image = image.astype(np.uint8)
            
            # 转换为PIL Image
            pil_image = Image.fromarray(image)
            
            # 根据质量设置调整图像（优化重采样算法）
            if quality == "low":
                # 低质量：缩小图像，使用快速重采样
                pil_image.thumbnail((512, 512), Image.Resampling.BILINEAR)
                format_type = "JPEG"
                encode_params = {"quality": 70, "optimize": True}
            elif quality == "high":
                # 高质量：保持原尺寸，使用高质量重采样
                max_size = 2048
                if max(pil_image.size) > max_size:
                    pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                format_type = "JPEG"  # 改为JPEG以减少文件大小
                encode_params = {"quality": 95, "optimize": True}
            else:  # auto
                # 自动：平衡质量和速度
                if max(pil_image.size) > 1024:
                    pil_image.thumbnail((1024, 1024), Image.Resampling.BILINEAR)
                format_type = "JPEG"
                encode_params = {"quality": 85, "optimize": True}
            
            # 编码为base64
            buffer = BytesIO()
            pil_image.save(buffer, format=format_type, **encode_params)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/{format_type.lower()};base64,{image_base64}"
            
        except Exception as e:
            raise Exception(f"图像转换失败: {str(e)}")

    def analyze_image(self, image, text_input: str, platform: str, model: str, 
                     max_tokens: int, history: int,
                     temperature: Optional[float] = 0.3, top_p: Optional[float] = 0.8,
                     image_quality: Optional[str] = "auto", clear_history: Optional[bool] = False):
        """
        调用Doubao Vision API分析图像

        Args:
            image: 输入图像
            text_input: 输入文本
            platform: 服务平台
            model: 模型名称
            max_tokens: 最大token数
            history: 保持的历史轮数
            temperature: 温度参数
            top_p: top_p参数
            image_quality: 图像质量
            clear_history: 是否清除历史

        Returns:
            tuple: (分析结果, 对话信息, token数量)
        """
        try:
            # 清除历史记录
            if clear_history:
                self.conversation_history.clear()

            # 获取平台配置
            platform_config = self.SERVICE_PLATFORMS.get(platform)
            if not platform_config:
                return (f"错误：不支持的平台 '{platform}'", "错误状态", 0)

            # 验证模型是否被当前平台支持
            supported_models = platform_config.get("models", [])
            if model not in supported_models:
                available_models = ", ".join(supported_models)
                return (f"❌ 模型兼容性错误\n\n🌋 平台 '{platform}' 不支持模型 '{model}'\n\n✅ 该平台支持的模型：\n{available_models}", "模型不兼容", 0)

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
            conversation_key = f"{platform_key}_{model}_vision"
            if conversation_key not in self.conversation_history:
                self.conversation_history[conversation_key] = []

            current_history = self.conversation_history[conversation_key]

            # 转换图像为base64
            image_base64 = self._image_to_base64(image, image_quality)

            # 构建消息内容
            message_content = [
                {
                    "type": "text",
                    "text": text_input
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_base64,
                        "detail": image_quality if image_quality != "auto" else "auto"
                    }
                }
            ]

            # 添加当前输入到历史
            current_history.append({"role": "user", "content": message_content})

            # 限制历史长度（视觉模型建议更少的历史）
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
            conversation_info = f"平台: {platform} | 模型: {model} | 图像质量: {image_quality} | 历史轮数: {len(current_history)//2} | 总Tokens: {total_tokens} (输入: {prompt_tokens}, 输出: {completion_tokens}, 限制: {max_tokens})"

            return (reply, conversation_info, token_count)

        except Exception as e:
            error_message = f"Doubao Vision API调用失败 ({platform}): {str(e)}"
            return (error_message, "错误状态", 0)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # 每次都重新执行，因为是API调用
        return float("nan")


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "DoubaoVisionAPI": DoubaoVisionAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DoubaoVisionAPI": "Doubao_视觉丨API"
}
