 # -*- coding: utf-8 -*-
"""
🎨QING配置服务器
提供HTTP端点用于前后端配置同步
参考comfyui_prompt_assistant项目的最佳实践
"""

import json
from pathlib import Path

try:
    from server import PromptServer
    from aiohttp import web
    COMFYUI_AVAILABLE = True
except ImportError:
    COMFYUI_AVAILABLE = False

if COMFYUI_AVAILABLE:
    from .settings_approach import get_config_manager
    
    def register_endpoints():
        """注册API端点（延迟注册以确保PromptServer已初始化）"""
        try:
            if not hasattr(PromptServer, 'instance') or PromptServer.instance is None:
                return False
            
            @PromptServer.instance.routes.get("/api/qing/config")
            async def get_qing_config(request):
                """获取🎨QING配置"""
                try:
                    config = get_config_manager().load_config()
                    return web.json_response(config)
                except Exception as e:
                    return web.json_response({
                        "error": f"获取配置失败: {str(e)}"
                    }, status=500)
            
            @PromptServer.instance.routes.post("/api/qing/config")
            async def update_qing_config(request):
                """更新🎨QING配置"""
                try:
                    data = await request.json()
                    action = data.get('action')
                    
                    if action == 'update_api_key':
                        api_key = data.get('api_key', '')
                        config_key = data.get('config_key', 'glm_api_key')
                        source = data.get('source', 'unknown')
                        
                        success = get_config_manager().update_api_key(api_key, source, config_key)
                        
                        if success:
                            return web.json_response({
                                "success": True,
                                "message": "API密钥更新成功"
                            })
                        else:
                            return web.json_response({
                                "error": "API密钥更新失败"
                            }, status=500)
                    
                    elif action == 'get_api_key':
                        api_key = get_config_manager().get_api_key()
                        return web.json_response({
                            "api_key": api_key,
                            "has_key": bool(api_key)
                        })
                    
                    elif action == 'clear_api_key':
                        success = get_config_manager().update_api_key("", data.get('source', 'unknown'))
                        return web.json_response({
                            "success": success,
                            "message": "API密钥已清除" if success else "清除失败"
                        })
                    
                    else:
                        return web.json_response({
                            "error": f"不支持的操作: {action}"
                        }, status=400)
                        
                except Exception as e:
                    return web.json_response({
                        "error": f"处理请求失败: {str(e)}"
                    }, status=500)
            
            return True
            
        except Exception:
            return False
    
    # 尝试立即注册，如果失败则稍后重试
    if not register_endpoints():
        import threading
        import time
        
        def delayed_register():
            """延迟注册端点"""
            for attempt in range(10):  # 最多重试10次
                time.sleep(1)  # 等待1秒
                if register_endpoints():
                    break
        
        # 在后台线程中延迟注册
        thread = threading.Thread(target=delayed_register, daemon=True)
        thread.start()

else:
    # 如果ComfyUI不可用，提供回退方法
    def get_qing_api_key_fallback():
        """回退的API密钥获取方法"""
        return get_api_key_by_platform('glm_api_key')
    
    def set_qing_api_key_fallback(api_key: str):
        """回退的API密钥设置方法"""
        return set_api_key_by_platform('glm_api_key', api_key)

# 支持多平台API密钥管理（通用函数，在任何情况下都可用）
def get_api_key_by_platform(config_key: str) -> str:
    """
    根据平台配置键获取API密钥
    
    Args:
        config_key: 配置键名（如: glm_api_key, volcengine_api_key, dashscope_api_key, siliconflow_api_key, tencent_lkeap_api_key, moonshot_api_key, gemini_api_key）
    
    Returns:
        str: API密钥
    """
    try:
        config_path = Path(__file__).parent / "config" / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_settings = config.get('api_settings', {})
                key_config = api_settings.get(config_key, '')
                
                # 兼容新旧配置格式
                if isinstance(key_config, dict):
                    # 新格式：返回value字段
                    return key_config.get('value', '')
                else:
                    # 旧格式：直接返回字符串值
                    return str(key_config) if key_config else ''
    except Exception:
        pass
    return ""

def set_api_key_by_platform(config_key: str, api_key: str) -> bool:
    """
    根据平台配置键设置API密钥
    
    Args:
        config_key: 配置键名
        api_key: API密钥
    
    Returns:
        bool: 是否设置成功
    """
    try:
        config_path = Path(__file__).parent / "config" / "config.json"
        config_path.parent.mkdir(exist_ok=True)
        
        config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        if 'api_settings' not in config:
            config['api_settings'] = {}
        
        # 获取或创建API密钥配置
        if config_key not in config['api_settings']:
            config['api_settings'][config_key] = {}
        
        # 兼容新旧格式
        key_config = config['api_settings'][config_key]
        if isinstance(key_config, dict):
            # 新格式：更新value字段
            key_config['value'] = api_key
        else:
            # 迁移到新格式
            config['api_settings'][config_key] = {
                "__comment": f"{config_key} API密钥",
                "value": api_key
            }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception:
        return False