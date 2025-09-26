# -*- coding: utf-8 -*-
"""
GLM Language API节点
调用智谱GLM语言模型API进行文本推理
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from zai import ZhipuAiClient
    ZAI_SDK_AVAILABLE = True
except ImportError:
    ZAI_SDK_AVAILABLE = False


class GLMLanguageAPI:
    """
    GLM Language API节点
    
    功能：
    - 调用智谱GLM模型API进行文本推理
    - 支持多种GLM模型选择
    - 支持历史对话上下文
    - 可自定义生成长度
    """
    
    # GLM模型列表
    GLM_MODELS = [
        # GLM-4.5 系列（最新）
        "glm-4.5-flash",
        "glm-4.5",
        "glm-4.5-air",
        "glm-4.5-x",
        "glm-4.5-airx",
        
        # GLM-4 系列
        "glm-4-flash",
        "glm-4-flash-250414",
        "GLM-4-FlashX",
        "GLM-4-PIus",
        "glm-4-0520", 
        "glm-4",
        "glm-4-air",
        "glm-4-airx",
        "glm-4-long",
        
        # GLM-3 系列
        "glm-3-turbo"
    ]
    
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self.client: Optional[Any] = None  # 使用Any类型以支持不同的客户端
        self._last_api_key: str = ""  # 缓存API密钥，避免重复初始化客户端
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_input": ("STRING", {
                    "default": "你好，请介绍一下你自己。",
                    "multiline": True,
                    "tooltip": "输入要发送给GLM模型的文本内容"
                }),
                "model": (cls.GLM_MODELS, {
                    "default": "glm-4.5-flash",
                    "tooltip": "选择要使用的GLM模型"
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
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("generated_text", "conversation_info", "token_count")
    FUNCTION = "generate_text"
    CATEGORY = "🎨QING/API调用"
    OUTPUT_NODE = False
    
    def generate_text(self, text_input: str, model: str, max_tokens: int, history: int,
                     temperature: float = 0.7, top_p: float = 0.9,
                     clear_history: bool = False) -> tuple:
        """
        使用GLM模型生成文本
        
        参数:
            text_input: 输入文本
            model: 模型名称
            max_tokens: 最大token数
            history: 历史对话轮数
            temperature: 温度参数
            top_p: top_p参数
            clear_history: 是否清除历史
            
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
            
            # 获取API密钥（多重获取策略）
            final_api_key = ""
            
            # 策略1: 从🎨QING API密钥服务器获取
            try:
                from .api_key_server import get_qing_api_key
                final_api_key = get_qing_api_key()
            except ImportError:
                pass
            
            # 策略2: 从JavaScript全局变量获取（通过特殊方式）
            if not final_api_key:
                try:
                    # 尝试从可能的全局状态获取
                    import tempfile
                    temp_file = Path(tempfile.gettempdir()) / "qing_api_key_temp.txt"
                    if temp_file.exists():
                        with open(temp_file, 'r', encoding='utf-8') as f:
                            temp_key = f.read().strip()
                            if temp_key:
                                final_api_key = temp_key
                except Exception:
                    pass
            
            # 策略3: 从环境变量获取
            if not final_api_key:
                final_api_key = os.getenv('ZHIPUAI_API_KEY', '')
            
            if not final_api_key:
                error_msg = """错误：未提供API密钥。请尝试以下方法之一：
1. 在🎨QING设置中配置智谱GLM_API_Key
2. 设置环境变量: set ZHIPUAI_API_KEY=your_key
3. 临时方案：创建文件 %TEMP%\\qing_api_key_temp.txt 并写入您的API密钥"""
                return (error_msg, "API密钥缺失", 0)
            
            # 初始化客户端（使用最新的zai-sdk）
            if self.client is None or self._last_api_key != final_api_key:
                self.client = ZhipuAiClient(api_key=final_api_key)
                self._last_api_key = final_api_key
            
            # 构建消息列表
            messages = self._build_messages(text_input, history)
            
            # 调用API
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=False
            )
            
            # 提取生成的文本
            if response.choices and len(response.choices) > 0:
                generated_text = response.choices[0].message.content
                
                # 更新对话历史
                self._update_conversation_history(text_input, generated_text, history)
                
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
            # 尝试解析具体的API错误
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
            else:
                error_msg = f"GLM API调用失败: {error_detail}"
                return (error_msg, f"错误: {type(e).__name__}", 0)
    
    def _build_messages(self, text_input: str, history: int) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []
        
        # 添加历史对话（限制数量）
        history_count = min(len(self.conversation_history), history * 2)  # 每轮对话包含用户和助手消息
        if history_count > 0:
            messages.extend(self.conversation_history[-history_count:])
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": text_input})
        
        return messages
    
    def _update_conversation_history(self, user_input: str, assistant_response: str, max_history: int):
        """更新对话历史"""
        # 添加用户输入和助手回复
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})
        
        # 限制历史长度（每轮对话包含用户和助手消息）
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
            f"对话状态: 正常"
        ]
        return "\n".join(info_lines)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # 每次都重新执行，因为是API调用
        return float("nan")


# 节点注册
NODE_CLASS_MAPPINGS = {
    "GLMLanguageAPI": GLMLanguageAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GLMLanguageAPI": "GLM_语言丨API"
}
