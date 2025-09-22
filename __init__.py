# 从 node 子目录中的文件导入节点类
from .nodes.Load_svg import LoadSVG
from .nodes.Mask_Splitter import MaskSplitter
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
from .nodes.Mask_preview import ImageMaskPreview
from .nodes.Image_cache import ImageCache


# 按照官方文档加载翻译系统
# 参考：https://docs.comfy.org/zh-CN/custom-nodes/i18n
# 官方示例：https://github.com/comfyui-wiki/ComfyUI-i18n-demo
try:
    from comfy.utils import load_translation
    load_translation(__file__)
except ImportError:
    # 当前 ComfyUI 版本不支持官方 i18n API
    # 使用 NODE_DISPLAY_NAME_MAPPINGS 作为回退方案
    pass

NODE_CLASS_MAPPINGS = {
    "LoadSVG": LoadSVG,
    "MaskSplitter": MaskSplitter,
    "SVGToImage": SVGToImage,
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
    "ImageMaskPreview": ImageMaskPreview,
    "ImageCache": ImageCache,
}

# 默认显示名称（中文作为默认）
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadSVG": "加载SVG文件",
    "MaskSplitter": "遮罩拆分",
    "SVGToImage": "SVG转图像",
    "CustomLoadImageWithFormat": "加载图像(支持SVG)",
    "MaskScale": "遮罩缩放",
    "TextCompare": "文本对比",
    "SyntheticVideo": "合成视频",
    "SVGSaver": "保存SVG",
    "ImageToSVG": "图像转SVG",
    "MaskJudgment": "遮罩判断",
    "MaskBlend": "遮罩混合",
    "MaskExpansion": "遮罩扩张",
    "ImageMaskConverter": "图像遮罩转换",
    "ImageMaskPreview": "图像遮罩预览",
    "ImageCache": "图像缓存",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
