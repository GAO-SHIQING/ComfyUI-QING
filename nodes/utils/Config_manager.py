# -*- coding: utf-8 -*-
"""
配置文件管理节点
功能：导出和导入ComfyUI的配置信息、工作流、输入输出文件等
"""

import os
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


class ConfigExport:
    """
    配置文件导出节点
    功能：导出ComfyUI的各类配置文件和资源
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "export_node_info": ("BOOLEAN", {
                    "default": True,
                    "label_on": "开启",
                    "label_off": "关闭",
                    "tooltip": "导出节点信息（custom_nodes列表和配置）"
                }),
                "export_frontend_settings": ("BOOLEAN", {
                    "default": True,
                    "label_on": "开启",
                    "label_off": "关闭",
                    "tooltip": "导出前端设置（界面配置、用户偏好）"
                }),
                "export_dependencies": ("BOOLEAN", {
                    "default": True,
                    "label_on": "开启",
                    "label_off": "关闭",
                    "tooltip": "导出环境依赖（requirements.txt、已安装包列表）"
                }),
                "export_workflows": ("BOOLEAN", {
                    "default": False,
                    "label_on": "开启",
                    "label_off": "关闭",
                    "tooltip": "导出工作流文件（workflow目录）"
                }),
                "export_inputs": ("BOOLEAN", {
                    "default": False,
                    "label_on": "开启",
                    "label_off": "关闭",
                    "tooltip": "导出输入文件（input目录，可能较大）"
                }),
                "export_outputs": ("BOOLEAN", {
                    "default": False,
                    "label_on": "开启",
                    "label_off": "关闭",
                    "tooltip": "导出输出文件（output目录，可能较大）"
                }),
                "output_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "自定义保存路径（绝对路径），留空则保存到默认路径"
                }),
            },
        }

    CATEGORY = "🎨QING/配置管理"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_analysis",)
    FUNCTION = "export_config"
    OUTPUT_NODE = True

    def export_config(self, export_node_info, export_frontend_settings, export_dependencies,
                     export_workflows, export_inputs, export_outputs, output_path):
        """
        主处理函数：导出ComfyUI配置
        
        参数:
            export_node_info: 是否导出节点信息
            export_frontend_settings: 是否导出前端设置
            export_dependencies: 是否导出环境依赖
            export_workflows: 是否导出工作流
            export_inputs: 是否导出输入文件
            export_outputs: 是否导出输出文件
            output_path: 自定义输出路径
            
        返回:
            tuple: (结果分析文本,)
        """
        try:
            # 获取ComfyUI根目录
            comfyui_root = self._get_comfyui_root()
            
            # 确定输出路径
            if output_path and output_path.strip():
                export_dir = Path(output_path.strip())
                # 验证自定义路径
                if not export_dir.is_absolute():
                    return ("❌ 错误：输出路径必须是绝对路径\n当前路径：" + str(export_dir),)
            else:
                # 默认路径：ComfyUI根目录/output/config_backups
                export_dir = comfyui_root / "output" / "config_backups"
            
            # 创建导出目录
            try:
                export_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return (f"❌ 错误：无权限访问输出路径\n路径：{export_dir}",)
            except Exception as e:
                return (f"❌ 错误：无法创建输出目录\n路径：{export_dir}\n错误：{str(e)}",)
            
            # 创建时间戳文件名（避免重复）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"comfyui_config_{timestamp}.zip"
            zip_path = export_dir / zip_filename
            
            # 处理文件名冲突（极少情况）
            counter = 1
            while zip_path.exists():
                zip_filename = f"comfyui_config_{timestamp}_{counter}.zip"
                zip_path = export_dir / zip_filename
                counter += 1
            
            # 导出统计
            stats = {
                "exported_items": [],
                "skipped_items": [],
                "file_count": 0,
                "total_size": 0,
                "errors": []
            }
            
            # 创建临时目录用于组织文件（确保唯一性）
            temp_counter = 0
            temp_dir = export_dir / f"temp_{timestamp}"
            while temp_dir.exists():
                temp_counter += 1
                temp_dir = export_dir / f"temp_{timestamp}_{temp_counter}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # 导出各类配置
                if export_node_info:
                    self._export_node_info(comfyui_root, temp_dir, stats)
                
                if export_frontend_settings:
                    self._export_frontend_settings(comfyui_root, temp_dir, stats)
                
                if export_dependencies:
                    self._export_dependencies(comfyui_root, temp_dir, stats)
                
                if export_workflows:
                    self._export_workflows(comfyui_root, temp_dir, stats)
                
                if export_inputs:
                    self._export_inputs(comfyui_root, temp_dir, stats)
                
                if export_outputs:
                    self._export_outputs(comfyui_root, temp_dir, stats)
                
                # 打包成zip文件
                if stats["file_count"] > 0:
                    # 创建导出元数据
                    self._create_export_metadata(temp_dir, timestamp, stats,
                                                export_node_info, export_frontend_settings,
                                                export_dependencies, export_workflows,
                                                export_inputs, export_outputs)
                    
                    self._create_zip(temp_dir, zip_path, stats)
                    result = self._generate_success_report(zip_path, stats, timestamp)
                else:
                    result = "⚠️ 未选择任何导出项，未生成导出文件"
                
            finally:
                # 清理临时目录
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
            return (result,)
            
        except Exception as e:
            error_msg = f"❌ 导出失败\n\n错误信息：{str(e)}\n\n请检查路径权限和磁盘空间"
            return (error_msg,)
    
    def _get_comfyui_root(self):
        """获取ComfyUI根目录"""
        try:
            import folder_paths
            # 尝试从folder_paths获取基础路径
            base_path = folder_paths.base_path
            return Path(base_path)
        except:
            # 回退：从当前文件向上查找
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / "main.py").exists() or (current / "comfyui").exists():
                    return current
                current = current.parent
            # 最后回退
            return Path.cwd()
    
    def _get_github_url(self, node_path):
        """获取节点的GitHub地址"""
        try:
            git_config = node_path / ".git" / "config"
            if not git_config.exists():
                return ""
            
            # 读取git config文件
            with open(git_config, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找remote "origin"的url
            import re
            # 匹配 url = xxx 格式
            url_match = re.search(r'url\s*=\s*(.+)', content)
            if url_match:
                url = url_match.group(1).strip()
                
                # 转换SSH格式到HTTPS格式
                # git@github.com:user/repo.git -> https://github.com/user/repo
                if url.startswith('git@github.com:'):
                    url = url.replace('git@github.com:', 'https://github.com/')
                
                # 移除.git后缀
                if url.endswith('.git'):
                    url = url[:-4]
                
                return url
            
            return ""
            
        except Exception as e:
            # 如果获取失败，返回空字符串而不是引发错误
            return ""
    
    def _create_export_metadata(self, temp_dir, timestamp, stats, 
                                export_node_info, export_frontend_settings,
                                export_dependencies, export_workflows,
                                export_inputs, export_outputs):
        """创建导出元数据文件"""
        try:
            import sys
            import platform
            
            metadata = {
                "export_info": {
                    "timestamp": timestamp,
                    "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "exporter": "ComfyUI-QING Config Manager",
                    "version": "1.0.0"
                },
                "export_options": {
                    "node_info": export_node_info,
                    "frontend_settings": export_frontend_settings,
                    "dependencies": export_dependencies,
                    "workflows": export_workflows,
                    "inputs": export_inputs,
                    "outputs": export_outputs
                },
                "statistics": {
                    "total_files": stats["file_count"],
                    "exported_items": stats["exported_items"],
                    "errors": stats["errors"]
                },
                "system_info": {
                    "python_version": sys.version,
                    "platform": platform.platform(),
                    "os": platform.system(),
                    "architecture": platform.machine()
                }
            }
            
            metadata_file = temp_dir / "export_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            stats["file_count"] += 1
            
        except Exception as e:
            stats["errors"].append(f"创建元数据失败: {str(e)}")
    
    def _export_node_info(self, root, temp_dir, stats):
        """导出节点信息"""
        try:
            node_info_dir = temp_dir / "node_info"
            node_info_dir.mkdir(exist_ok=True)
            
            # 导出custom_nodes目录列表
            custom_nodes_dir = root / "custom_nodes"
            if custom_nodes_dir.exists():
                nodes_list = []
                for item in custom_nodes_dir.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        node_data = {
                            "name": item.name,
                            "path": str(item.relative_to(root)),
                            "github_url": self._get_github_url(item),
                            "has_init": (item / "__init__.py").exists(),
                            "has_requirements": (item / "requirements.txt").exists(),
                            "has_pyproject": (item / "pyproject.toml").exists(),
                            "has_readme": any((item / f"README{ext}").exists() for ext in [".md", ".MD", ".txt", ""]),
                            "has_license": any((item / f"LICENSE{ext}").exists() for ext in ["", ".txt", ".md"]),
                        }
                        
                        # 尝试获取pyproject.toml中的版本信息
                        pyproject_file = item / "pyproject.toml"
                        if pyproject_file.exists():
                            try:
                                with open(pyproject_file, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    # 简单提取version字段
                                    import re
                                    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                                    if version_match:
                                        node_data["version"] = version_match.group(1)
                            except:
                                pass
                        
                        nodes_list.append(node_data)
                
                # 保存节点列表
                nodes_file = node_info_dir / "custom_nodes_list.json"
                with open(nodes_file, 'w', encoding='utf-8') as f:
                    json.dump(nodes_list, f, indent=2, ensure_ascii=False)
                
                stats["exported_items"].append(f"节点信息 ({len(nodes_list)}个节点)")
                stats["file_count"] += 1
            
        except Exception as e:
            stats["errors"].append(f"导出节点信息失败: {str(e)}")
    
    def _export_frontend_settings(self, root, temp_dir, stats):
        """导出前端设置"""
        try:
            settings_dir = temp_dir / "frontend_settings"
            settings_dir.mkdir(exist_ok=True)
            
            # 可能的设置文件位置
            setting_paths = [
                root / "user" / "default" / "comfy.settings.json",
                root / "user" / "comfy.settings.json",
                root / "web" / "user.settings.json",
            ]
            
            exported_count = 0
            for setting_path in setting_paths:
                if setting_path.exists():
                    dest = settings_dir / setting_path.name
                    shutil.copy2(setting_path, dest)
                    exported_count += 1
            
            if exported_count > 0:
                stats["exported_items"].append("前端设置")
                stats["file_count"] += exported_count
            
        except Exception as e:
            stats["errors"].append(f"导出前端设置失败: {str(e)}")
    
    def _export_dependencies(self, root, temp_dir, stats):
        """导出环境依赖（整个Python环境的所有依赖）"""
        try:
            deps_dir = temp_dir / "dependencies"
            deps_dir.mkdir(exist_ok=True)
            
            # 获取Python版本信息
            import sys
            import platform
            
            # 导出环境信息
            env_info_file = deps_dir / "environment_info.txt"
            with open(env_info_file, 'w', encoding='utf-8') as f:
                f.write("# Python环境信息\n")
                f.write(f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Python版本: {sys.version}\n")
                f.write(f"Python路径: {sys.executable}\n")
                f.write(f"操作系统: {platform.system()} {platform.release()}\n")
                f.write(f"平台: {platform.platform()}\n")
                f.write(f"架构: {platform.machine()}\n\n")
            
            stats["file_count"] += 1
            
            # 导出pip freeze结果（整个Python环境的所有已安装包）
            pip_success = False
            try:
                import subprocess
                
                # 尝试多种pip调用方式
                pip_commands = [
                    ['pip', 'freeze'],
                    [sys.executable, '-m', 'pip', 'freeze'],  # python -m pip freeze
                    ['pip3', 'freeze'],
                ]
                
                for cmd in pip_commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        if result.returncode == 0 and result.stdout.strip():
                            freeze_file = deps_dir / "python_packages.txt"
                            with open(freeze_file, 'w', encoding='utf-8') as f:
                                f.write("# Python环境完整包列表\n")
                                f.write(f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                f.write(f"# Python版本: {sys.version.split()[0]}\n")
                                f.write(f"# 使用以下命令安装: pip install -r python_packages.txt\n\n")
                                f.write(result.stdout)
                            
                            # 统计包数量
                            package_count = len([line for line in result.stdout.split('\n') if line.strip() and not line.startswith('#')])
                            
                            stats["exported_items"].append(f"环境依赖 ({package_count}个包)")
                            stats["file_count"] += 1
                            pip_success = True
                            break
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
                
                if not pip_success:
                    stats["errors"].append("pip命令未找到或执行失败（已尝试多种调用方式），环境信息仍已导出")
                    
            except subprocess.TimeoutExpired:
                stats["errors"].append("pip freeze执行超时（30秒），环境信息仍已导出")
            except Exception as e:
                stats["errors"].append(f"获取包列表失败: {str(e)}，环境信息仍已导出")
            
        except Exception as e:
            stats["errors"].append(f"导出环境依赖失败: {str(e)}")
    
    def _export_workflows(self, root, temp_dir, stats):
        """导出工作流文件"""
        try:
            workflow_sources = [
                root / "user" / "default" / "workflows",
                root / "workflows",
                root / "my_workflows",
            ]
            
            workflow_dir = temp_dir / "workflows"
            workflow_dir.mkdir(exist_ok=True)
            
            total_files = 0
            for source in workflow_sources:
                if source.exists() and source.is_dir():
                    for file in source.rglob("*.json"):
                        rel_path = file.relative_to(source)
                        dest = workflow_dir / source.name / rel_path
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file, dest)
                        total_files += 1
            
            if total_files > 0:
                stats["exported_items"].append(f"工作流文件 ({total_files}个)")
                stats["file_count"] += total_files
            
        except Exception as e:
            stats["errors"].append(f"导出工作流失败: {str(e)}")
    
    def _export_inputs(self, root, temp_dir, stats):
        """导出输入文件"""
        try:
            input_dir = root / "input"
            if input_dir.exists() and input_dir.is_dir():
                dest_dir = temp_dir / "input"
                shutil.copytree(input_dir, dest_dir, dirs_exist_ok=True)
                
                # 统计文件数量
                file_count = sum(1 for _ in dest_dir.rglob("*") if _.is_file())
                stats["exported_items"].append(f"输入文件 ({file_count}个)")
                stats["file_count"] += file_count
            
        except Exception as e:
            stats["errors"].append(f"导出输入文件失败: {str(e)}")
    
    def _export_outputs(self, root, temp_dir, stats):
        """导出输出文件（排除备份和临时文件）"""
        try:
            output_dir = root / "output"
            if output_dir.exists() and output_dir.is_dir():
                dest_dir = temp_dir / "output"
                dest_dir.mkdir(exist_ok=True)
                
                file_count = 0
                for item in output_dir.iterdir():
                    # 跳过备份目录和临时目录
                    if item.name == "config_backups" or item.name.startswith("temp_import_"):
                        continue
                    
                    dest = dest_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                        file_count += sum(1 for _ in dest.rglob("*") if _.is_file())
                    else:
                        shutil.copy2(item, dest)
                        file_count += 1
                
                if file_count > 0:
                    stats["exported_items"].append(f"输出文件 ({file_count}个)")
                    stats["file_count"] += file_count
            
        except Exception as e:
            stats["errors"].append(f"导出输出文件失败: {str(e)}")
    
    def _create_zip(self, source_dir, zip_path, stats):
        """创建ZIP压缩包"""
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in source_dir.rglob("*"):
                    if file.is_file():
                        arcname = file.relative_to(source_dir)
                        zipf.write(file, arcname)
                        stats["total_size"] += file.stat().st_size
        except Exception as e:
            stats["errors"].append(f"创建压缩包失败: {str(e)}")
            raise
    
    def _generate_success_report(self, zip_path, stats, timestamp):
        """生成成功报告"""
        size_mb = stats["total_size"] / (1024 * 1024)
        
        report = "✅ 配置导出成功！\n\n"
        report += f"📦 导出文件：{zip_path.name}\n"
        report += f"📂 保存路径：{zip_path.parent}\n"
        report += f"📊 文件数量：{stats['file_count']} 个\n"
        report += f"💾 压缩大小：{size_mb:.2f} MB\n"
        report += f"🕐 导出时间：{timestamp}\n\n"
        
        if stats["exported_items"]:
            report += "📋 已导出内容：\n"
            for item in stats["exported_items"]:
                report += f"  ✓ {item}\n"
        
        if stats["errors"]:
            report += "\n⚠️ 部分内容导出失败：\n"
            for error in stats["errors"]:
                report += f"  ✗ {error}\n"
        
        return report


class ConfigImport:
    """
    配置文件导入节点
    功能：导入ComfyUI的各类配置文件和资源
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "import_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "导入路径（支持ZIP压缩包或文件夹的绝对路径）"
                }),
                "import_mode": (["overwrite", "skip", "auto_rename"], {
                    "default": "overwrite",
                    "tooltip": "导入形式：overwrite(覆盖已存在文件) skip(跳过已存在文件) auto_rename(自动重命名)"
                }),
                "create_backup": ("BOOLEAN", {
                    "default": True,
                    "label_on": "开启",
                    "label_off": "关闭",
                    "tooltip": "导入前创建现有配置的备份（保存到output目录）"
                }),
            },
        }

    CATEGORY = "🎨QING/配置管理"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_analysis",)
    FUNCTION = "import_config"
    OUTPUT_NODE = True

    def import_config(self, import_path, import_mode="auto_rename", create_backup=True):
        """
        主处理函数：导入ComfyUI配置
        
        参数:
            import_path: 导入文件路径（支持ZIP文件或文件夹）
            import_mode: 导入模式（overwrite/skip/auto_rename）
            create_backup: 是否创建备份
            
        返回:
            tuple: (结果分析文本,)
        """
        try:
            # 验证导入路径
            if not import_path or not import_path.strip():
                return ("❌ 错误：未指定导入路径",)
            
            source_path = Path(import_path.strip())
            if not source_path.exists():
                return (f"❌ 错误：路径不存在\n路径：{source_path}",)
            
            # 获取ComfyUI根目录
            comfyui_root = self._get_comfyui_root()
            
            # 导入统计
            stats = {
                "imported_items": [],
                "skipped_items": [],
                "renamed_items": [],
                "file_count": 0,
                "backup_created": False,
                "errors": [],
                "import_type": ""
            }
            
            # 创建临时解压目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_dir = comfyui_root / f"temp_import_{timestamp}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # 判断是ZIP文件还是文件夹
                if source_path.is_file():
                    if source_path.suffix.lower() == '.zip':
                        # ZIP文件：验证完整性并解压
                        stats["import_type"] = "ZIP压缩包"
                        try:
                            with zipfile.ZipFile(source_path, 'r') as zipf:
                                # 测试ZIP文件完整性
                                bad_file = zipf.testzip()
                                if bad_file:
                                    return (f"❌ 错误：ZIP文件已损坏\n损坏的文件：{bad_file}",)
                                # 解压到临时目录
                                zipf.extractall(temp_dir)
                        except zipfile.BadZipFile:
                            return (f"❌ 错误：不是有效的ZIP文件\n文件：{source_path.name}",)
                        except Exception as e:
                            return (f"❌ 错误：ZIP文件解压失败\n错误：{str(e)}",)
                    else:
                        return (f"❌ 错误：不支持的文件格式\n支持：ZIP压缩包或文件夹\n当前：{source_path.suffix}",)
                elif source_path.is_dir():
                    # 文件夹：直接复制到临时目录
                    stats["import_type"] = "文件夹"
                    shutil.copytree(source_path, temp_dir, dirs_exist_ok=True)
                else:
                    return (f"❌ 错误：不支持的路径类型\n路径：{source_path}",)
                
                # 创建备份（如果需要）
                if create_backup:
                    self._create_backup(comfyui_root, stats)
                
                # 导入各类配置
                self._import_node_info(temp_dir, comfyui_root, import_mode, stats)
                self._import_frontend_settings(temp_dir, comfyui_root, import_mode, stats)
                self._import_dependencies(temp_dir, comfyui_root, import_mode, stats)
                self._import_workflows(temp_dir, comfyui_root, import_mode, stats)
                self._import_inputs(temp_dir, comfyui_root, import_mode, stats)
                self._import_outputs(temp_dir, comfyui_root, import_mode, stats)
                
                result = self._generate_import_success_report(source_path, stats, import_mode)
                
            finally:
                # 清理临时目录
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
            return (result,)
            
        except Exception as e:
            error_msg = f"❌ 导入失败\n\n错误信息：{str(e)}\n\n请检查路径格式和权限"
            return (error_msg,)
    
    def _get_comfyui_root(self):
        """获取ComfyUI根目录"""
        try:
            import folder_paths
            base_path = folder_paths.base_path
            return Path(base_path)
        except:
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / "main.py").exists() or (current / "comfyui").exists():
                    return current
                current = current.parent
            return Path.cwd()
    
    def _create_backup(self, root, stats):
        """创建现有配置的备份（保存到output目录）"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 使用output目录作为备份目录
            try:
                import folder_paths
                output_dir = Path(folder_paths.get_output_directory())
            except:
                output_dir = root / "output"
            
            backup_dir = output_dir / "config_backups" / f"before_import_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 备份关键配置目录
            backup_targets = [
                (root / "user", "user"),
                (root / "workflows", "workflows"),
            ]
            
            backup_count = 0
            for source, name in backup_targets:
                if source.exists():
                    dest = backup_dir / name
                    if source.is_dir():
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                        backup_count += 1
                    else:
                        shutil.copy2(source, dest)
                        backup_count += 1
            
            if backup_count > 0:
                stats["backup_created"] = True
                stats["backup_path"] = str(backup_dir)
            else:
                stats["errors"].append("未找到需要备份的配置目录")
            
        except Exception as e:
            stats["errors"].append(f"创建备份失败: {str(e)}")
    
    def _copy_file_with_mode(self, source, dest, mode, stats):
        """根据模式复制文件"""
        try:
            if not source.exists():
                return False
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            if not dest.exists():
                # 目标不存在，直接复制
                shutil.copy2(source, dest)
                return True
            else:
                # 目标已存在，根据模式处理
                if mode == "overwrite":
                    shutil.copy2(source, dest)
                    return True
                elif mode == "skip":
                    stats["skipped_items"].append(str(dest.relative_to(dest.parents[2])))
                    return False
                elif mode == "auto_rename":
                    # 自动重命名
                    base = dest.stem
                    ext = dest.suffix
                    counter = 1
                    new_dest = dest.parent / f"{base}_{counter}{ext}"
                    while new_dest.exists():
                        counter += 1
                        new_dest = dest.parent / f"{base}_{counter}{ext}"
                    shutil.copy2(source, new_dest)
                    stats["renamed_items"].append(str(new_dest.relative_to(new_dest.parents[2])))
                    return True
            
        except Exception as e:
            stats["errors"].append(f"复制文件失败 {source.name}: {str(e)}")
            return False
    
    def _import_node_info(self, temp_dir, root, mode, stats):
        """导入节点信息"""
        try:
            node_info_dir = temp_dir / "node_info"
            if not node_info_dir.exists():
                return
            
            nodes_list_file = node_info_dir / "custom_nodes_list.json"
            if nodes_list_file.exists():
                with open(nodes_list_file, 'r', encoding='utf-8') as f:
                    nodes_data = json.load(f)
                
                # 保存节点信息到user目录
                user_dir = root / "user" / "default"
                user_dir.mkdir(parents=True, exist_ok=True)
                
                dest = user_dir / "custom_nodes_info.json"
                if self._copy_file_with_mode(nodes_list_file, dest, mode, stats):
                    stats["imported_items"].append("节点信息")
                    stats["file_count"] += 1
            
        except Exception as e:
            stats["errors"].append(f"导入节点信息失败: {str(e)}")
    
    def _import_frontend_settings(self, temp_dir, root, mode, stats):
        """导入前端设置"""
        try:
            settings_dir = temp_dir / "frontend_settings"
            if not settings_dir.exists():
                return
            
            imported_count = 0
            for setting_file in settings_dir.glob("*.json"):
                # 导入到user/default目录
                dest_dir = root / "user" / "default"
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / setting_file.name
                
                if self._copy_file_with_mode(setting_file, dest, mode, stats):
                    imported_count += 1
            
            if imported_count > 0:
                stats["imported_items"].append(f"前端设置 ({imported_count}个)")
                stats["file_count"] += imported_count
            
        except Exception as e:
            stats["errors"].append(f"导入前端设置失败: {str(e)}")
    
    def _import_dependencies(self, temp_dir, root, mode, stats):
        """导入环境依赖"""
        try:
            deps_dir = temp_dir / "dependencies"
            if not deps_dir.exists():
                return
            
            # 导入requirements.txt（仅作为参考，不自动安装）
            req_file = deps_dir / "requirements.txt"
            if req_file.exists():
                dest = root / "imported_requirements.txt"
                if self._copy_file_with_mode(req_file, dest, mode, stats):
                    stats["imported_items"].append("环境依赖信息（需手动安装）")
                    stats["file_count"] += 1
            
        except Exception as e:
            stats["errors"].append(f"导入环境依赖失败: {str(e)}")
    
    def _import_workflows(self, temp_dir, root, mode, stats):
        """导入工作流文件"""
        try:
            workflow_dir = temp_dir / "workflows"
            if not workflow_dir.exists():
                return
            
            dest_dir = root / "user" / "default" / "workflows"
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            imported_count = 0
            for workflow_file in workflow_dir.rglob("*.json"):
                rel_path = workflow_file.relative_to(workflow_dir)
                dest = dest_dir / rel_path
                if self._copy_file_with_mode(workflow_file, dest, mode, stats):
                    imported_count += 1
            
            if imported_count > 0:
                stats["imported_items"].append(f"工作流文件 ({imported_count}个)")
                stats["file_count"] += imported_count
            
        except Exception as e:
            stats["errors"].append(f"导入工作流失败: {str(e)}")
    
    def _import_inputs(self, temp_dir, root, mode, stats):
        """导入输入文件"""
        try:
            input_dir = temp_dir / "input"
            if not input_dir.exists():
                return
            
            dest_dir = root / "input"
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            imported_count = 0
            for input_file in input_dir.rglob("*"):
                if input_file.is_file():
                    rel_path = input_file.relative_to(input_dir)
                    dest = dest_dir / rel_path
                    if self._copy_file_with_mode(input_file, dest, mode, stats):
                        imported_count += 1
            
            if imported_count > 0:
                stats["imported_items"].append(f"输入文件 ({imported_count}个)")
                stats["file_count"] += imported_count
            
        except Exception as e:
            stats["errors"].append(f"导入输入文件失败: {str(e)}")
    
    def _import_outputs(self, temp_dir, root, mode, stats):
        """导入输出文件"""
        try:
            output_dir = temp_dir / "output"
            if not output_dir.exists():
                return
            
            dest_dir = root / "output"
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            imported_count = 0
            for output_file in output_dir.rglob("*"):
                if output_file.is_file():
                    rel_path = output_file.relative_to(output_dir)
                    dest = dest_dir / rel_path
                    if self._copy_file_with_mode(output_file, dest, mode, stats):
                        imported_count += 1
            
            if imported_count > 0:
                stats["imported_items"].append(f"输出文件 ({imported_count}个)")
                stats["file_count"] += imported_count
            
        except Exception as e:
            stats["errors"].append(f"导入输出文件失败: {str(e)}")
    
    def _generate_import_success_report(self, source_path, stats, mode):
        """生成导入成功报告"""
        mode_names = {
            "overwrite": "覆盖模式",
            "skip": "跳过模式",
            "auto_rename": "自动重命名模式"
        }
        
        report = "✅ 配置导入成功！\n\n"
        report += f"📦 导入来源：{source_path.name}\n"
        report += f"📂 导入类型：{stats.get('import_type', '未知')}\n"
        report += f"🔧 导入模式：{mode_names.get(mode, mode)}\n"
        report += f"📊 导入文件数：{stats['file_count']} 个\n\n"
        
        if stats["backup_created"]:
            backup_path = stats.get('backup_path', '已创建')
            report += f"💾 备份位置：{backup_path}\n\n"
        
        if stats["imported_items"]:
            report += "📋 已导入内容：\n"
            for item in stats["imported_items"]:
                report += f"  ✓ {item}\n"
        
        if stats["renamed_items"]:
            report += f"\n🔄 自动重命名：{len(stats['renamed_items'])} 个文件\n"
        
        if stats["skipped_items"]:
            report += f"\n⏭️ 跳过文件：{len(stats['skipped_items'])} 个\n"
        
        if stats["errors"]:
            report += "\n⚠️ 部分内容导入失败：\n"
            for error in stats["errors"]:
                report += f"  ✗ {error}\n"
        
        report += "\n💡 提示：如需应用新配置，请重启ComfyUI"
        
        return report


# 节点注册
NODE_CLASS_MAPPINGS = {
    "ConfigExport": ConfigExport,
    "ConfigImport": ConfigImport
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ConfigExport": "配置文件丨导出",
    "ConfigImport": "配置文件丨导入"
}

