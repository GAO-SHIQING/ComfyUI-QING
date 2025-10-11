# -*- coding: utf-8 -*-

class IntToString:
    """整数到字符串转换节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"integer": ("INT", {"default": 0})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("字符串",)
    FUNCTION = "convert"
    CATEGORY = "🎨QING/数据工具"

    def convert(self, integer):
        return (str(integer),)


class StringToInt:
    """字符串到整数转换节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"string": ("STRING", {"default": "0"})}}

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("整数",)
    FUNCTION = "convert"
    CATEGORY = "🎨QING/数据工具"

    def convert(self, string):
        try:
            return (int(float(string.strip())),)
        except:
            return (0,)


class StringToBool:
    """字符串到布尔转换节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"string": ("STRING", {"default": ""})}}

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("布尔",)
    FUNCTION = "convert"
    CATEGORY = "🎨QING/数据工具"

    def convert(self, string):
        s = string.strip().lower()
        return (s in {"true", "1", "yes", "on", "t", "y"},)


class BoolToInt:
    """布尔到整数转换节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"boolean": ("BOOLEAN", {"default": False})}}

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("整数",)
    FUNCTION = "convert"
    CATEGORY = "🎨QING/数据工具"

    def convert(self, boolean):
        return (1 if boolean else 0,)


class IntToBool:
    """整数到布尔转换节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"integer": ("INT", {"default": 0})}}

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("布尔",)
    FUNCTION = "convert"
    CATEGORY = "🎨QING/数据工具"

    def convert(self, integer):
        return (bool(integer),)


class BoolInvert:
    """布尔反转节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"boolean": ("BOOLEAN", {"default": False})}}

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("布尔",)
    FUNCTION = "convert"
    CATEGORY = "🎨QING/数据工具"

    def convert(self, boolean):
        return (not boolean,)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "IntToString": IntToString,
    "StringToInt": StringToInt,
    "StringToBool": StringToBool,
    "BoolToInt": BoolToInt,
    "IntToBool": IntToBool,
    "BoolInvert": BoolInvert,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IntToString": "整数到字符串",
    "StringToInt": "字符串到整数", 
    "StringToBool": "字符串到布尔",
    "BoolToInt": "布尔到整数",
    "IntToBool": "整数到布尔",
    "BoolInvert": "布尔反转",
}