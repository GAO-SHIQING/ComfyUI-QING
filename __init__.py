# 从 node 子目录中的文件导入节点类
from .nodes.Load_svg import LoadSVG
from .nodes.Split_mask import MaskSplitterPro
from .nodes.Svg_to_image import SVGToImage
from .nodes.Custom_load_image import CustomLoadImageWithFormat
from .nodes.Mask_scale import MaskScale
from .nodes.Text_compare import TextCompare
from .nodes.Video_combine import SyntheticVideo
from .nodes.Svg_saver import SVGSaver
from .nodes.Image_to_svg import ImageToSVG
from .nodes.Mask_judgment import MaskJudgment
from .nodes.Mask_blend import MaskBlend
from .nodes.Mask_expansion import MaskExpansion
from .nodes.Image_mask_converter import ImageMaskConverter

NODE_CLASS_MAPPINGS = {
    "Load SVG": LoadSVG,
    "MaskSplitterPro": MaskSplitterPro,
    "SVG To Image": SVGToImage,
    "CustomLoadImageWithFormat": CustomLoadImageWithFormat,
    "MaskScale": MaskScale,
    "TextCompare": TextCompare,
    "SyntheticVideo": SyntheticVideo,
    "SVGSaver": SVGSaver,
    "ImageToSVG": ImageToSVG,
    "MaskJudgment": MaskJudgment,
    "MaskBlend": MaskBlend,
    "MaskExpansion": MaskExpansion,
    "ImageMaskConverter": ImageMaskConverter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Load SVG": "加载SVG",
    "MaskSplitterPro": "拆分遮罩",
    "SVG To Image": "SVG到图像",
    "CustomLoadImageWithFormat": "加载图像(支持SVG)",
    "MaskScale": "遮罩缩放",
    "TextCompare": "文本对比",
    "SyntheticVideo": "合成视频",
    "SVGSaver": "保存SVG",
    "ImageToSVG": "图像到SVG",
    "MaskJudgment": "遮罩判断",
    "MaskBlend": "遮罩混合",
    "MaskExpansion": "遮罩扩张",
    "ImageMaskConverter": "图像遮罩转换",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

