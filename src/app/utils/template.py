# generate method to render the manifest
import os
from abc import ABC, abstractmethod
from jinja2 import Environment, FileSystemLoader


class Template(ABC):
    @abstractmethod
    def render(self, template_name, output_folder, output_file, render_data, create_out_folder=True)-> bool:
        pass


class TemplateFactory:
    @staticmethod
    def create_template(template_type, template_dir):
        if template_type == "jinja":
            return JinjaTempalte(template_dir)
        else:
            raise ValueError(f"Unsupported template type: {template_type}")


class JinjaTempalte(Template):
    def __init__(self, templates_folder):
        self.templates_folder = templates_folder
        self.environment = None

    def load_environment(self):
        self.environment = Environment(loader=FileSystemLoader(self.templates_folder))

    def render(self, template_name, output_folder, output_file, render_data, create_out_folder=True) -> bool:
        if self.environment is None:
            self.load_environment()
        template = self.environment.get_template(template_name)
        output = template.render(render_data)
        if create_out_folder and not os.path.isdir(output_folder):
            os.makedirs(output_folder, exist_ok=True)
        try:
            with open(f'{output_folder}/{output_file}', "w") as f:
                num_chars_written = f.write(output)
                if num_chars_written > 0:
                    return True
                else:
                    return False
        except Exception as e:
            return False
