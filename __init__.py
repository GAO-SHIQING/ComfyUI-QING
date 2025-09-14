# 从 node 子目录中的文件导入节点类
from .nodes.load_svg import LoadSVG
from .nodes.split_mask import MaskSplitterPro
from .nodes.svg_to_image import SVGToImage
from .nodes.custom_load_image import CustomLoadImageWithFormat

NODE_CLASS_MAPPINGS = {
    "Load SVG": LoadSVG,
    "MaskSplitterPro": MaskSplitterPro,
    "SVG To Image": SVGToImage,
    "CustomLoadImageWithFormat": CustomLoadImageWithFormat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Load SVG": "加载SVG",
    "MaskSplitterPro": "拆分遮罩",
    "SVG To Image": "SVG到图像",
    "CustomLoadImageWithFormat": "加载图像(支持SVG)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
