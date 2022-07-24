from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape


base = """
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto&display=swap');
        * {
            font-family: 'Roboto', sans-serif;
        }
        .t-header{
            background-color: rgba(0, 0, 0, 0.3)
        }
        .st-table .st-row:nth-child(even){
            background-color: rgba(0,0,0, .1)
        }
        td {
            padding: 5px;
        }
    </style>
</head>
<body>
"""

def get_uri(path):
    path = Path(path)
    return path.as_uri().replace(path.name, '')

def tabulate(filename: str, name: str, data, page_number):
    env = Environment(loader=PackageLoader("granny-hunter"), autoescape=select_autoescape())
    env.filters['get_uri'] = get_uri
    temp = env.get_template('table.html.jinja')
    with open(filename, 'w') as page:
        page.write(temp.render(data=data, page=page_number, name=name))

# def tabulate(table_name: str, data):
#     headers = ['Hash', 'Absolute path', 'Name', 'Size', 'Last modified']
#     with open(table_name, 'w') as page:
#         page.write(base)
#         page.write('<table>\n<thead class="t-header">\n<tr>')
#         for header in headers:
#             page.write(f'<th>{header}</th>')
#         page.write('</tr>\n</thead>\n')
#         page.write('<tbody class="st-table">\n')
#         for row in data:
#             page.write('<tr class="st-row">\n')
#             for item in row:
#                 if item is row[2]:
#                     p = Path(row[1])
#                     file_uri = p.as_uri().replace(p.name, '')
#                     page.write(f'<td><a href="{file_uri}">{item}</a></td>')
#                 else:
#                     page.write(f'<td>{item}</td>')
#             page.write('</tr>\n')
#         page.write('</tbody>\n</table>\n</body>')

# env = Environment(
#     loader=PackageLoader("granny-hunter"),
#     autoescape=select_autoescape()
# )
# env.filters['get_uri'] = get_uri
# temp = env.get_template('table.html.jinja')
# temp.render(name="table")