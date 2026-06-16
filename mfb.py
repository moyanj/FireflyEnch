import os
import shutil
import time
import json
import click
from typing import Dict, Any, List, Optional, Protocol
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


class BasePlugin(Protocol):
    """插件基类协议"""
    base_path: str

    def render(self, template_path: str, output_dir: str, context: Dict[str, Any]) -> bool:
        """渲染模板"""
        ...


class HtmlPlugin:
    """HTML模板插件"""
    def __init__(self):
        self.base_path = ""

    def render(self, template_path: str, output_dir: str, context: Dict[str, Any]) -> bool:
        if template_path.endswith(".html"):
            env = Environment(loader=FileSystemLoader(self.base_path), autoescape=True)
            template = env.get_template(os.path.relpath(template_path, self.base_path))
            rendered_content = template.render(context)
            output_path = os.path.join(output_dir, os.path.basename(template_path))
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            return True
        return False


class DefaultPlugin:
    """默认文件复制插件"""
    def __init__(self):
        self.base_path = ""

    def render(self, template_path: str, output_dir: str, context: Dict[str, Any]) -> bool:
        filename = os.path.basename(template_path)
        output_file = os.path.join(output_dir, filename)
        shutil.copy(template_path, output_file)
        return True


class TJSPlugin:
    """JavaScript模板插件 (.t.js → .js)"""
    def __init__(self):
        self.base_path = ""

    def render(self, template_path: str, output_dir: str, context: Dict[str, Any]) -> bool:
        if template_path.endswith(".t.js"):
            env = Environment(loader=FileSystemLoader(self.base_path), autoescape=True)
            template = env.get_template(os.path.relpath(template_path, self.base_path))
            rendered_content = template.render(context)
            output_path = os.path.join(
                output_dir, os.path.basename(template_path).replace(".t.js", ".js")
            )
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            return True
        return False


class RJSPlugin:
    """JavaScript资源插件 (.r.js)"""
    def __init__(self):
        self.base_path = ""

    def render(self, template_path: str, output_dir: str, context: Dict[str, Any]) -> bool:
        if template_path.endswith(".r.js"):
            # 处理资源文件
            return True
        return False


class TemplateRenderer:
    """模板渲染器"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.plugins: List[BasePlugin] = []
        self._load_default_plugins()

    def _load_default_plugins(self):
        """加载默认插件"""
        self.load_plugin(HtmlPlugin())
        self.load_plugin(DefaultPlugin())

    def load_plugin(self, plugin: BasePlugin):
        """加载插件"""
        plugin.base_path = str(self.input_dir)
        self.plugins.append(plugin)

    def render_templates(self, context: Dict[str, Any] = None, ignore_files: List[str] = None):
        """渲染所有模板"""
        if context is None:
            context = {}
        if ignore_files is None:
            ignore_files = ["base.html"]

        # 清理输出目录
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 遍历模板文件
        for root, _, files in os.walk(self.input_dir):
            for f in files:
                if f in ignore_files:
                    continue

                template_path = Path(root) / f
                output_subdir = self.output_dir / Path(root).relative_to(self.input_dir)
                output_subdir.mkdir(parents=True, exist_ok=True)

                # 使用插件处理文件
                for plugin in self.plugins:
                    try:
                        if plugin.render(str(template_path), str(output_subdir), context):
                            break
                    except Exception as e:
                        print(f"Error processing {template_path}: {e}")
                        continue


def get_build_context(config: Dict[str, Any], extra: Dict[str, Any] = None) -> Dict[str, Any]:
    """获取构建上下文"""
    context = {
        "build_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "version": "1.0.2",
        "type": "rel",
        "build_timestamp": time.time(),
        "base_url": "",
        "name": config.get("name", "FireflyEnch"),
    }
    if extra:
        context.update(extra)
    return context


def build(renderer: TemplateRenderer, config: Dict[str, Any], extra: Dict[str, Any] = None):
    """执行构建"""
    context = get_build_context(config, extra)
    renderer.render_templates(context)


@click.command()
@click.argument("input_dir")
@click.option("--plugin", "-p", multiple=True, help="Additional plugins to load")
@click.option("--dist", default="dist", help="Output directory")
@click.option("--define", "-d", multiple=True, help="Define context variables (key=value)")
@click.option("--config", "-c", default="config.json", help="Config file path")
def cli(input_dir: str, plugin: List[str], dist: str, define: List[str], config: str):
    """FireflyEnch 构建工具"""
    # 加载配置
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Config file not found: {config}")
        raise SystemExit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid config file: {e}")
        raise SystemExit(1)

    # 初始化渲染器
    renderer = TemplateRenderer(input_dir, dist)

    # 加载额外插件
    plugin_map = {
        "tjs": TJSPlugin,
        "rjs": RJSPlugin,
    }
    
    for p in plugin:
        if p in plugin_map:
            renderer.load_plugin(plugin_map[p]())
        else:
            click.echo(f"Unknown plugin: {p}")
            raise SystemExit(1)

    # 解析定义变量
    context_vars = {}
    for d in define:
        if "=" not in d:
            click.echo(f"Invalid define format: {d}")
            raise SystemExit(1)
        key, value = d.split("=", 1)
        context_vars[key] = value

    # 执行构建
    build(renderer, config_data, context_vars)
    click.echo(f"Build completed: {dist}")


if __name__ == "__main__":
    cli()
