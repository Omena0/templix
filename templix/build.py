from bs4 import BeautifulSoup, formatter, element
from markdown.extensions import tables
from collections import defaultdict
from shlex import split
from typing import Any
import markdown as md
import shutil
import os

class TemplateError(SyntaxError): ...

def normalize_text(tag):
    for child in list(tag.children):
        if isinstance(child, element.NavigableString):
            cleaned = " ".join(child.split())
            child.replace_with(cleaned)

def pretty_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # normalize text inside all tags
    for tag in soup.find_all():
        normalize_text(tag)

    return soup.prettify(formatter=formatter.HTMLFormatter(indent=2))

def render_markdown(markdown:str) -> str:
    html = md.markdown(
        markdown,
        extensions=[tables.TableExtension()]
    )
    return html

def ensure_resource(filename, conf:dict):
    path = os.path.join(conf['source'], filename)
    dest = os.path.join(conf['output'], filename)
    shutil.copy(path, dest)
    return filename

def parse_special(template:str, vars:dict, conf:dict) -> str:
    if '{%' not in template:
        return template

    i = 0
    stack = []
    conds = []
    while i < len(template):
        if template[i:i+2] == '{%':
            stack.append(i)

        elif template[i:i+2] == '%}':
            stack.append(i)
            start = stack[-2]
            name = template[start+2:i-1].strip().split(' ')

            if name[0] == 'if':
                conds.append(('if', eval(name[1], vars)))

            elif name[0] == 'for':
                conds.append(('for', name[1], eval(' '.join(name[3:]), vars)))

            elif name[0] == 'import':
                exec(f'import {name[1]}', vars)

                start = stack[-2]
                end   = stack[-1]+2
                content = template[start:end].strip()

                template = template.replace(content, '')
                conds.append(('_placeholder',))

            elif name[0] == 'end':
                start = stack[-4]
                end   = stack[-1]+2
                content = template[start:end].strip()

                cond = conds[-1]

                if cond[0] == 'if':
                    if not cond[1]:
                        template = template.replace(content, '')
                    else:
                        new_content = content.split('%}')[1].split('{%')[0].strip()
                        template = template.replace(content, new_content)

                elif cond[0] == 'for':
                    full = ''
                    for value in cond[2]:
                        t = '\n'.join(content.splitlines()[1:-1])
                        vars.update({cond[1]: value})
                        t = apply_template(t, vars, conf)
                        full += t
                    template = template.replace(content, full)

        i += 1

    return template

def include(file:str, conf:dict, **kwargs:dict[str,str]) -> str:
    with open(os.path.join(conf['source'], file), 'rb') as f:
        content = f.read().decode(errors='ignore')
    return apply_template(content, kwargs, conf)

def url(file:str, conf:dict):
    return ensure_resource(file, conf)

def apply_template(template:str, values:dict, conf:dict) -> str:
    vars:dict[str, Any] = defaultdict(lambda: None)
    vars.update(values)

    builtins = {}
    for name in dir(__builtins__):
        builtins[name] = getattr(__builtins__, name)

    vars.update(builtins)

    vars['include'] = lambda *args, **kwargs: include(*args, conf=conf, **kwargs)
    vars['url'] = lambda *args, **kwargs: url(*args, conf=conf, **kwargs)

    template, t_file, new_values = preprocess(template, conf)

    template = parse_special(template, vars, conf)

    # Find each {{ }} value
    start = 0
    while True:
        template = parse_special(template, vars, conf)

        # Get start and end pos
        start = template.find('{{', start, -1)+2
        if start == 1:
            break

        end = template.find('}}', start)

        # Get content in between them
        content = template[start:end]

        # Reconstruct replacement key
        key = '{{'+content+'}}'

        # Make sure we didn't skip over one
        if '{{' in content:
            raise TemplateError(f'Invalid syntax: {content}')

        # Multiline code block (exec, use result variable)
        if '\n' in content:
            locals = {}
            exec(content, vars, locals)

            result = locals.get('result', '')

            if '{{' in template or '{%' in template:
                result = apply_template(result, values, conf)

        # Single line (eval)
        else:
            result = eval(content, vars)

        if key not in template:
            raise TemplateError(f'Key not found in template.')

        if key == result:
            raise TemplateError('Key cannot be equal to result.')

        # Replace
        template = template.replace(key, result, 1)

    # Templates can inherit other templates
    if t_file:
        with open(os.path.join(conf['source'], t_file), 'rb') as f:
            new_template = f.read().decode(errors='ignore')

        new_values.update(values)
        new_values['content'] = render_markdown(template)

        return apply_template(new_template, new_values, conf)

    if '{{' not in template and '{%' not in template:
        return template

    # Leaf template
    return apply_template(template, vars, conf)

def preprocess(source, config):
    template_file = None
    values = {}

    content = ""
    include_file = ""

    # Preprocess
    for line in source.splitlines():
        line = line.strip()
        if line.startswith('@'):
            line = split(line.removeprefix('@'))

            if line[0] == 'using':
                template_file = line[1]

            elif line[0] == 'include':
                include_file = line[1]

        elif line.startswith('$'):
            try:
                key, value = line.removeprefix('$').split(' ', 1)
            except Exception as e:
                raise TemplateError(f'Invalid syntax: {line}') from e
            values[key] = value

        else:
            if include_file:
                content += include(include_file, conf=config, **values)
                include_file = ""

            else:
                content += line+'\n'

    if include_file:
        content += include(include_file, conf=config, **values)
        include_file = ""

    return content, template_file, values

def get_page(source:str, conf:dict[str,str]) -> str:
    content, template_file, values = preprocess(source, conf)

    content = render_markdown(content)

    if not template_file:
        return content

    values['content'] = content

    with open(os.path.join(conf['source'], template_file), 'rb') as f:
        template = f.read().decode(errors='ignore')

    html = apply_template(template, values, conf)

    result = '\n'.join(line.rstrip() for line in html.splitlines() if line)

    return result

def generate(conf:dict):
    src_dir:str = conf['source']
    out_dir:str = conf['output']
    for file in os.listdir(src_dir):
        if not file.endswith('.md'):
            continue

        with open(os.path.join(src_dir, file), 'rb') as f:
            source = f.read().decode(errors='ignore')

        html = get_page(source, conf)
        html = pretty_html(html)

        out_path = os.path.join(out_dir, os.path.splitext(file)[0])+'.html'
        with open(out_path, 'w') as f:
            f.write(html)
