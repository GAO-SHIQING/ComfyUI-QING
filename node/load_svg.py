import os
import folder_paths
import re

class LoadSVG:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "svg_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "请输入SVG文件的完整路径 (如: E:\\ceche\\path1.svg 或 /path/to/file.svg)"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("SVG内容",)  # 添加返回值的显示名称
    FUNCTION = "load_svg"
    CATEGORY = "input"
    TITLE = "加载SVG文件"
    DESCRIPTION = "加载SVG文件内容，支持绝对路径"

    def clean_path(self, path):
        """清理路径字符串，移除不可见字符和多余空格"""
        # 移除所有不可见字符（包括从左到右标记）
        cleaned = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', path.strip())
        # 移除多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def load_svg(self, svg_path):
        # 检查是否提供了路径
        if not svg_path or not svg_path.strip():
            raise Exception("未提供SVG文件路径")
        
        # 清理路径字符串，移除不可见字符
        cleaned_path = self.clean_path(svg_path)
        
        # 检查是否是绝对路径
        if os.path.isabs(cleaned_path):
            # 如果是绝对路径，直接使用
            file_path = os.path.normpath(cleaned_path)
        else:
            # 如果不是绝对路径，尝试相对于输入目录
            input_dir = folder_paths.get_input_directory()
            file_path = os.path.join(input_dir, cleaned_path)
            file_path = os.path.normpath(file_path)
        
        # 检查文件是否存在
        if not os.path.isfile(file_path):
            # 提供更详细的错误信息
            if not os.path.exists(file_path):
                raise Exception(f"文件不存在: {file_path}\n请检查路径是否正确")
            elif os.path.isdir(file_path):
                raise Exception(f"路径指向的是目录而不是文件: {file_path}")
            else:
                raise Exception(f"无法访问文件: {file_path}\n请检查文件权限")
        
        # 检查文件扩展名
        if not file_path.lower().endswith('.svg'):
            raise Exception(f"选择的文件不是SVG格式: {file_path}")
        
        # 检查文件是否为空
        if os.path.getsize(file_path) == 0:
            raise Exception(f"SVG文件为空: {file_path}")
            
        # 读取SVG文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    svg_content = f.read()
            except Exception as e:
                raise Exception(f"读取SVG文件时出错 (编码问题): {str(e)}")
        except PermissionError:
            raise Exception(f"没有权限读取文件: {file_path}")
        except Exception as e:
            raise Exception(f"读取SVG文件时出错: {str(e)}")
        
        # 检查读取的内容是否有效
        if not svg_content or not svg_content.strip():
            raise Exception(f"SVG文件内容为空或无效: {file_path}")
            
        # 验证内容是否包含SVG标签
        if '<svg' not in svg_content.lower():
            raise Exception(f"文件内容不是有效的SVG格式: {file_path}")
            
        return (svg_content,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "LoadSVG": LoadSVG
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadSVG": "加载SVG文件"
}