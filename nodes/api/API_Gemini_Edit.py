# -*- coding: utf-8 -*-
"""
Gemini Edit API节点 - 基于通用框架
调用Gemini编辑模型API进行图像编辑和生成
支持Google AI Studio平台
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseVisionAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class GoogleAIStudioGeminiEditAdapter(BasePlatformAdapter):
    """Google AI Studio Gemini编辑平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # Gemini编辑模型不支持重复惩罚参数，但保持兼容性
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        if repetition_penalty != 1.0:
            # Gemini使用不同的参数名，转换为temperature调整
            current_temp = params.get('temperature', 0.4)
            adjusted_temp = max(0.0, min(2.0, current_temp + (repetition_penalty - 1.0) * 0.3))
            params['temperature'] = adjusted_temp
        
        # 应用token限制
        params["max_tokens"] = self.apply_token_limit(params["max_tokens"])
        
        # 注意：image_quality 参数仅用于内部逻辑，不传递给OpenAI兼容API
        # OpenAI兼容接口不支持 image_quality 参数
        image_quality = kwargs.get('image_quality', 'auto')
        # 可以在这里根据 image_quality 调整其他参数，但不添加到 params 中
        
        # 根据文档，Gemini API通过OpenAI兼容层支持思考功能
        # 可以添加reasoning_effort参数（low, medium, high）
        reasoning_effort = kwargs.get('reasoning_effort', None)
        if reasoning_effort and reasoning_effort in ['low', 'medium', 'high']:
            params["reasoning_effort"] = reasoning_effort
        
        return params


class GeminiEditAPI(BaseVisionAPINode):
    """
    Gemini编辑模型API调用节点 - 框架版本
    支持Google AI Studio平台的Gemini编辑模型调用
    """
    
    # 节点信息
    NODE_NAME = "GeminiEditAPI"
    DISPLAY_NAME = "Gemini_编辑丨API"
    
    # 返回类型
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    
    # 返回名称
    RETURN_NAMES = ("edited_image", "conversation_info", "total_tokens")
    
    # Gemini编辑模型列表
    GEMINI_EDIT_MODELS = [
        "gemini-2.5-flash-image-preview"
    ]
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "Google AI Studio": PlatformConfig(
            name="Google AI Studio",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key_env="GEMINI_API_KEY",
            config_key="gemini_api_key",
            platform_key="google_ai_studio_edit",
            models=GEMINI_EDIT_MODELS,
            model_mapping={
                "gemini-2.5-flash-image-preview": "gemini-2.5-flash-image-preview"
            },
            max_tokens_limit=4096,  # 图像编辑模型通常不需要过多token
            supports_frequency_penalty=False,
            # 针对图像编辑模型的特殊配置，使用custom_params存储
            custom_params={
                "supports_image_editing": True,
                "supports_multi_image": True,
                "max_images": 3
            }
        )
    }
    
    # 平台适配器映射
    PLATFORM_ADAPTERS = {
        "Google AI Studio": GoogleAIStudioGeminiEditAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加Gemini编辑特定的提示信息和多图像输入"""
        # 由于父类BaseVisionAPINode的get_input_types会访问cls.PLATFORM_CONFIGS
        # 而在类定义时这可能还未完全初始化，我们直接构建输入类型
        
        base_types = {
            "required": {
                "text_input": ("STRING", {
                    "default": "请编辑这张图片。",
                    "multiline": True,
                    "tooltip": "输入图像编辑指令，描述你想要如何修改或生成图像。建议使用简洁明确的指令，如'将背景改为蓝天'、'转换为水彩画风格'等"
                }),
                "platform": (list(cls.PLATFORM_CONFIGS.keys()), {
                    "default": list(cls.PLATFORM_CONFIGS.keys())[0] if cls.PLATFORM_CONFIGS else "Google AI Studio",
                    "tooltip": "选择Gemini编辑模型的服务平台"
                }),
                "model": (tuple(cls.GEMINI_EDIT_MODELS), {
                    "default": cls.GEMINI_EDIT_MODELS[0] if cls.GEMINI_EDIT_MODELS else "gemini-2.5-flash-image-preview",
                    "tooltip": """选择要使用的Gemini编辑模型
📋 gemini-2.5-flash-image-preview特点：
🎨 专业图像编辑：支持精确的图像修改和生成
🖼️ 多图支持：可同时处理最多3张图像
🎭 风格转换：擅长艺术风格、滤镜效果转换
✨ 内容编辑：智能添加、删除或修改图像元素
⚡ 快速响应：针对图像编辑任务优化的高效模型
💡 最佳实践：使用较低temperature(0.2)确保编辑一致性"""
                }),
                "max_tokens": ("INT", {
                    "default": 2048,
                    "min": 1,
                    "max": 4096,
                    "step": 1,
                    "tooltip": "模型生成文本时最多能使用的token数量（1-4096，图像编辑优化）"
                }),
                "history": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 18,
                    "step": 1,
                    "tooltip": "保持的历史对话轮数（1-18轮，编辑任务建议4轮）"
                }),
            },
            "optional": {
                "temperature": ("FLOAT", {
                    "default": 0.2,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01,
                    "tooltip": "控制生成结果的随机性，越高越随机（0.0-2.0，编辑建议0.2确保一致性）"
                }),
                "top_p": ("FLOAT", {
                    "default": 0.8,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "tooltip": "控制生成结果的多样性（0.0-1.0）"
                }),
                "image_quality": (["auto", "low", "high"], {
                    "default": "high",
                    "tooltip": "图像处理质量：auto(自动选择), low(低质量，速度快), high(高质量，精度高)"
                }),
                "reasoning_effort": (["none", "low", "medium", "high"], {
                    "default": "medium",
                    "tooltip": "推理努力程度：none(无), low(低), medium(中等), high(高) - 影响编辑质量和处理时间"
                }),
                "clear_history": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否清除历史对话记录"
                })
            }
        }
        
        # 添加三个图像输入端口
        base_types["required"]["image1"] = ("IMAGE", {
            "tooltip": "输入要编辑的第一张图像（必需）"
        })
        
        base_types["optional"]["image2"] = ("IMAGE", {
            "tooltip": "输入要编辑的第二张图像（可选）"
        })
        
        base_types["optional"]["image3"] = ("IMAGE", {
            "tooltip": "输入要编辑的第三张图像（可选）"
        })
        
        return base_types
    
    def generate_response(self, text_input: str, image1, image2=None, image3=None, platform: str = "Google AI Studio", 
                         model: str = "gemini-2.5-flash-image-preview", max_tokens: int = 2048, 
                         history: int = 4, temperature: float = 0.2, top_p: float = 0.8,
                         image_quality: str = "high", reasoning_effort: str = "medium",
                         clear_history: bool = False, **kwargs) -> tuple:
        """生成响应，支持多图像输入"""
        
        # 收集所有非空的图像
        images = []
        if image1 is not None:
            images.append(image1)
        if image2 is not None:
            images.append(image2)
        if image3 is not None:
            images.append(image3)
        
        # 至少需要一张图像
        if not images:
            raise ValueError("至少需要提供一张图像进行编辑")
        
        try:
            # 清除历史记录
            if clear_history:
                self.conversation_manager.clear_all()
            
            # 验证输入参数
            is_valid, error_msg = self._validate_inputs(platform, model)
            if not is_valid:
                return (None, error_msg, 0)
            
            # 获取平台配置和适配器
            platform_config = self.PLATFORM_CONFIGS[platform]
            adapter = self._get_platform_adapter(platform)
            
            # 获取API密钥
            api_key = self.api_key_manager.get_api_key(platform_config)
            if not api_key:
                error_msg = f"""错误：未提供{platform}的API密钥。请尝试以下方法之一：

1. 设置环境变量：{platform_config.api_key_env}
2. 在🎨QING设置中配置API密钥
3. 使用临时文件设置密钥

获取Gemini API密钥：https://aistudio.google.com/app/apikey

请配置后重试。"""
                return (None, error_msg, 0)
            
            # 获取或创建客户端
            client = self.client_manager.get_or_create_client(platform_config, api_key)
            
            # 管理对话历史
            conversation_key = self.conversation_manager.get_conversation_key(
                platform_config.platform_key, model
            )
            
            # 准备多图像消息
            messages = self._prepare_edit_messages(images, text_input, conversation_key)
            
            # 限制历史长度
            self.conversation_manager.limit_history(conversation_key, history)
            
            # 准备基础API参数
            base_params = self._prepare_base_params(
                adapter.get_api_model_name(model),
                messages,
                adapter.apply_token_limit(max_tokens),
                temperature,
                top_p
            )
            
            # 使用适配器准备最终参数（包含图像质量和reasoning_effort）
            api_params = adapter.prepare_api_params(
                base_params, 
                model=model, 
                image_quality=image_quality,
                reasoning_effort=reasoning_effort,
                additional_images=images[1:] if len(images) > 1 else []
            )
            
            # 调用API
            response = client.chat.completions.create(**api_params)
            
            # 处理响应
            reply, usage_info = self._handle_api_response(response, conversation_key)
            
            # 对于图像编辑API，Gemini返回的是实际图像数据
            # 解析返回的图像（通常在response中或作为URL）
            edited_image = self._parse_edited_image(response, reply)
            
            # 生成对话信息，包含reasoning_effort
            reasoning_info = f" | 推理: {reasoning_effort}" if reasoning_effort != "none" else ""
            conversation_info = f"平台: {platform} | 模型: {model} | 历史轮数: {len(messages)//2} | 图像质量: {image_quality}{reasoning_info} | 总Tokens: {usage_info['total_tokens']} (输入: {usage_info['prompt_tokens']}, 输出: {usage_info['completion_tokens']}, 限制: {max_tokens})"
            
            return (edited_image, conversation_info, usage_info['total_tokens'])
            
        except Exception as e:
            error_message = f"{self.NODE_NAME} API调用失败 ({platform}): {str(e)}"
            return (None, error_message, 0)
    
    def _prepare_edit_messages(self, images: list, text_input: str, conversation_key: str) -> list:
        """准备图像编辑模型的消息格式，支持多图像"""
        content_parts = []
        
        # 添加所有图像
        for i, image in enumerate(images):
            image_base64 = self._image_to_base64(image)
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": image_base64
                }
            })
        
        # 添加文本指令
        content_parts.append({
            "type": "text",
            "text": text_input
        })
        
        # 创建用户消息
        user_message = {
            "role": "user",
            "content": content_parts
        }
        
        # 添加到对话历史
        self.conversation_manager.add_message(conversation_key, "user", user_message["content"])
        
        return self.conversation_manager.get_history(conversation_key)
    
    def _parse_edited_image(self, response, reply: str):
        """
        解析Gemini图像编辑API返回的实际图像数据
        gemini-2.5-flash-image-preview模型返回的是实际图像
        """
        import torch
        import numpy as np
        from PIL import Image
        import base64
        from io import BytesIO
        import re
        
        try:
            # 方法1: 尝试从response.choices中提取图像URL或base64数据
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                
                # 检查是否有图像内容
                if hasattr(choice.message, 'content'):
                    content = choice.message.content
                    
                    # 如果content是列表（多模态响应）
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict):
                                # 检查图像URL
                                if item.get('type') == 'image_url':
                                    image_url = item.get('image_url', {}).get('url', '')
                                    if image_url:
                                        return self._load_image_from_url_or_base64(image_url)
                                
                                # 检查直接的图像数据
                                if 'image' in item or 'image_data' in item:
                                    image_data = item.get('image') or item.get('image_data')
                                    return self._load_image_from_base64(image_data)
                    
                    # 如果content是字符串，尝试查找base64图像数据
                    elif isinstance(content, str):
                        # 查找base64图像数据模式
                        base64_pattern = r'data:image/[^;]+;base64,([^"\s]+)'
                        matches = re.findall(base64_pattern, content)
                        if matches:
                            return self._load_image_from_base64(matches[0])
                        
                        # 尝试直接作为base64解码
                        if len(content) > 100 and not content.startswith('http'):
                            try:
                                return self._load_image_from_base64(content)
                            except:
                                pass
            
            # 方法2: 检查response中是否有直接的图像字段
            if hasattr(response, 'data'):
                if isinstance(response.data, list):
                    for item in response.data:
                        if hasattr(item, 'url'):
                            return self._load_image_from_url_or_base64(item.url)
                        if hasattr(item, 'b64_json'):
                            return self._load_image_from_base64(item.b64_json)
            
            # 方法3: 如果都失败，返回提示图像
            return self._create_error_image("无法解析图像数据，请检查API响应格式")
            
        except Exception as e:
            return self._create_error_image(f"图像解析失败: {str(e)}")
    
    def _load_image_from_url_or_base64(self, data: str):
        """
        从URL或base64字符串加载图像
        """
        import torch
        import numpy as np
        from PIL import Image
        import base64
        from io import BytesIO
        import requests
        
        try:
            # 如果是base64数据URI
            if data.startswith('data:image'):
                # 提取base64部分
                base64_data = data.split(',', 1)[1] if ',' in data else data
                return self._load_image_from_base64(base64_data)
            
            # 如果是HTTP(S) URL
            elif data.startswith('http://') or data.startswith('https://'):
                response = requests.get(data, timeout=30)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                return self._pil_to_tensor(img)
            
            # 否则尝试作为base64
            else:
                return self._load_image_from_base64(data)
                
        except Exception as e:
            raise ValueError(f"加载图像失败: {str(e)}")
    
    def _load_image_from_base64(self, base64_str: str):
        """
        从base64字符串加载图像
        """
        import torch
        import numpy as np
        from PIL import Image
        import base64
        from io import BytesIO
        
        try:
            # 清理base64字符串
            base64_str = base64_str.strip().replace('\n', '').replace('\r', '')
            
            # 解码base64
            image_data = base64.b64decode(base64_str)
            
            # 加载图像
            img = Image.open(BytesIO(image_data))
            
            return self._pil_to_tensor(img)
            
        except Exception as e:
            raise ValueError(f"Base64解码失败: {str(e)}")
    
    def _pil_to_tensor(self, img: 'Image'):
        """
        将PIL图像转换为ComfyUI tensor格式
        """
        import torch
        import numpy as np
        
        # 转换为RGB（如果是RGBA或其他格式）
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 转换为numpy数组并归一化到0-1
        img_np = np.array(img).astype(np.float32) / 255.0
        
        # 转换为torch tensor，添加batch维度 [1, H, W, C]
        img_tensor = torch.from_numpy(img_np)[None,]
        
        return img_tensor
    
    def _create_error_image(self, error_message: str):
        """
        创建一个错误提示图像
        """
        import torch
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        try:
            # 创建512x512的浅红色背景图像
            img = Image.new('RGB', (512, 512), color=(255, 230, 230))
            draw = ImageDraw.Draw(img)
            
            # 尝试使用字体
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # 绘制错误消息
            lines = ["⚠️ 图像解析错误", "", error_message[:50]]
            y_offset = 200
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (512 - text_width) // 2
                draw.text((x, y_offset), line, fill='red', font=font)
                y_offset += 30
            
            # 转换为tensor
            img_np = np.array(img).astype(np.float32) / 255.0
            return torch.from_numpy(img_np)[None,]
            
        except Exception:
            # 最后的备用方案：纯色图像
            img_np = np.full((512, 512, 3), 0.9, dtype=np.float32)
            return torch.from_numpy(img_np)[None,]


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "GeminiEditAPI": GeminiEditAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GeminiEditAPI": "Gemini_编辑丨API"
}
