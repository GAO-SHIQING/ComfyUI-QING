# 从 node 子目录中的文件导入节点类
from .nodes.load_svg import LoadSVG
from .nodes.split_mask import MaskSplitterPro
from .nodes.svg_to_image import SVGToImage
from .nodes.custom_load_image import CustomLoadImageWithFormat
from .nodes.mask_scale import MaskScale
from .nodes.text_compare import TextCompare

NODE_CLASS_MAPPINGS = {
    "Load SVG": LoadSVG,
    "MaskSplitterPro": MaskSplitterPro,
    "SVG To Image": SVGToImage,
    "CustomLoadImageWithFormat": CustomLoadImageWithFormat,
    "MaskScale": MaskScale,
    "TextCompare": TextCompare,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Load SVG": "加载SVG",
    "MaskSplitterPro": "拆分遮罩",
    "SVG To Image": "SVG到图像",
    "CustomLoadImageWithFormat": "加载图像(支持SVG)",
    "MaskScale": "遮罩缩放",
    "TextCompare":"文本比较",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
