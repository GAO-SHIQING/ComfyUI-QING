# -*- coding: utf-8 -*-
"""
GLM Vision API节点
调用智谱GLM视觉模型API进行图像理解和分析
"""

import os
import base64
import io
from typing import Optional, List, Dict, Any
import torch
import numpy as np
from PIL import Image

try:
    from zai import ZhipuAiClient
    ZAI_SDK_AVAILABLE = True
except ImportError:
    ZAI_SDK_AVAILABLE = False


class GLMVisionAPI:
    """
    GLM Vision API节点
    
    功能：
    - 调用智谱GLM视觉模型API进行图像理解
    - 支持多种GLM视觉模型选择
    - 支持历史对话上下文
    - 支持图像+文本多模态输入
    """
    
    # GLM视觉模型列表（严格按照官方文档定义）
    GLM_VISION_MODELS = [
        # GLM-4.5V 系列（最新视觉模型）
        "glm-4.5v",
        
        # GLM-4.1V Thinking 系列（支持思维链推理）
        "glm-4.1v-thinking-flashx", 
        
        # GLM-4V 系列（经典视觉模型）
        "glm-4v-flash",  # 快速版本
        "glm-4v",        # 标准版本  
        "glm-4v-plus",   # 增强版本
    ]
    
    def __init__(self):
        self.conversation_history: List[Dict[str, Any]] = []
        self.client: Optional[Any] = None
        self._last_api_key: str = ""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "输入要分析的图像"
                }),
                "text_input": ("STRING", {
                    "default": "请描述这张图片的内容。",
                    "multiline": True,
                    "tooltip": "输入关于图像的问题或指令"
                }),
                 "model": (cls.GLM_VISION_MODELS, {
                     "default": "glm-4.5v",
                     "tooltip": "选择要使用的GLM视觉模型"
                 }),
                "max_tokens": ("INT", {
                    "default": 3072,
                    "min": 1,
                    "max": 32768,
                    "step": 1,
                    "tooltip": "模型生成文本时最多能使用的token数量"
                }),
                "history": ("INT", {
                    "default": 6,
                    "min": 1,
                    "max": 18,
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
                    "tooltip": "控制生成文本的随机性，越高越随机"
                }),
                "top_p": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "tooltip": "控制生成文本的多样性"
                }),
                "clear_history": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否清除历史对话记录"
                }),
                "image_quality": (["auto", "low", "high"], {
                    "default": "auto",
                    "tooltip": "图像质量设置：auto自动，low低质量，high高质量"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("generated_text", "conversation_info", "token_count")
    FUNCTION = "analyze_image"
    CATEGORY = "🎨QING/API调用"
    OUTPUT_NODE = False
    
    def analyze_image(self, image: torch.Tensor, text_input: str, model: str, max_tokens: int, 
                     history: int, temperature: float = 0.7, 
                     top_p: float = 0.9, clear_history: bool = False, 
                     image_quality: str = "auto") -> tuple:
        """
        使用GLM视觉模型分析图像
        
        参数:
            image: 输入图像张量
            text_input: 输入文本
            model: 模型名称
            max_tokens: 最大token数
            history: 历史对话轮数
            temperature: 温度参数
            top_p: top_p参数
            clear_history: 是否清除历史
            image_quality: 图像质量
            
        返回:
            tuple: (生成的文本, 对话信息, token使用量)
        """
        try:
            # 检查依赖
            if not ZAI_SDK_AVAILABLE:
                error_msg = "错误：未安装zai-sdk库。请运行：pip install zai-sdk"
                return (error_msg, "依赖缺失", 0)
            
            # 如果需要清除历史
            if clear_history:
                self.conversation_history.clear()
            
            # 获取API密钥（优先级：🎨QING设置 > 环境变量）
            try:
                from .api_key_server import get_qing_api_key
                final_api_key = get_qing_api_key()
            except ImportError:
                # 回退到环境变量
                final_api_key = os.getenv('ZHIPUAI_API_KEY', '')
            
            if not final_api_key:
                error_msg = "错误：未提供API密钥。请在🎨QING设置中配置智谱GLM_API_Key，或设置ZHIPUAI_API_KEY环境变量"
                return (error_msg, "API密钥缺失", 0)
            
            # 初始化客户端
            if self.client is None or self._last_api_key != final_api_key:
                self.client = ZhipuAiClient(api_key=final_api_key)
                self._last_api_key = final_api_key
            
            # 处理图像
            image_base64 = self._process_image(image, image_quality)
            if image_base64 is None:
                error_msg = "错误：图像处理失败"
                return (error_msg, "图像处理异常", 0)
            
            # 构建消息列表
            messages = self._build_messages(text_input, image_base64, history)
            
            # 根据官方文档对不同模型进行参数适配
            response = None
            
            if model in ["glm-4.5v", "glm-4.1v-thinking-flashx"]:
                # GLM-4.5V和GLM-4.1V系列：支持完整参数
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stream=False
                )
            elif model in ["glm-4v-flash", "glm-4v", "glm-4v-plus"]:
                # GLM-4V系列：基于1210错误测试结果进行多层参数尝试
                try:
                    # 策略1：只使用max_tokens（去掉temperature和top_p）
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        stream=False
                    )
                except Exception as e:
                    if "1210" in str(e):
                        # 策略2：完全最小参数（连max_tokens也去掉）
                        response = self.client.chat.completions.create(
                            model=model,
                            messages=messages,
                            stream=False
                        )
                    else:
                        raise e
            else:
                # 未知模型：使用基础参数
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    stream=False
                )
            
            # 提取生成的文本
            if response.choices and len(response.choices) > 0:
                generated_text = response.choices[0].message.content
                
                # 更新对话历史
                self._update_conversation_history(text_input, image_base64, generated_text, history)
                
                # 获取token使用信息
                token_count = getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
                
                # 生成对话信息
                conversation_info = self._generate_conversation_info(model, len(messages), token_count)
                
                return (generated_text, conversation_info, token_count)
            else:
                error_msg = "错误：API返回空响应"
                return (error_msg, "API响应异常", 0)
                
        except ImportError as e:
            error_msg = f"导入错误: {str(e)}"
            return (error_msg, "模块导入失败", 0)
        except ConnectionError as e:
            error_msg = f"网络连接错误: {str(e)}"
            return (error_msg, "网络异常", 0)
        except TimeoutError as e:
            error_msg = f"请求超时: {str(e)}"
            return (error_msg, "请求超时", 0)
        except ValueError as e:
            error_msg = f"参数错误: {str(e)}"
            return (error_msg, "参数异常", 0)
        except Exception as e:
            # 严格按照官方文档处理错误（不做特殊参数尝试）
            error_detail = str(e)
            if "api_key" in error_detail.lower():
                error_msg = f"API密钥错误: {error_detail}"
                return (error_msg, "认证失败", 0)
            elif "quota" in error_detail.lower() or "balance" in error_detail.lower():
                error_msg = f"余额不足: {error_detail}"
                return (error_msg, "配额不足", 0)
            elif "rate" in error_detail.lower():
                error_msg = f"请求频率过高: {error_detail}"
                return (error_msg, "频率限制", 0)
            elif "1210" in error_detail:
                error_msg = f"API参数错误(1210): {error_detail} - 请检查模型名称和参数是否符合官方文档"
                return (error_msg, "参数不兼容", 0)
            else:
                error_msg = f"GLM Vision API调用失败: {error_detail}"
                return (error_msg, f"错误: {type(e).__name__}", 0)
    
    def _process_image(self, image: torch.Tensor, quality: str = "auto") -> Optional[str]:
        """处理图像并转换为base64编码"""
        try:
            # 转换tensor到PIL Image
            if len(image.shape) == 4:
                # 批次维度，取第一张图片
                image = image[0]
            
            # 确保数据类型正确
            if image.dtype == torch.float32 or image.dtype == torch.float64:
                # 假设数据范围是[0, 1]
                image_np = (image.cpu().numpy() * 255).astype(np.uint8)
            else:
                image_np = image.cpu().numpy()
            
            # 转换为PIL图像
            if len(image_np.shape) == 3:
                if image_np.shape[2] == 3:  # RGB
                    pil_image = Image.fromarray(image_np, 'RGB')
                elif image_np.shape[2] == 4:  # RGBA
                    pil_image = Image.fromarray(image_np, 'RGBA')
                    # 转换为RGB
                    pil_image = pil_image.convert('RGB')
                else:
                    return None
            else:
                return None
            
            # 根据质量设置调整图像
            if quality == "low":
                # 降低分辨率
                max_size = (512, 512)
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                jpeg_quality = 60
            elif quality == "high":
                # 保持高分辨率
                max_size = (2048, 2048)
                if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
                    pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                jpeg_quality = 95
            else:  # auto
                # 自动调整
                max_size = (1024, 1024)
                if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
                    pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                jpeg_quality = 85
            
            # 转换为base64
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG', quality=jpeg_quality)
            image_bytes = buffer.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            return image_base64
            
        except Exception as e:
            pass
            return None
    
    def _build_messages(self, text_input: str, image_base64: str, history: int) -> List[Dict[str, Any]]:
        """构建消息列表（严格遵循智谱AI官方API文档格式）"""
        messages = []
        
        # 添加历史对话（限制数量）
        history_count = min(len(self.conversation_history), history * 2)
        if history_count > 0:
            messages.extend(self.conversation_history[-history_count:])
        
        # 构建当前用户消息（完全按照官方文档规范）
        # 参考官方文档：https://docs.bigmodel.cn/api-reference/模型-api/对话补全#视觉模型
        current_message = {
            "role": "user",
            "content": [
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                },
                {
                    "type": "text",
                    "text": text_input
                }
            ]
        }
        
        messages.append(current_message)
        return messages
    
    def _update_conversation_history(self, user_input: str, image_base64: str, 
                                   assistant_response: str, max_history: int):
        """更新对话历史（符合官方API格式）"""
        # 添加用户输入（为了节省存储，只保存文本部分）
        user_message = {
            "role": "user", 
            "content": user_input  # 简化为纯文本，避免重复存储图像
        }
        
        # 添加助手回复
        assistant_message = {
            "role": "assistant", 
            "content": assistant_response
        }
        
        self.conversation_history.append(user_message)
        self.conversation_history.append(assistant_message)
        
        # 限制历史长度
        max_messages = max_history * 2
        if len(self.conversation_history) > max_messages:
            self.conversation_history = self.conversation_history[-max_messages:]
    
    def _generate_conversation_info(self, model: str, message_count: int, token_count: int) -> str:
        """生成对话信息"""
        history_rounds = len(self.conversation_history) // 2
        info_lines = [
            f"模型: {model}",
            f"本次消息数: {message_count}",
            f"历史轮数: {history_rounds}",
            f"Token使用: {token_count}",
            f"模式: 视觉+文本",
            f"对话状态: 正常"
        ]
        return "\n".join(info_lines)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # 每次都重新执行，因为是API调用
        return float("nan")


# 节点注册
NODE_CLASS_MAPPINGS = {
    "GLMVisionAPI": GLMVisionAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GLMVisionAPI": "GLM_视觉丨API"
}
