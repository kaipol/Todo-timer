"""
配置管理模块 - 保存和加载用户设置
"""
import json
import os
from pathlib import Path


class Config:
    """配置管理类"""
    
    DEFAULT_CONFIG = {
        'app_icon': '',  # 自定义应用图标路径
        # 计时器背景设置
        'background_type': 'gradient',  # 'gradient', 'color', 'image'
        'background_color': '#667eea',  # 背景颜色
        'background_gradient': ['#667eea', '#764ba2'],  # 渐变颜色
        'background_image': '',  # 背景图片路径
        # 全局背景设置
        'global_bg_enabled': False,  # 是否启用全局背景
        'global_bg_type': 'image',  # 'image', 'color', 'gradient'
        'global_bg_image': '',  # 全局背景图片路径
        'global_bg_color': '#f8f9fa',  # 全局背景颜色
        'global_bg_gradient': ['#e0e5ec', '#f8f9fa'],  # 全局背景渐变
        'global_bg_blur': 0,  # 背景模糊度 (0-50)
        'global_bg_opacity': 0.85,  # 内容区域不透明度 (0.0-1.0)
    }
    
    def __init__(self):
        self.config_dir = Path.home() / '.time_tracker'
        self.config_file = self.config_dir / 'config.json'
        self.config = self.DEFAULT_CONFIG.copy()
        self._ensure_config_dir()
        self.load()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)
    
    def load(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 合并配置，保留默认值
                    for key in self.DEFAULT_CONFIG:
                        if key in saved_config:
                            self.config[key] = saved_config[key]
            except Exception:
                pass
    
    def save(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        self.save()
    
    def reset(self):
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()


# 全局配置实例
app_config = Config()