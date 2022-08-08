from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape


def get_uri(path):
    if not isinstance(path, Path):
        path = Path(path)
    return path.as_uri().replace(path.name, '')

def tabulate(filename: str, name: str, data, page_number):
    env = Environment(loader=PackageLoader("granny-hunter"), autoescape=select_autoescape())
    env.filters['get_uri'] = get_uri
    temp = env.get_template('table.html.jinja')
    with open(filename, 'w') as page:
        page.write(temp.render(data=data, page=page_number, name=name))
