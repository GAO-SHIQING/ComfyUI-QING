# -*- coding: utf-8 -*-
"""
通用API节点基础框架
为所有AI模型API节点提供统一的基础架构
支持多平台、多模型的统一管理
"""

import os
from typing import Optional, List, Dict, Any, Tuple, Type
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class APIType(Enum):
    """API类型枚举"""
    LANGUAGE = "language"
    VISION = "vision"
    MULTIMODAL = "multimodal"


@dataclass
class PlatformConfig:
    """平台配置数据类"""
    name: str
    base_url: str
    api_key_env: str
    config_key: str
    platform_key: str
    models: List[str]
    model_mapping: Dict[str, str]
    max_tokens_limit: Optional[int] = None
    supports_repetition_penalty: bool = False
    supports_frequency_penalty: bool = True
    supports_presence_penalty: bool = False
    custom_params: Dict[str, Any] = field(default_factory=dict)


class BasePlatformAdapter(ABC):
    """平台适配器抽象基类"""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
    
    @abstractmethod
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """准备API调用参数"""
        pass
    
    def validate_model(self, model: str) -> bool:
        """验证模型是否支持"""
        return model in self.config.models
    
    def get_api_model_name(self, model: str) -> str:
        """获取API调用时的模型名称"""
        return self.config.model_mapping.get(model, model.lower())
    
    def apply_token_limit(self, max_tokens: int) -> int:
        """应用平台token限制"""
        if self.config.max_tokens_limit:
            return min(max_tokens, self.config.max_tokens_limit)
        return max_tokens
    
    def handle_repetition_penalty(self, params: Dict[str, Any], repetition_penalty: float) -> Dict[str, Any]:
        """处理重复惩罚参数"""
        if repetition_penalty == 1.0:
            return params
            
        if self.config.supports_repetition_penalty:
            params["repetition_penalty"] = repetition_penalty
        elif self.config.supports_frequency_penalty:
            params["frequency_penalty"] = (repetition_penalty - 1.0) * 0.5
        
        return params
    
    def handle_image_quality(self, params: Dict[str, Any], image_quality: str) -> Dict[str, Any]:
        """处理图像质量参数（视觉节点专用）"""
        if image_quality != 'auto':
            params["image_quality"] = image_quality
        return params


class APIKeyManager:
    """API密钥管理器 - 通用版本"""
    
    @staticmethod
    def get_api_key(platform_config: PlatformConfig) -> str:
        """获取API密钥（支持多平台）"""
        final_api_key = ""
        config_key = platform_config.config_key

        # 策略1: 从环境变量获取
        final_api_key = os.getenv(platform_config.api_key_env, '')

        # 策略2: 从🎨QING配置系统获取（支持多平台）
        if not final_api_key:
            try:
                # 直接从settings_approach获取，避免复杂的导入链
                from .utils.settings_approach import get_qing_api_key_improved
                final_api_key = get_qing_api_key_improved(config_key)
            except ImportError:
                pass

        # 策略3: 从临时文件获取（兼容性）
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


class ConversationManager:
    """对话历史管理器 - 通用版本"""
    
    def __init__(self):
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    def get_conversation_key(self, platform_key: str, model: str, user_id: str = "default") -> str:
        """生成对话键"""
        return f"{platform_key}_{model}_{user_id}"
    
    def add_message(self, conversation_key: str, role: str, content: str):
        """添加消息到历史"""
        if conversation_key not in self.conversation_history:
            self.conversation_history[conversation_key] = []
        
        self.conversation_history[conversation_key].append({
            "role": role, 
            "content": content
        })
    
    def get_history(self, conversation_key: str) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.get(conversation_key, [])
    
    def limit_history(self, conversation_key: str, max_rounds: int):
        """限制历史长度"""
        if conversation_key in self.conversation_history:
            history = self.conversation_history[conversation_key]
            if len(history) > max_rounds * 2:
                self.conversation_history[conversation_key] = history[-(max_rounds * 2):]
    
    def clear_all(self):
        """清除所有历史"""
        self.conversation_history.clear()
    
    def clear_conversation(self, conversation_key: str):
        """清除特定对话历史"""
        if conversation_key in self.conversation_history:
            del self.conversation_history[conversation_key]


class ClientManager:
    """API客户端管理器 - 通用版本"""
    
    def __init__(self):
        self._clients = {}
    
    def get_or_create_client(self, platform_config: PlatformConfig, api_key: str):
        """获取或创建API客户端（带缓存）"""
        client_key = f"{platform_config.platform_key}_{api_key[:10]}"
        
        if client_key not in self._clients:
            try:
                from openai import OpenAI
                self._clients[client_key] = OpenAI(
                    base_url=platform_config.base_url,
                    api_key=api_key
                )
            except ImportError:
                raise ImportError("错误：未安装openai库。请运行：pip install openai")
        
        return self._clients[client_key]
    
    def clear_clients(self):
        """清除所有客户端缓存"""
        self._clients.clear()


class BaseAPINode(ABC):
    """
    API节点基类
    为所有AI模型API节点提供统一的基础功能
    """
    
    # 标记为基类，不应该被ComfyUI注册为节点
    _IS_BASE_CLASS = True
    
    # 子类需要定义的属性
    API_TYPE: APIType = APIType.LANGUAGE
    NODE_NAME: str = "BaseAPI"
    DISPLAY_NAME: str = "Base API"
    CATEGORY: str = "🎨QING/API调用"
    
    # 平台配置和适配器映射 - 子类需要重写
    PLATFORM_CONFIGS: Dict[str, PlatformConfig] = {}
    PLATFORM_ADAPTERS: Dict[str, Type[BasePlatformAdapter]] = {}
    
    def __init__(self):
        """初始化节点"""
        self.conversation_manager = ConversationManager()
        self.api_key_manager = APIKeyManager()
        self.client_manager = ClientManager()
    
    @classmethod
    def get_all_models(cls) -> List[str]:
        """获取所有支持的模型（类方法，避免实例化）"""
        models = []
        for config in cls.PLATFORM_CONFIGS.values():
            models.extend(config.models)
        return list(set(models))  # 去重
    
    @property
    def all_models(self) -> List[str]:
        """获取所有支持的模型（实例方法，向后兼容）"""
        return self.get_all_models()
    
    @classmethod
    @abstractmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """获取输入类型 - 子类必须实现"""
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        """ComfyUI标准接口"""
        return cls.get_input_types()
    
    def _validate_inputs(self, platform: str, model: str) -> Tuple[bool, str]:
        """验证输入参数"""
        # 验证平台
        if platform not in self.PLATFORM_CONFIGS:
            return False, f"错误：不支持的平台 '{platform}'"
        
        # 验证模型
        platform_config = self.PLATFORM_CONFIGS[platform]
        if model not in platform_config.models:
            available_models = ", ".join(platform_config.models)
            return False, f"❌ 模型兼容性错误\n\n平台 '{platform}' 不支持模型 '{model}'\n\n✅ 该平台支持的模型：\n{available_models}"
        
        return True, ""
    
    def _get_platform_adapter(self, platform: str) -> BasePlatformAdapter:
        """获取平台适配器"""
        platform_config = self.PLATFORM_CONFIGS[platform]
        adapter_class = self.PLATFORM_ADAPTERS[platform]
        return adapter_class(platform_config)
    
    def _prepare_base_params(self, model: str, messages: List[Dict[str, str]], 
                           max_tokens: int, temperature: float, top_p: float) -> Dict[str, Any]:
        """准备基础API参数"""
        return {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
    
    def _handle_api_response(self, response, conversation_key: str) -> Tuple[str, Dict[str, Any]]:
        """处理API响应"""
        # 提取回复
        reply = response.choices[0].message.content
        
        # 添加助手回复到历史
        self.conversation_manager.add_message(conversation_key, "assistant", reply)
        
        # 计算token使用情况
        usage_info = {}
        if hasattr(response, 'usage') and response.usage:
            usage_info = {
                'total_tokens': response.usage.total_tokens,
                'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
                'completion_tokens': getattr(response.usage, 'completion_tokens', 0)
            }
        else:
            usage_info = {'total_tokens': 0, 'prompt_tokens': 0, 'completion_tokens': 0}
        
        return reply, usage_info
    
    @abstractmethod
    def generate_response(self, **kwargs) -> Tuple[str, str, int]:
        """生成响应 - 子类必须实现"""
        pass
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """ComfyUI缓存控制"""
        return float("nan")


class BaseLanguageAPINode(BaseAPINode):
    """
    语言模型API节点基类
    为语言模型提供标准的输入输出接口
    """
    
    # 标记为基类，不应该被ComfyUI注册为节点
    _IS_BASE_CLASS = True
    
    API_TYPE = APIType.LANGUAGE
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """语言模型的标准输入类型"""
        return {
            "required": {
                "text_input": ("STRING", {
                    "default": "请帮我分析一下这个问题，并提供详细的解决方案。",
                    "multiline": True,
                    "tooltip": "输入要发送给AI模型的文本内容"
                }),
                "platform": (list(cls.PLATFORM_CONFIGS.keys()), {
                    "default": list(cls.PLATFORM_CONFIGS.keys())[0] if cls.PLATFORM_CONFIGS else "未配置",
                    "tooltip": "选择API服务提供商"
                }),
                "model": (cls.get_all_models(), {
                    "default": cls.get_all_models()[0] if cls.get_all_models() else "未配置",
                    "tooltip": "选择要使用的AI模型"
                }),
                "max_tokens": ("INT", {
                    "default": 4096,
                    "min": 1,
                    "max": 32768,
                    "step": 1,
                    "tooltip": "模型生成文本时最多能使用的token数量"
                }),
                "history": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 40,
                    "step": 1,
                    "tooltip": "保持的历史对话轮数"
                }),
            },
            "optional": {
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "控制生成文本的随机性"
                }),
                "top_p": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "控制生成文本的多样性"
                }),
                "repetition_penalty": ("FLOAT", {
                    "default": 1.1,
                    "min": 1.0,
                    "max": 1.3,
                    "step": 0.05,
                    "tooltip": "控制重复文本的惩罚程度"
                }),
                "clear_history": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否清除历史对话记录"
                }),
            }
        }
    
    # 标准返回类型
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("generated_text", "conversation_info", "total_tokens")
    FUNCTION = "generate_response"
    OUTPUT_NODE = False
    
    def generate_response(self, text_input: str, platform: str, model: str, max_tokens: int, history: int,
                         temperature: Optional[float] = 0.7, top_p: Optional[float] = 0.9, 
                         repetition_penalty: Optional[float] = 1.1, clear_history: Optional[bool] = False):
        """
        生成文本响应的通用实现
        """
        try:
            # 清除历史记录
            if clear_history:
                self.conversation_manager.clear_all()
            
            # 验证输入参数
            is_valid, error_msg = self._validate_inputs(platform, model)
            if not is_valid:
                return (error_msg, "参数错误", 0)
            
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

请配置后重试。"""
                return (error_msg, "API密钥缺失", 0)
            
            # 获取或创建客户端
            client = self.client_manager.get_or_create_client(platform_config, api_key)
            
            # 管理对话历史
            conversation_key = self.conversation_manager.get_conversation_key(
                platform_config.platform_key, model
            )
            
            # 添加用户消息
            self.conversation_manager.add_message(conversation_key, "user", text_input)
            
            # 限制历史长度
            self.conversation_manager.limit_history(conversation_key, history)
            
            # 获取当前历史
            current_history = self.conversation_manager.get_history(conversation_key)
            
            # 准备基础API参数
            base_params = self._prepare_base_params(
                adapter.get_api_model_name(model),
                current_history,
                adapter.apply_token_limit(max_tokens),
                temperature,
                top_p
            )
            
            # 使用适配器准备最终参数
            api_params = adapter.prepare_api_params(
                base_params,
                model=model,
                repetition_penalty=repetition_penalty
            )
            
            # 调用API
            response = client.chat.completions.create(**api_params)
            
            # 处理响应
            reply, usage_info = self._handle_api_response(response, conversation_key)
            
            # 生成对话信息
            conversation_info = f"平台: {platform} | 模型: {model} | 历史轮数: {len(current_history)//2} | 总Tokens: {usage_info['total_tokens']} (输入: {usage_info['prompt_tokens']}, 输出: {usage_info['completion_tokens']}, 限制: {max_tokens})"
            
            return (reply, conversation_info, usage_info['total_tokens'])
            
        except Exception as e:
            error_message = f"{self.NODE_NAME} API调用失败 ({platform}): {str(e)}"
            return (error_message, "错误状态", 0)


class BaseVisionAPINode(BaseAPINode):
    """
    视觉模型API节点基类
    为视觉模型提供标准的输入输出接口
    """
    
    # 标记为基类，不应该被ComfyUI注册为节点
    _IS_BASE_CLASS = True
    
    API_TYPE = APIType.VISION
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """视觉模型的标准输入类型"""
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "输入要分析的图像"
                }),
                "text_input": ("STRING", {
                    "default": "请描述这张图片的内容。",
                    "multiline": True,
                    "tooltip": "输入要发送给AI视觉模型的文本问题"
                }),
                "platform": (list(cls.PLATFORM_CONFIGS.keys()), {
                    "default": list(cls.PLATFORM_CONFIGS.keys())[0] if cls.PLATFORM_CONFIGS else "未配置",
                    "tooltip": "选择API服务提供商"
                }),
                "model": (cls.get_all_models(), {
                    "default": cls.get_all_models()[0] if cls.get_all_models() else "未配置",
                    "tooltip": "选择要使用的AI视觉模型"
                }),
                "max_tokens": ("INT", {
                    "default": 4096,
                    "min": 1,
                    "max": 32768,
                    "step": 1,
                    "tooltip": "模型生成文本时最多能使用的token数量"
                }),
                "history": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 25,
                    "step": 1,
                    "tooltip": "保持的历史对话轮数"
                }),
            },
            "optional": {
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "控制生成文本的随机性"
                }),
                "top_p": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "控制生成文本的多样性"
                }),
                "image_quality": (["auto", "low", "high"], {
                    "default": "auto",
                    "tooltip": "图像处理质量：auto(自动选择), low(低质量，速度快), high(高质量，精度高)"
                }),
                "clear_history": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否清除历史对话记录"
                }),
            }
        }
    
    # 标准返回类型
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("generated_text", "conversation_info", "total_tokens")
    FUNCTION = "generate_response"
    OUTPUT_NODE = False
    
    def _image_to_base64(self, image) -> str:
        """将图像转换为base64格式"""
        try:
            # 处理ComfyUI的图像格式
            if TORCH_AVAILABLE and isinstance(image, torch.Tensor):
                if image.dim() == 4:  # batch dimension
                    image = image.squeeze(0)
                if image.dim() == 3 and image.shape[0] in [1, 3, 4]:  # CHW format
                    image = image.permute(1, 2, 0)  # HWC format
                
                # 确保值在0-255范围内
                if image.max() <= 1.0:
                    image = image * 255
                image = image.clamp(0, 255).byte()
                
                # 转换为PIL Image
                import numpy as np
                from PIL import Image
                image_np = image.cpu().numpy()
                if image_np.shape[2] == 1:  # 灰度图
                    image_pil = Image.fromarray(image_np.squeeze(), mode='L')
                elif image_np.shape[2] == 3:  # RGB
                    image_pil = Image.fromarray(image_np, mode='RGB')
                elif image_np.shape[2] == 4:  # RGBA
                    image_pil = Image.fromarray(image_np, mode='RGBA')
                else:
                    raise ValueError(f"不支持的图像通道数: {image_np.shape[2]}")
            else:
                image_pil = image
            
            # 转换为base64
            import base64
            from io import BytesIO
            buffer = BytesIO()
            image_pil.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            raise ValueError(f"图像转换失败: {str(e)}")
    
    def _prepare_vision_messages(self, image, text_input: str, conversation_key: str) -> List[Dict[str, Any]]:
        """准备视觉模型的消息格式"""
        # 转换图像为base64
        image_base64 = self._image_to_base64(image)
        
        # 添加用户消息（包含图像和文本）
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text_input
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_base64
                    }
                }
            ]
        }
        
        self.conversation_manager.add_message(conversation_key, "user", user_message["content"])
        
        # 获取历史消息
        return self.conversation_manager.get_history(conversation_key)
    
    def generate_response(self, image, text_input: str, platform: str, model: str, max_tokens: int, history: int,
                         temperature: Optional[float] = 0.7, top_p: Optional[float] = 0.9, 
                         image_quality: Optional[str] = "auto", clear_history: Optional[bool] = False):
        """
        生成视觉响应的通用实现
        """
        try:
            # 清除历史记录
            if clear_history:
                self.conversation_manager.clear_all()
            
            # 验证输入参数
            is_valid, error_msg = self._validate_inputs(platform, model)
            if not is_valid:
                return (error_msg, "参数错误", 0)
            
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

请配置后重试。"""
                return (error_msg, "API密钥缺失", 0)
            
            # 获取或创建客户端
            client = self.client_manager.get_or_create_client(platform_config, api_key)
            
            # 管理对话历史
            conversation_key = self.conversation_manager.get_conversation_key(
                platform_config.platform_key, model
            )
            
            # 准备视觉消息
            messages = self._prepare_vision_messages(image, text_input, conversation_key)
            
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
            
            # 使用适配器准备最终参数（包含图像质量）
            api_params = adapter.prepare_api_params(base_params, model=model, image_quality=image_quality)
            
            # 调用API
            response = client.chat.completions.create(**api_params)
            
            # 处理响应
            reply, usage_info = self._handle_api_response(response, conversation_key)
            
            # 生成对话信息
            conversation_info = f"平台: {platform} | 模型: {model} | 历史轮数: {len(messages)//2} | 图像质量: {image_quality} | 总Tokens: {usage_info['total_tokens']} (输入: {usage_info['prompt_tokens']}, 输出: {usage_info['completion_tokens']}, 限制: {max_tokens})"
            
            return (reply, conversation_info, usage_info['total_tokens'])
            
        except Exception as e:
            error_message = f"{self.NODE_NAME} API调用失败 ({platform}): {str(e)}"
            return (error_message, "错误状态", 0)


# 导出基础类供其他节点使用
__all__ = [
    'APIType',
    'PlatformConfig', 
    'BasePlatformAdapter',
    'APIKeyManager',
    'ConversationManager', 
    'ClientManager',
    'BaseAPINode',
    'BaseLanguageAPINode',
    'BaseVisionAPINode'
]
