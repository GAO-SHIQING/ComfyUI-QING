# 从 node 子目录中的文件导入节点类
from .node.load_svg import LoadSVG
from .node.split_mask import MaskSplitterPro
from .node.svg_to_image import SVGToImage
from .node.custom_load_image import CustomLoadImageWithFormat

NODE_CLASS_MAPPINGS = {
    "Load SVG": LoadSVG,
    "MaskSplitterPro": MaskSplitterPro,
    "SVG To Image": SVGToImage,
    "CustomLoadImageWithFormat": CustomLoadImageWithFormat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Load SVG": "Load SVG",
    "MaskSplitterPro": "Split Mask",
    "SVG To Image": "SVG To Image",
    "CustomLoadImageWithFormat": "加载图像(支持SVG)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
