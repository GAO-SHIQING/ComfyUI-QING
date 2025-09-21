# -*- coding: utf-8 -*-
import torch

class TextCompare:
    """
    文本比较节点：固定3组对比，支持全局是否区分大小写
    - 输入 textN 与 subtextN（N=1..3）
    - 输出每组对比的布尔结果
    """
    
    MODULE_COUNT = 3
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        input_types = {
            "required": {
                "case_sensitive": ("BOOLEAN", {
                    "default": False, 
                    "label_on": "开启", 
                    "label_off": "关闭"
                }),
            },
            "optional": {}
        }
        
        # 使用英文参数名
        for i in range(cls.MODULE_COUNT):
            module_num = i + 1
            input_types["optional"][f"text_{module_num}"] = ("STRING", {
                "default": "", 
                "multiline": False
            })
            input_types["optional"][f"subtext_{module_num}"] = ("STRING", {
                "default": "", 
                "multiline": False
            })
        
        return input_types
    
    RETURN_TYPES = tuple(["BOOLEAN"] * MODULE_COUNT)
    # 输出名称去掉下划线，使用更简洁的中文
    RETURN_NAMES = tuple([f"result_{i+1}" for i in range(MODULE_COUNT)])
    FUNCTION = "compare_texts"
    CATEGORY = "文本/处理"
    OUTPUT_NODE = True
    
    def compare_texts(self, case_sensitive=False, **kwargs):
        results = []
        
        for i in range(self.MODULE_COUNT):
            text_key = f"text_{i+1}"
            subtext_key = f"subtext_{i+1}"
            
            text = kwargs.get(text_key, "")
            subtext = kwargs.get(subtext_key, "")
            
            if not isinstance(text, str):
                text = str(text) if text is not None else ""
            if not isinstance(subtext, str):
                subtext = str(subtext) if subtext is not None else ""
            
            try:
                if case_sensitive:
                    result = (text == subtext)
                else:
                    result = (text.lower() == subtext.lower())
            except Exception as e:
                # Error comparing texts in module
                result = False
                
            results.append(result)
            
        return tuple(results)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

NODE_CLASS_MAPPINGS = {
    "TextCompare": TextCompare
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextCompare": "Text Compare"
}
