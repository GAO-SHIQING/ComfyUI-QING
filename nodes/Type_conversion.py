# -*- coding: utf-8 -*-

class IntToString:
    """
    整数到字符串转换节点
    功能：将输入的整数转换为字符串
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "integer": ("INT", {
                    "default": 0,
                    "min": -2147483648,
                    "max": 2147483647,
                    "step": 1
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "convert_int_to_string"
    CATEGORY = "QING/数据类型"

    def convert_int_to_string(self, integer):
        """
        将整数转换为字符串
        
        参数:
            integer: 输入的整数
            
        返回:
            tuple: (字符串,)
        """
        try:
            result = str(integer)
            return (result,)
        except Exception as e:
            # 转换失败时返回空字符串
            return ("",)


class StringToInt:
    """
    字符串到整数转换节点
    功能：将输入的字符串转换为整数
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "string": ("STRING", {
                    "default": "0",
                    "multiline": False
                }),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("integer",)
    FUNCTION = "convert_string_to_int"
    CATEGORY = "QING/数据类型"

    def convert_string_to_int(self, string):
        """
        将字符串转换为整数
        
        转换规则:
        - 纯整数字符串直接转换
        - 浮点数字符串使用标准数学四舍五入规则
        - 自动去除首尾空格
        - 转换失败时返回0
        
        注意：使用标准四舍五入（0.5进位），而非Python默认的银行家舍入
        
        参数:
            string: 输入的字符串
            
        返回:
            tuple: (整数,)
        """
        try:
            # 去除首尾空格
            string = string.strip()
            
            # 处理空字符串
            if not string:
                return (0,)
            
            # 尝试转换为整数
            result = int(string)
            return (result,)
        except ValueError:
            # 如果字符串不能转换为整数，尝试转换浮点数再四舍五入
            try:
                float_val = float(string)
                # 实现标准数学四舍五入（而非Python的银行家舍入）
                if float_val >= 0:
                    result = int(float_val + 0.5)
                else:
                    result = int(float_val - 0.5)
                return (result,)
            except ValueError:
                # 转换失败时返回0
                return (0,)
        except Exception:
            # 其他异常情况返回0
            return (0,)


class StringToBool:
    """
    字符串到布尔转换节点
    功能：将输入的字符串转换为布尔值
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "string": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            },
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("boolean",)
    FUNCTION = "convert_string_to_bool"
    CATEGORY = "QING/数据类型"

    def convert_string_to_bool(self, string):
        """
        将字符串转换为布尔值
        
        转换规则：
        - "true", "1", "yes", "on", "enable" -> True
        - "false", "0", "no", "off", "disable", "" -> False
        - 数字字符串：非零为True，零为False
        
        参数:
            string: 输入的字符串
            
        返回:
            tuple: (布尔值,)
        """
        try:
            # 去除首尾空格并转换为小写
            string = string.strip().lower()
            
            # 处理空字符串
            if not string:
                return (False,)
            
            # 明确的真值字符串
            true_values = {"true", "1", "yes", "on", "enable", "enabled", "t", "y"}
            if string in true_values:
                return (True,)
            
            # 明确的假值字符串
            false_values = {"false", "0", "no", "off", "disable", "disabled", "f", "n"}
            if string in false_values:
                return (False,)
            
            # 尝试作为数字处理
            try:
                num_value = float(string)
                return (bool(num_value != 0),)
            except ValueError:
                # 如果不是数字，非空字符串默认为True
                return (True,)
                
        except Exception:
            # 异常情况返回False
            return (False,)


class BoolToInt:
    """
    布尔到整数转换节点
    功能：将输入的布尔值转换为整数
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "boolean": ("BOOLEAN", {
                    "default": False,
                    "label_on": "True",
                    "label_off": "False"
                }),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("integer",)
    FUNCTION = "convert_bool_to_int"
    CATEGORY = "QING/数据类型"

    def convert_bool_to_int(self, boolean):
        """
        将布尔值转换为整数
        
        转换规则：
        - True -> 1
        - False -> 0
        
        参数:
            boolean: 输入的布尔值
            
        返回:
            tuple: (整数,)
        """
        try:
            result = 1 if boolean else 0
            return (result,)
        except Exception:
            # 异常情况返回0
            return (0,)


class IntToBool:
    """
    整数到布尔转换节点
    功能：将输入的整数转换为布尔值
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "integer": ("INT", {
                    "default": 0,
                    "min": -2147483648,
                    "max": 2147483647,
                    "step": 1
                }),
            },
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("boolean",)
    FUNCTION = "convert_int_to_bool"
    CATEGORY = "QING/数据类型"

    def convert_int_to_bool(self, integer):
        """
        将整数转换为布尔值
        
        转换规则：
        - 0 -> False
        - 非零 -> True
        
        参数:
            integer: 输入的整数
            
        返回:
            tuple: (布尔值,)
        """
        try:
            result = bool(integer != 0)
            return (result,)
        except Exception:
            # 异常情况返回False
            return (False,)


class BoolInvert:
    """
    布尔反转节点
    功能：将输入的布尔值进行反转
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "boolean": ("BOOLEAN", {
                    "default": False,
                    "label_on": "True",
                    "label_off": "False"
                }),
            },
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("boolean",)
    FUNCTION = "invert_bool"
    CATEGORY = "QING/数据类型"

    def invert_bool(self, boolean):
        """
        将布尔值进行反转
        
        转换规则：
        - True -> False
        - False -> True
        
        参数:
            boolean: 输入的布尔值
            
        返回:
            tuple: (反转后的布尔值,)
        """
        try:
            result = not boolean
            return (result,)
        except Exception:
            # 异常情况返回False
            return (False,)


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
