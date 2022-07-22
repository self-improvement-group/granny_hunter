from pathlib import Path
# import os

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


def html_table(table_name: str, data, headers: list):
    with open(table_name, 'w') as page:
        page.write(base)
        page.write('<table>\n<thead class="t-header">\n<tr>')
        for header in headers:
            page.write(f'<th>{header}</th>')
        page.write('</tr>\n</thead>\n')
        page.write('<tbody class="st-table">\n')
        for row in data:
            page.write('<tr class="st-row">\n')
            for item in row:
                if item is row[2]:
                    p = Path(row[1])
                    file_uri = p.as_uri().replace(p.name, '')
                    page.write(f'<td><a href="{file_uri}">{item}</a></td>')
                else:
                    page.write(f'<td>{item}</td>')
            page.write('</tr>\n')
        page.write('</tbody>\n</table>\n</body>')