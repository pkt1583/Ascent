from app.utils.template import Template,TemplateFactory
import os
from logging  import getLogger

log = getLogger(__name__)

def init_template():
    # Define the relative path to the directory containing your templates
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log.info(f"current file directory {current_dir}")
    # Update with the relative path to your templates directory
    template_dir = os.path.join(current_dir, '../../templates')

    log.info(f"template directory {template_dir}")
    template_factory = TemplateFactory()
    template = template_factory.create_template("jinja", template_dir)
    return template