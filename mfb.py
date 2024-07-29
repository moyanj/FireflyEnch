import os
import shutil
import time
import sass
import click
from jinja2 import Environment, FileSystemLoader

class BasePlugin:
    def __init__(self):
        self.base_path = ''
    
    def render(self, template_path, output_dir, context):
        pass
        
# HTML预处理插件实现
class HtmlPlugin(BasePlugin):
    def render(self, template_path, output_dir, context):
        if template_path.endswith(('.html')):
            
            env = Environment(loader=FileSystemLoader(self.base_path), autoescape=True)
            template = env.get_template(os.path.relpath(template_path, self.base_path))
            rendered_content = template.render(context)
            
            output_path = os.path.join(output_dir, os.path.basename(template_path))
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            return True

class DefaultPlugin(BasePlugin):
    def render(self, template_path, output_dir, context):
        # 获取文件名
        filename = os.path.basename(template_path)
        
        output_file = os.path.join(output_dir, filename)
        
        # 复制文件到输出目录
        shutil.copy(template_path, output_file)
        return True
        
class TJSPlugin(BasePlugin):
    def render(self,template_path, output_dir, context):
        if template_path.endswith('.t.js'):
            env = Environment(loader=FileSystemLoader(self.base_path), autoescape=True)
            template = env.get_template(os.path.relpath(template_path, self.base_path))
            rendered_content = template.render(context)
            
            output_path = os.path.join(output_dir, os.path.basename(template_path).replace('.t.js','.js'))
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            return True

class SassPlugin(BasePlugin):
    def render(self,template_path, output_dir, context):
        if template_path.endswith(('.sass')):
            with open(template_path) as f:
                rendered = sass.compile(string=f.read())
            with open(os.path.join(output_dir, os.path.basename(template_path).replace('.sass','.css')), 'w') as f:
                f.write(rendered)
            return True
            
class RJSPlugin(BasePlugin):
    def render(self, template_path, output_dir, context):
        if template_path.endswith('.r.js'):
            return True

# 模板渲染器类
class TemplateRenderer:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.plugins = []
        self.load_plugin(HtmlPlugin())
        if os.path.exists(output_dir):
            shutil.rmtree(self.output_dir)
    
    def load_plugin(self, plugin):
        plugin.base_path = self.input_dir
        self.plugins.append(plugin)
        
    def render_templates(self, context={}, ignore_files=['base.html']):
        self.load_plugin(DefaultPlugin())
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        # 遍历模板文件
        for root, _, files in os.walk(self.input_dir):
           
            for f in files:
                if f in ignore_files:
                    continue
                    
                template_path = os.path.relpath(os.path.join(root, f), self.input_dir)
                output_subdir = os.path.join(self.output_dir, os.path.relpath(root, self.input_dir))
                os.makedirs(output_subdir, exist_ok=True)
                
                # 使用插件处理文件
                for plugin in self.plugins:
                    if plugin.render(os.path.join(root, f), output_subdir, context):
                        break

def build(renderer,other={}):
    context = {
        'build_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        'version': '1.0.0',
        'type':'debug',
        'build_timestamp':time.time(),
        'base_url':''
    }
    context.update(other)
    # 渲染模板
    renderer.render_templates(context)
   
@click.command()
@click.argument('input_dir')
@click.option('--plugin','-p', multiple=True)              
@click.option('--dist', default='dist')
@click.option('--define','-d', multiple=True)
def cli(input_dir, plugin, dist, define):
    plug_map = {
        'sass':SassPlugin,
        'tjs':TJSPlugin,
        'rjs':RJSPlugin
    }
    renderer = TemplateRenderer(input_dir, dist)
    
    for p in plugin:
        if p in plug_map:
            renderer.load_plugin(plug_map[p]())
        else:
            print('There is no plugin named',p)
            exit(1)
    
    ctxs = {}
    for d in define:
        ctxs[d.split('=')[0]] = d.split('=')[1]
        
    build(renderer, ctxs)
# 示例用法
def main():
    input_dir = 'PornPictures/'
    output_dir = 'dist'

    # 创建模板渲染器
    renderer = TemplateRenderer(input_dir, output_dir)
    renderer.load_plugin(TJSPlugin())
    renderer.load_plugin(SassPlugin())
    # 定义要传递的变量
    context = {
        'build_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        'version': '1.0.0',
        'type':'debug',
        'build_timestamp':time.time(),
        'base_url':'http://127.0.0.1:5000'
    }
    # 渲染模板
    renderer.render_templates(context)
   
  
if __name__ == "__main__":
    cli()
