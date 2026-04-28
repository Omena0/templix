
# Templix

[![PyPi](https://github.com/Omena0/templix/actions/workflows/publish.yml/badge.svg?branch=main)](https://github.com/Omena0/templix/actions/workflows/publish.yml)

A static HTML templating engine. Suitable for github pages and other static sites.

All code is ran at build time.

## Usage

Install via `pipx install templix`, then use `templix` to build.

A default config file will be created with the following contents:

```json
{"source": "src", "output": "build"}
```

Running `templix` will build `src/index.md`. Any files used by it will be included in the build.

## Syntax

Normal markdown will be parsed in `.md` files.

You are supposed to write reusable `.html` file templates
that you then use in your `.md` files.

### Python code blocks

You can use `{{ <code> }}` to embed the result of running python code.

If the opening and closing braces are on the same line `eval()` will be used and the block will be replaced by the evaluation result
Otherwise it will be replaced by the value of the emitted `result` variable.

**Example:**

Single line

```html
<title>{{ title }}</title>
```

Multiline

```html
<p>
    {{
        result = ''
        for i in range(25):
            result += f'Hello, {i}\n'
    }}
</p>
```

### Special blocks

You can use `{% <special> %}` for `if`, `for` and `import` statements.

End a block with a `{% end %}`.

#### If statements

If the condition is false the contents of the block is skipped.
Otherwise the block will be replaced by its contents.

**Example:**

```html
{% if title %}
    <title>{{ title }}</title>
{% end %}
```

#### For statements

The block will be repeated for every element in the evaluated result.

**Example:**

```html
{% for page in pages %}
    <h2>{{ page.rsplit('.',1)[0].capitalize() }}</h2>
    <p>{{ open(page).read() }}</p>
    <br>
{% end %}
```

Pages definition (example)

```py
pages = [
    'page1.md',
    'page2.md',
    'page3.md',
    'page4.md',
    'page5.md'
]
```

#### Import statements

Identical to a python code block. Imports the module and stores it in vars.

**Example:**

Automatically includes files from a folder.

```py
{% import os %}
{% for i in os.listdir("pages") %}
    {{ open(os.path.join("pages", i)).read() }}
{% end %}
```

### Preprocessor syntax

#### @using declaration

With `@using <file>` you can embed the current file in between content in `<file>`.

The content of the file will be passed into `<file>` as the `content` variable.

#### @include declaration

With `@include <file>` you can embed `<file>` into the current file.

The declaration is replaced with the file contents.

#### Argument declarations

Using `​ $<key> <value>`, you can pass arguments to
the `@using` or `@include` declarations.
They will be available in the file as normal variables.

The space before the `$` is not required but without it
the syntax highlight will break.

The value is parsed as everything on the same line after
the declaration. It is passed as a string.

**Example:**

Proper `.html` boilerplate.

##### index.md

```md
@using base.html
 $title Hello, World

# Hello, World!

This is an example!

@include content.html
```

##### base.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {% if title %}
        <title>{{ title }}</title>
    {% end %}
</head>
<body>
    {{ content }}
</body>
</html>
```

##### content.html

```html
<h2>Lorem ipsum dolor sit amet,</h2>
<p>
    consectetur adipiscing elit.
    Vivamus tempus mauris vel ex congue porta. Integer elementum,
    purus sed convallis fermentum, ipsum est pellentesque dui,
    eget viverra ligula felis ut nisi. Duis pellentesque felis
    quis tellus aliquam, non pretium erat interdum. Fusce ut
    pulvinar urna. Proin venenatis congue commodo. Nullam metus mi,
    posuere a nulla vitae, tincidunt blandit erat. Nulla imperdiet
    massa ut semper facilisis. 
</p>
```

### Builtin functions

All python builtins are available, additionally,
templix provides two additional builtin funcions.

#### include(file:str, **kwargs)

Same as the `@include` declaration. Fetches the file, parses it and returns it.
You can provide variables to the file via `**kwargs`.

#### url(file)

Returns a url to the target file. Automatically replaces `.md` with `.html`.

Additionally pointing this to a non-html file will copy that file over.

This is very useful for linking to scripts or stylesheets.

**Example:**

```html
<!-- Stylesheet -->
<link rel="stylesheet" href="{{ url('style.css') }}">
<!-- Script -->
<script src="{{ url('script.js') }}"></script>
```
