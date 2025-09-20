import os
import sys
import json
import subprocess
import numpy as np
import re
import datetime
import tempfile
import shutil
import base64
from typing import List, Dict, Any, Optional, Generator
import torch
from PIL import Image, ExifTags, ImageSequence
from PIL.PngImagePlugin import PngInfo
from pathlib import Path
from string import Template
import itertools
import functools

import folder_paths

# 常量
BIGMAX = 0x7fffffff
ENCODE_ARGS = ('utf-8', 'ignore')

# 内置视频格式配置 - 扩展更多编码选项
DEFAULT_VIDEO_FORMATS = {
    "mp4": {
        "extension": "mp4",
        "encoders": {
            "h264": {
                "main_pass": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium"],
                "audio_pass": ["-c:a", "aac", "-b:a", "128k"],
                "description": "H.264编码，兼容性好"
            },
            "h265": {
                "main_pass": ["-c:v", "libx265", "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "medium"],
                "audio_pass": ["-c:a", "aac", "-b:a", "128k"],
                "description": "H.265/HEVC编码，高压缩率"
            },
            "av1": {
                "main_pass": ["-c:v", "libaom-av1", "-crf", "30", "-b:v", "0", "-cpu-used", "6"],
                "audio_pass": ["-c:a", "aac", "-b:a", "128k"],
                "description": "AV1编码，最新压缩技术"
            },
            "prores": {
                "main_pass": ["-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0"],
                "audio_pass": ["-c:a", "pcm_s16le"],
                "description": "Apple ProRes编码，高质量"
            }
        },
        "default_encoder": "h264",
        "dim_alignment": 2,
        "save_metadata": "True",
        "environment": {}
    },
    "webm": {
        "extension": "webm",
        "encoders": {
            "vp9": {
                "main_pass": ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0"],
                "audio_pass": ["-c:a", "libopus", "-b:a", "128k"],
                "description": "VP9编码，WebM标准"
            },
            "av1": {
                "main_pass": ["-c:v", "libaom-av1", "-crf", "30", "-b:v", "0", "-cpu-used", "6"],
                "audio_pass": ["-c:a", "libopus", "-b:a", "128k"],
                "description": "AV1编码，最新压缩技术"
            }
        },
        "default_encoder": "vp9",
        "dim_alignment": 2,
        "save_metadata": "True",
        "environment": {}
    },
    "avi": {
        "extension": "avi",
        "encoders": {
            "mpeg4": {
                "main_pass": ["-c:v", "mpeg4", "-qscale:v", "3"],
                "audio_pass": ["-c:a", "mp3", "-b:a", "128k"],
                "description": "MPEG-4编码，兼容性好"
            },
            "xvid": {
                "main_pass": ["-c:v", "libxvid", "-qscale:v", "3"],
                "audio_pass": ["-c:a", "mp3", "-b:a", "128k"],
                "description": "Xvid编码，DivX兼容"
            }
        },
        "default_encoder": "mpeg4",
        "dim_alignment": 2,
        "save_metadata": "False",
        "environment": {}
    },
    "mov": {
        "extension": "mov",
        "encoders": {
            "prores": {
                "main_pass": ["-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0"],
                "audio_pass": ["-c:a", "pcm_s16le"],
                "description": "Apple ProRes编码，高质量"
            },
            "h264": {
                "main_pass": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium"],
                "audio_pass": ["-c:a", "aac", "-b:a", "128k"],
                "description": "H.264编码，兼容性好"
            }
        },
        "default_encoder": "prores",
        "dim_alignment": 2,
        "save_metadata": "True",
        "environment": {}
    },
    "gif": {
        "extension": "gif",
        "encoders": {
            "gif": {
                "main_pass": ["-f", "gif"],
                "gifski_pass": ["--fps", "10", "--quality", "90"],
                "description": "标准GIF编码"
            },
            "high_quality": {
                "main_pass": ["-f", "gif"],
                "gifski_pass": ["--fps", "10", "--quality", "100", "--extra"],
                "description": "高质量GIF编码"
            }
        },
        "default_encoder": "gif",
        "dim_alignment": 1,
        "save_metadata": "False",
        "environment": {}
    },
    "mkv": {
        "extension": "mkv",
        "encoders": {
            "h264": {
                "main_pass": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23"],
                "audio_pass": ["-c:a", "aac", "-b:a", "128k"],
                "description": "H.264编码，兼容性好"
            },
            "h265": {
                "main_pass": ["-c:v", "libx265", "-pix_fmt", "yuv420p", "-crf", "28"],
                "audio_pass": ["-c:a", "aac", "-b:a", "128k"],
                "description": "H.265/HEVC编码，高压缩率"
            },
            "av1": {
                "main_pass": ["-c:v", "libaom-av1", "-crf", "30", "-b:v", "0", "-cpu-used", "6"],
                "audio_pass": ["-c:a", "aac", "-b:a", "128k"],
                "description": "AV1编码，最新压缩技术"
            }
        },
        "default_encoder": "h264",
        "dim_alignment": 2,
        "save_metadata": "True",
        "environment": {}
    },
    "flv": {
        "extension": "flv",
        "encoders": {
            "flv": {
                "main_pass": ["-c:v", "flv", "-qscale:v", "5"],
                "audio_pass": ["-c:a", "mp3", "-b:a", "128k"],
                "description": "Flash视频格式"
            }
        },
        "default_encoder": "flv",
        "dim_alignment": 2,
        "save_metadata": "False",
        "environment": {}
    }
}

def flatten_list(l):
    """展平嵌套列表"""
    ret = []
    for e in l:
        if isinstance(e, list):
            ret.extend(e)
        else:
            ret.append(e)
    return ret

def iterate_format(video_format, for_widgets=True):
    """提供对控件或参数的迭代器"""
    def indirector(cont, index):
        if isinstance(cont[index], list) and (not for_widgets
          or len(cont[index]) > 1 and not isinstance(cont[index][1], dict)):
            inp = yield cont[index]
            if inp is not None:
                cont[index] = inp
                yield
    for k in video_format:
        if k == "extra_widgets":
            if for_widgets:
                yield from video_format["extra_widgets"]
        elif k.endswith("_pass"):
            for i in range(len(video_format[k])):
                yield from indirector(video_format[k], i)
            if not for_widgets:
                video_format[k] = flatten_list(video_format[k])
        else:
            yield from indirector(video_format, k)

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
video_formats_path = os.path.join(current_dir, "video_formats.json")

def get_video_formats():
    """获取所有支持的视频格式"""
    formats = []
    format_widgets = {}
    
    # 首先添加内置格式
    for format_name, video_format in DEFAULT_VIDEO_FORMATS.items():
        # 为每种格式添加编码器选择控件
        encoder_choices = list(video_format["encoders"].keys())
        encoder_widget = [
            "encoder", 
            ["list", encoder_choices],
            {"default": video_format["default_encoder"], "display_name": "编码器"}
        ]
        
        # 使用友好的显示名称，去掉"video/"前缀
        friendly_name = format_name.upper() if format_name != "gif" else "GIF"
        formats.append(("video/" + format_name, friendly_name))
        format_widgets["video/"+ format_name] = [encoder_widget]
    
    # 添加图像格式
    formats.append(("image/gif", "GIF图像"))
    formats.append(("image/webp", "WebP图像"))
    
    # 检查外部格式文件是否存在
    if not os.path.exists(video_formats_path):
        print(f"Info: Using built-in video formats only, external config not found at {video_formats_path}")
        return formats, format_widgets
    
    try:
        with open(video_formats_path, 'r', encoding='utf-8') as stream:
            all_formats = json.load(stream)
            
        # 处理外部格式配置
        for format_name, video_format in all_formats.items():
            # 检查是否需要 gifski
            if "gifski_pass" in video_format:
                # 跳过gif格式检查，只在需要时检查
                pass
            
            widgets = list(iterate_format(video_format))
            friendly_name = format_name.upper()
            formats.append(("video/" + format_name, friendly_name))
            
            if len(widgets) > 0:
                format_widgets["video/"+ format_name] = widgets
                
    except Exception as e:
        print(f"Error loading external video formats: {e}")
    
    return formats, format_widgets

def apply_format_widgets(format_name, kwargs):
    """应用格式控件设置"""
    # 首先检查是否是内置格式
    if format_name in DEFAULT_VIDEO_FORMATS:
        video_format = DEFAULT_VIDEO_FORMATS[format_name].copy()
        
        # 获取选择的编码器
        encoder = kwargs.get("encoder", video_format["default_encoder"])
        if encoder not in video_format["encoders"]:
            encoder = video_format["default_encoder"]
            
        # 合并编码器特定的参数
        encoder_settings = video_format["encoders"][encoder]
        for key, value in encoder_settings.items():
            video_format[key] = value
            
    else:
        # 检查外部格式文件
        if not os.path.exists(video_formats_path):
            raise ValueError(f"Format {format_name} not found in built-in formats and external config not found at {video_formats_path}")
        
        try:
            with open(video_formats_path, 'r', encoding='utf-8') as stream:
                all_formats = json.load(stream)
                
            if format_name not in all_formats:
                raise ValueError(f"Format {format_name} not found in video_formats.json")
                
            video_format = all_formats[format_name]
        except Exception as e:
            raise ValueError(f"Failed to load video format {format_name}: {e}")
    
    # 设置默认值
    for w in iterate_format(video_format):
        if w[0] not in kwargs:
            if len(w) > 2 and 'default' in w[2]:
                default = w[2]['default']
            else:
                if type(w[1]) is list:
                    default = w[1][0]
                else:
                    default = {"BOOLEAN": False, "INT": 0, "FLOAT": 0, "STRING": ""}[w[1]]
            kwargs[w[0]] = default
    
    # 应用格式设置
    wit = iterate_format(video_format, False)
    for w in wit:
        while isinstance(w, list):
            if len(w) == 1:
                w = [Template(x).substitute(**kwargs) for x in w[0]]
                break
            elif isinstance(w[1], dict):
                w = w[1][str(kwargs[w[0]])]
            elif len(w) > 3:
                w = Template(w[3]).substitute(val=kwargs[w[0]])
            else:
                w = str(kwargs[w[0]])
        wit.send(w)
    return video_format

def tensor_to_int(tensor, bits):
    """将张量转换为指定位深的整数"""
    tensor = tensor.cpu().numpy() * (2**bits-1)
    return np.clip(tensor, 0, (2**bits-1))

def tensor_to_shorts(tensor):
    """将张量转换为16位整数"""
    return tensor_to_int(tensor, 16).astype(np.uint16)

def tensor_to_bytes(tensor):
    """将张量转换为8位整数"""
    return tensor_to_int(tensor, 8).astype(np.uint8)

def ffmpeg_process(args, video_format, video_metadata, file_path, env, save_metadata=True):
    """处理FFmpeg进程"""
    res = None
    frame_data = yield
    total_frames_output = 0
    
    # 创建临时目录用于存储中间文件
    temp_dir = tempfile.mkdtemp()
    try:
        if save_metadata and video_format.get('save_metadata', 'False') != 'False':
            metadata = json.dumps(video_metadata)
            metadata_path = os.path.join(temp_dir, "metadata.txt")
            metadata = metadata.replace("\\","\\\\")
            metadata = metadata.replace(";","\\;")
            metadata = metadata.replace("#","\\#")
            metadata = metadata.replace("=","\\=")
            metadata = metadata.replace("\n","\\\n")
            metadata = "comment=" + metadata
            with open(metadata_path, "w", encoding='utf-8') as f:
                f.write(";FFMETADATA1\n")
                f.write(metadata)
            m_args = args[:1] + ["-i", metadata_path] + args[1:] + ["-metadata", "creation_time=now"]
            with subprocess.Popen(m_args + [file_path], stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE, env=env) as proc:
                try:
                    while frame_data is not None:
                        proc.stdin.write(frame_data)
                        frame_data = yield
                        total_frames_output += 1
                    proc.stdin.flush()
                    proc.stdin.close()
                    res = proc.stderr.read()
                except BrokenPipeError as e:
                    err = proc.stderr.read()
                    if os.path.exists(file_path):
                        os.remove(file_path)  # 清理失败的文件
                    raise Exception("An error occurred in the ffmpeg subprocess:\n" \
                            + err.decode(*ENCODE_ARGS))
        else:
            with subprocess.Popen(args + [file_path], stderr=subprocess.PIPE,
                                  stdin=subprocess.PIPE, env=env) as proc:
                try:
                    while frame_data is not None:
                        proc.stdin.write(frame_data)
                        frame_data = yield
                        total_frames_output += 1
                    proc.stdin.flush()
                    proc.stdin.close()
                    res = proc.stderr.read()
                except BrokenPipeError as e:
                    res = proc.stderr.read()
                    if os.path.exists(file_path):
                        os.remove(file_path)  # 清理失败的文件
                    raise Exception("An error occurred in the ffmpeg subprocess:\n" \
                            + res.decode(*ENCODE_ARGS))
        yield total_frames_output
        if len(res) > 0:
            print(res.decode(*ENCODE_ARGS), end="", file=sys.stderr)
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

def gifski_process(args, dimensions, video_format, file_path, env, gifski_path):
    """处理Gifski进程"""
    frame_data = yield
    try:
        with subprocess.Popen(args + video_format['main_pass'] + ['-f', 'yuv4mpegpipe', '-'],
                              stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, env=env) as procff:
            with subprocess.Popen([gifski_path] + video_format['gifski_pass']
                                  + ['-W', f'{dimensions[0]}', '-H', f'{dimensions[1]}']
                                  + ['-q', '-o', file_path, '-'], stderr=subprocess.PIPE,
                                  stdin=procff.stdout, stdout=subprocess.PIPE,
                                  env=env) as procgs:
                try:
                    while frame_data is not None:
                        procff.stdin.write(frame_data)
                        frame_data = yield
                    procff.stdin.flush()
                    procff.stdin.close()
                    resff = procff.stderr.read()
                    resgs = procgs.stderr.read()
                    outgs = procgs.stdout.read()
                except BrokenPipeError as e:
                    procff.stdin.close()
                    resff = procff.stderr.read()
                    resgs = procgs.stderr.read()
                    if os.path.exists(file_path):
                        os.remove(file_path)  # 清理失败的文件
                    raise Exception("An error occurred while creating gifski output\n" \
                            + "Make sure you are using gifski --version >=1.32.0\nffmpeg: " \
                            + resff.decode(*ENCODE_ARGS) + '\ngifski: ' + resgs.decode(*ENCODE_ARGS))
        if len(resff) > 0:
            print(resff.decode(*ENCODE_ARGS), end="", file=sys.stderr)
        if len(resgs) > 0:
            print(resgs.decode(*ENCODE_ARGS), end="", file=sys.stderr)
        if len(outgs) > 0:
            print(outgs.decode(*ENCODE_ARGS))
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)  # 清理失败的文件
        raise e

def to_pingpong(inp):
    """生成来回播放的帧序列"""
    if not hasattr(inp, "__getitem__"):
        inp = list(inp)
    yield from inp
    for i in range(len(inp)-2,0,-1):
        yield inp[i]

def merge_filter_args(args, filter_arg='-filter_complex'):
    """合并过滤器参数"""
    filters = []
    i = 0
    while i < len(args):
        if args[i] == filter_arg:
            i += 1
            if i < len(args):
                filters.append(args[i])
        i += 1
    if filters:
        new_args = []
        i = 0
        while i < len(args):
            if args[i] == filter_arg:
                i += 1
                if i < len(args):
                    new_args.extend([filter_arg, ';'.join(filters)])
            else:
                new_args.append(args[i])
            i += 1
        return new_args
    return args

def find_ffmpeg_path():
    """查找FFmpeg路径"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        try:
            ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg")
            if os.path.exists(ffmpeg_path):
                return ffmpeg_path
        except Exception:
            pass
        return "ffmpeg"  # 回退到系统路径

def find_gifski_path():
    """查找Gifski路径"""
    try:
        gifski_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gifski")
        if os.path.exists(gifski_path):
            return gifski_path
        
        # 检查系统路径
        possible_paths = [
            "gifski",
            "/usr/bin/gifski",
            "/usr/local/bin/gifski",
            os.path.expanduser("~/.cargo/bin/gifski")
        ]
        
        for p in possible_paths:
            try:
                subprocess.run([p, "--version"], capture_output=True, check=True)
                return p
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
                
        return None
    except Exception:
        return None

def ensure_directory_exists(path):
    """确保目录存在，如果不存在则创建"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}")
        return False



def get_safe_path(base_path, filename_prefix, is_output=True):
    """
    获取安全的文件保存路径
    如果base_path存在且可写，则使用base_path
    否则使用ComfyUI的默认目录
    """
    if base_path and base_path.strip() and os.path.isdir(base_path) and os.access(base_path, os.W_OK):
        # 使用自定义路径
        print(f"使用自定义保存路径: {base_path}")
        full_output_folder = base_path
        filename = filename_prefix
        subfolder = ""
    else:
        # 使用ComfyUI默认路径
        output_dir = (
            folder_paths.get_output_directory()
            if is_output
            else folder_paths.get_temp_directory()
        )
        (
            full_output_folder,
            filename,
            _,
            subfolder,
            _,
        ) = folder_paths.get_save_image_path(filename_prefix, output_dir)
        print(f"使用默认保存路径: {full_output_folder}")
    
    return full_output_folder, filename, subfolder

class SyntheticVideo:
    @classmethod
    def INPUT_TYPES(s):
        # 修复格式列表定义 - 使用字符串列表而不是元组列表
        format_choices = [
            "video/mp4",
            "video/webm",
            "video/avi",
            "video/mov",
            "video/gif",
            "video/mkv",
            "video/flv",
            "image/gif",
            "image/webp"
        ]
        
        # 构建输入类型字典
        input_types = {
            "required": {
                "images": ("IMAGE",),
                "frame_rate": (
                    "FLOAT",
                    {"default": 16, "min": 1, "step": 1},
                ),
                "loop_count": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),
                "skip_frames": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1, "display_name": "跳过前X帧"}),
                "filename_prefix": ("STRING", {"default": "QING"}),
                "format": (format_choices, {"default": "video/mp4"}),
                "pingpong": ("BOOLEAN", {"default": False}),
                "save_output": ("BOOLEAN", {"default": True}),
                "save_metadata": ("BOOLEAN", {"default": True, "display_name": "保存元数据"}),
            },
            "optional": {
                "custom_save_path": ("STRING", {"default": "", "display_name": "自定义保存路径"}),
                "audio": ("AUDIO",),
                "custom_ffmpeg_args": ("STRING", {"default": "", "multiline": True}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }
        
        # 为所有视频格式添加编码器选项，使用友好的显示名称
        for format_name, video_format in DEFAULT_VIDEO_FORMATS.items():
            encoders = list(video_format["encoders"].keys())
            default_encoder = video_format["default_encoder"]
            
            # 使用友好的显示名称
            display_name = f"{format_name.upper()}编码器"
            input_types["required"][f"encoder_{format_name}"] = (
                encoders,
                {
                    "default": default_encoder, 
                    "display_name": display_name,
                    "tooltip": f"当选择{format_name.upper()}格式时使用此编码器"
                }
            )
        
        return input_types

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)
    OUTPUT_NODE = True
    CATEGORY = "视频/合成"
    FUNCTION = "combine_video"

    def combine_video(
        self,
        frame_rate: int,
        loop_count: int,
        skip_frames: int = 0,
        images=None,
        filename_prefix="QING",
        format="video/mp4",  # 这里设置默认值
        pingpong=False,
        save_output=True,
        save_metadata=True,
        prompt=None,
        extra_pnginfo=None,
        custom_save_path="",
        audio=None,
        custom_ffmpeg_args="",
        unique_id=None,
        **kwargs
    ):
        try:
            print(f"SyntheticVideo: 开始处理视频合成...")
            print(f"输入参数: frame_rate={frame_rate}, loop_count={loop_count}, skip_frames={skip_frames}")
            print(f"图像数量: {len(images) if images is not None else 'None'}")
            print(f"格式: {format}, 文件名前缀: {filename_prefix}")
            print(f"自定义保存路径: '{custom_save_path}'")
            
            if images is None:
                print("错误: 没有输入图像")
                return ("",)
                
            # 跳过指定数量的帧
            if skip_frames > 0 and skip_frames < len(images):
                images = images[skip_frames:]
                print(f"已跳过前 {skip_frames} 帧，剩余 {len(images)} 帧")
            elif skip_frames >= len(images):
                raise ValueError(f"跳过的帧数 ({skip_frames}) 不能大于或等于总帧数 ({len(images)})")
                
            # 查找ffmpeg路径
            print(f"正在查找FFmpeg...")
            ffmpeg_path = find_ffmpeg_path()
            print(f"FFmpeg路径: {ffmpeg_path}")
            
            if ffmpeg_path is None or not os.path.exists(ffmpeg_path):
                print("警告: FFmpeg未找到，视频格式可能无法生成")
            
            # 只有在需要gif格式时才查找gifski
            gifski_path = None
            if format == "image/gif" or format.startswith("video/gif"):
                gifski_path = find_gifski_path()
                if gifski_path is None:
                    print("Warning: gifski not found, GIF quality may be lower")

            if isinstance(images, torch.Tensor) and images.size(0) == 0:
                return ("",)
                
            num_frames = len(images)
            first_image = images[0]
            
            # 使用生成器处理图像，减少内存使用
            def image_generator():
                for img in images:
                    yield img
                    
            images_iter = image_generator()
            
            # 获取输出信息 - 使用自定义路径或默认路径
            print(f"正在获取保存路径...")
            full_output_folder, filename, subfolder = get_safe_path(
                custom_save_path, filename_prefix, save_output
            )
            print(f"最终保存路径: {full_output_folder}")
            print(f"文件名: {filename}")
            
            # 确保输出目录存在
            if not ensure_directory_exists(full_output_folder):
                # 如果自定义目录创建失败，回退到默认目录
                output_dir = (
                    folder_paths.get_output_directory()
                    if save_output
                    else folder_paths.get_temp_directory()
                )
                (
                    full_output_folder,
                    filename,
                    _,
                    subfolder,
                    _,
                ) = folder_paths.get_save_image_path(filename_prefix, output_dir)
            
            output_files = []

            metadata = PngInfo()
            video_metadata = {}
            if save_metadata:
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                    video_metadata["prompt"] = prompt
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                        video_metadata[x] = extra_pnginfo[x]
                metadata.add_text("CreationTime", datetime.datetime.now().isoformat(" ")[:19])

            # comfy counter workaround
            max_counter = 0
            matcher = re.compile(f"{re.escape(filename)}_(\\d+)\\D*\\..+", re.IGNORECASE)
            try:
                if os.path.exists(full_output_folder) and os.path.isdir(full_output_folder):
                    for existing_file in os.listdir(full_output_folder):
                        match = matcher.fullmatch(existing_file)
                        if match:
                            file_counter = int(match.group(1))
                            if file_counter > max_counter:
                                max_counter = file_counter
            except Exception as e:
                print(f"Warning: Could not scan directory for existing files: {e}")
            counter = max_counter + 1

            # 保存第一帧为PNG以保留元数据（如果启用）
            if save_metadata:
                first_image_file = f"{filename}_{counter:05}.png"
                file_path = os.path.join(full_output_folder, first_image_file)
                Image.fromarray(tensor_to_bytes(first_image)).save(
                    file_path,
                    pnginfo=metadata,
                    compress_level=4,
                )
                output_files.append(file_path)

            format_type, format_ext = format.split("/")
            final_file_path = ""
            
            if format_type == "image":
                image_kwargs = {}
                if format_ext == "gif":
                    image_kwargs['disposal'] = 2
                if format_ext == "webp":
                    exif = Image.Exif()
                    exif[ExifTags.IFD.Exif] = {36867: datetime.datetime.now().isoformat(" ")[:19]}
                    image_kwargs['exif'] = exif
                    image_kwargs['lossless'] = kwargs.get("lossless", True)
                file = f"{filename}_{counter:05}.{format_ext}"
                file_path = os.path.join(full_output_folder, file)
                if pingpong:
                    images_iter = to_pingpong(list(images_iter))
                    
                def frames_gen(images):
                    for i in images:
                        yield Image.fromarray(tensor_to_bytes(i))
                        
                frames = frames_gen(images_iter)
                first_frame = next(frames)
                first_frame.save(
                    file_path,
                    format=format_ext.upper(),
                    save_all=True,
                    append_images=frames,
                    duration=round(1000 / frame_rate),
                    loop=loop_count,
                    compress_level=4,
                    **image_kwargs
                )
                output_files.append(file_path)
                final_file_path = file_path
                
            else:
                print(f"开始处理视频格式: {format_ext}")
                if ffmpeg_path is None or not os.path.exists(ffmpeg_path):
                    print(f"错误: FFmpeg未找到，路径: {ffmpeg_path}")
                    raise ProcessLookupError(f"ffmpeg is required for video outputs and could not be found.")

                # 获取选择的编码器
                encoder_key = f"encoder_{format_ext}"
                encoder_name = kwargs.get(encoder_key, DEFAULT_VIDEO_FORMATS[format_ext]["default_encoder"])
                
                # 检查是否需要gifski并且可用
                if format_ext == "gif" and gifski_path is not None and os.path.exists(gifski_path):
                    has_alpha = first_image.shape[-1] == 4
                    kwargs["has_alpha"] = has_alpha
                    kwargs["encoder"] = encoder_name
                    video_format = apply_format_widgets(format_ext, kwargs)
                    dim_alignment = video_format.get("dim_alignment", 2)
                else:
                    # 对于其他格式，使用内置配置
                    if format_ext in DEFAULT_VIDEO_FORMATS:
                        kwargs["encoder"] = encoder_name
                        video_format = apply_format_widgets(format_ext, kwargs)
                    else:
                        # 尝试从外部配置加载
                        try:
                            kwargs["encoder"] = encoder_name
                            video_format = apply_format_widgets(format_ext, kwargs)
                        except Exception:
                            # 回退到mp4格式
                            print(f"Warning: Format {format_ext} not found, using MP4 as fallback")
                            format_ext = "mp4"
                            kwargs["encoder"] = encoder_name
                            video_format = apply_format_widgets("mp4", kwargs)
                    
                    has_alpha = first_image.shape[-1] == 4
                    kwargs["has_alpha"] = has_alpha
                    dim_alignment = video_format.get("dim_alignment", 2)

                # 处理图像尺寸对齐
                if (first_image.shape[1] % dim_alignment) or (first_image.shape[0] % dim_alignment):
                    to_pad = (-first_image.shape[1] % dim_alignment,
                              -first_image.shape[0] % dim_alignment)
                    padding = (to_pad[0]//2, to_pad[0] - to_pad[0]//2,
                               to_pad[1]//2, to_pad[1] - to_pad[1]//2)
                    padfunc = torch.nn.ReplicationPad2d(padding)
                    def pad(image):
                        image = image.permute((2,0,1))
                        padded = padfunc(image.to(dtype=torch.float32))
                        return padded.permute((1,2,0))
                    images_iter = map(pad, images_iter)
                    dimensions = (-first_image.shape[1] % dim_alignment + first_image.shape[1],
                                  -first_image.shape[0] % dim_alignment + first_image.shape[0])
                    print("输出图像分辨率不符合要求，已自动填充对齐")
                else:
                    dimensions = (first_image.shape[1], first_image.shape[0])
                    
                if loop_count > 0:
                    loop_args = ["-vf", "loop=loop=" + str(loop_count)+":size=" + str(num_frames)]
                else:
                    loop_args = []
                    
                if pingpong:
                    images_iter = to_pingpong(list(images_iter))
                    
                if video_format.get('input_color_depth', '8bit') == '16bit':
                    images_iter = map(tensor_to_shorts, images_iter)
                    if has_alpha:
                        i_pix_fmt = 'rgba64'
                    else:
                        i_pix_fmt = 'rgb48'
                else:
                    images_iter = map(tensor_to_bytes, images_iter)
                    if has_alpha:
                        i_pix_fmt = 'rgba'
                    else:
                        i_pix_fmt = 'rgb24'
                        
                file = f"{filename}_{counter:05}.{video_format['extension']}"
                file_path = os.path.join(full_output_folder, file)
                bitrate_arg = []
                bitrate = video_format.get('bitrate')
                if bitrate is not None:
                    bitrate_arg = ["-b:v", str(bitrate) + "M" if video_format.get('megabit') == 'True' else str(bitrate) + "K"]
                    
                args = [ffmpeg_path, "-v", "error", "-f", "rawvideo", "-pix_fmt", i_pix_fmt,
                        "-color_range", "pc", "-colorspace", "rgb", "-color_primaries", "bt709",
                        "-color_trc", video_format.get("fake_trc", "iec61966-2-1"),
                        "-s", f"{dimensions[0]}x{dimensions[1]}", "-r", str(frame_rate), "-i", "-"] \
                        + loop_args

                # 添加自定义FFmpeg参数
                if custom_ffmpeg_args.strip():
                    custom_args = [arg.strip() for arg in custom_ffmpeg_args.split() if arg.strip()]
                    args.extend(custom_args)

                images_iter = map(lambda x: x.tobytes(), images_iter)
                env = os.environ.copy()
                if "environment" in video_format:
                    env.update(video_format["environment"])

                if "pre_pass" in video_format:
                    # 对于pre_pass，我们需要将所有图像数据收集到内存中
                    images_data = b''.join(images_iter)
                    temp_dir = tempfile.mkdtemp()
                    try:
                        in_args_len = args.index("-i") + 2
                        pre_pass_args = args[:in_args_len] + video_format['pre_pass']
                        
                        pre_pass_args = merge_filter_args(pre_pass_args)
                        try:
                            subprocess.run(pre_pass_args, input=images_data, env=env,
                                           capture_output=True, check=True)
                        except subprocess.CalledProcessError as e:
                            raise Exception("An error occurred in the ffmpeg prepass:\n" + e.stderr.decode(*ENCODE_ARGS))
                    finally:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    # 重新创建图像迭代器，因为数据已处理
                    images_iter = image_generator()
                    images_iter = map(lambda x: x.tobytes(), images_iter)

                if "inputs_main_pass" in video_format:
                    in_args_len = args.index("-i") + 2
                    args = args[:in_args_len] + video_format['inputs_main_pass'] + args[in_args_len:]

                try:
                    if 'gifski_pass' in video_format and gifski_path and os.path.exists(gifski_path):
                        output_process = gifski_process(args, dimensions, video_format, file_path, env, gifski_path)
                    else:
                        args += video_format['main_pass'] + bitrate_arg
                        args = merge_filter_args(args)
                        output_process = ffmpeg_process(args, video_format, video_metadata, file_path, env, save_metadata)
                        
                    output_process.send(None)
                    for image in images_iter:
                        output_process.send(image)
                        
                    try:
                        total_frames_output = output_process.send(None)
                        output_process.send(None)
                    except StopIteration:
                        pass
                        
                    output_files.append(file_path)
                    final_file_path = file_path

                    if audio is not None and "audio_pass" in video_format:
                        try:
                            a_waveform = audio['waveform']
                        except KeyError:
                            a_waveform = None
                            
                        if a_waveform is not None:
                            output_file_with_audio = f"{filename}_{counter:05}-audio.{video_format['extension']}"
                            output_file_with_audio_path = os.path.join(full_output_folder, output_file_with_audio)
                            
                            channels = audio['waveform'].size(1)
                            min_audio_dur = total_frames_output / frame_rate + 1
                            if video_format.get('trim_to_audio', 'False') != 'False':
                                apad = []
                            else:
                                apad = ["-af", "apad=whole_dur="+str(min_audio_dur)]
                                
                            mux_args = [ffmpeg_path, "-v", "error", "-n", "-i", file_path,
                                        "-ar", str(audio['sample_rate']), "-ac", str(channels),
                                        "-f", "f32le", "-i", "-", "-c:v", "copy"] \
                                        + video_format["audio_pass"] \
                                        + apad + ["-shortest", output_file_with_audio_path]

                            audio_data = audio['waveform'].squeeze(0).transpose(0,1).numpy().tobytes()
                            mux_args = merge_filter_args(mux_args, '-af')
                            try:
                                res = subprocess.run(mux_args, input=audio_data,
                                                     env=env, capture_output=True, check=True)
                            except subprocess.CalledProcessError as e:
                                if os.path.exists(output_file_with_audio_path):
                                    os.remove(output_file_with_audio_path)
                                raise Exception("An error occurred in the ffmpeg subprocess:\n" + e.stderr.decode(*ENCODE_ARGS))
                            if res.stderr:
                                print(res.stderr.decode(*ENCODE_ARGS), end="", file=sys.stderr)
                            
                            # 删除原始无音频文件，并将带音频文件重命名为原始文件名
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            os.rename(output_file_with_audio_path, file_path)
                            final_file_path = file_path

                except Exception as e:
                    # 清理可能创建的部分文件
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise e

            # 显示最终视频信息
            if final_file_path and os.path.exists(final_file_path):
                video_size = os.path.getsize(final_file_path) / (1024 * 1024)  # MB
                print(f"视频已生成: {final_file_path}")
                print(f"文件大小: {video_size:.1f} MB")
                print(f"视频信息: {len(images)}帧, {frame_rate}fps, 时长{len(images)/frame_rate:.1f}秒")

            return (final_file_path,)
            
        except Exception as e:
            # 捕获所有异常并提供更友好的错误信息
            error_msg = f"视频合成失败: {str(e)}"
            print(f"Error: {error_msg}")
            # 返回空路径而不是抛出异常，以避免中断整个工作流
            return ("",)

# For ComfyUI node registration
NODE_CLASS_MAPPINGS = {
    "VHS_SyntheticVideo": SyntheticVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VHS_SyntheticVideo": "Synthetic Video",
}
