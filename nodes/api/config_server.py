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
    from .settings_approach import qing_config_manager
    
    def register_endpoints():
        """注册API端点（延迟注册以确保PromptServer已初始化）"""
        try:
            if not hasattr(PromptServer, 'instance') or PromptServer.instance is None:
                return False
            
            @PromptServer.instance.routes.get("/api/qing/config")
            async def get_qing_config(request):
                """获取🎨QING配置"""
                try:
                    config = qing_config_manager.load_config()
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
                        source = data.get('source', 'unknown')
                        
                        success = qing_config_manager.update_api_key(api_key, source)
                        
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
                        api_key = qing_config_manager.get_api_key()
                        return web.json_response({
                            "api_key": api_key,
                            "has_key": bool(api_key)
                        })
                    
                    elif action == 'clear_api_key':
                        success = qing_config_manager.update_api_key("", data.get('source', 'unknown'))
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
    # 如果ComfyUI不可用，提供一个简单的文件系统API
    def get_qing_api_key_fallback():
        """回退的API密钥获取方法"""
        try:
            config_path = Path(__file__).parent / "config" / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('api_settings', {}).get('glm_api_key', '')
        except Exception:
            pass
        return ""
    
    def set_qing_api_key_fallback(api_key: str):
        """回退的API密钥设置方法"""
        try:
            config_path = Path(__file__).parent / "config" / "config.json"
            config_path.parent.mkdir(exist_ok=True)
            
            config = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            if 'api_settings' not in config:
                config['api_settings'] = {}
            
            config['api_settings']['glm_api_key'] = api_key
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False