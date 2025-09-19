# 从 node 子目录中的文件导入节点类
from .nodes.load_svg import LoadSVG
from .nodes.split_mask import MaskSplitterPro
from .nodes.svg_to_image import SVGToImage
from .nodes.custom_load_image import CustomLoadImageWithFormat
from .nodes.mask_scale import MaskScale
from .nodes.text_compare import TextCompare
from .nodes.video_combine import SyntheticVideo
from .nodes.svg_saver import SVGSaver
from .nodes.image_to_svg import ImageToSVG
from .nodes.mask_judgment import MaskJudgment
from .nodes.MaskBlend import MaskBlend

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
    "MaskJudgment":MaskJudgment,
    "MaskBlend":MaskBlend,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Load SVG": "加载SVG",
    "MaskSplitterPro": "拆分遮罩",
    "SVG To Image": "SVG到图像",
    "CustomLoadImageWithFormat": "加载图像(支持SVG)",
    "MaskScale": "遮罩缩放",
    "TextCompare":"文本对比",
    "SyntheticVideo": "合成视频",
    "SVGSaver": "保存SVG",
    "ImageToSVG": "图像到SVG",
    "MaskJudgment":"遮罩判断",
    "MaskBlend":"遮罩混合",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

