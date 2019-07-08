# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
import os
import subprocess
from datetime import datetime
from pathlib import Path

import toml
import yaml
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from PyPDF2 import PdfFileReader, PdfFileWriter


latex_jinja_env = Environment(
    block_start_string='\BLOCK{',
    block_end_string='}',
    variable_start_string='\VAR{',
    variable_end_string='}',
    comment_start_string='\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,
    loader=FileSystemLoader([
        os.path.abspath('.'),
        os.path.abspath('templates'),
    ])
)


def merge_pdfs(files, output):
    pdf_writer = PdfFileWriter()

    for file in files:
        pdf_reader = PdfFileReader(file)
        for page in range(pdf_reader.getNumPages()):
            pdf_writer.addPage(pdf_reader.getPage(page))

    with open(output, 'wb') as output:
        pdf_writer.write(output)


def main():
    parser = argparse.ArgumentParser(description='Do some paperwork')
    parser.add_argument('config', type=str, nargs=1, help='Config file')
    args = parser.parse_args()

    config_file = os.path.join(os.getcwd(), args.config[0])

    with open(config_file, 'r') as toml_config:
        config = toml.load(toml_config)

    print(yaml.dump(config, default_flow_style=False))

    for title, data in config.get('letters').items():
        jobname = f'{title}-{datetime.now():%Y%m%d_%H%M%S}'
        template = latex_jinja_env.get_template(data.get('template'))

        render = template.render(**data.get('payload'))

        print(jobname)
        # render = f'%& -job-name={jobname}' + str('\n\n') + render

        print(render)

        with open(f'{jobname}.tex', 'w+', encoding='utf-8') as tex:
            tex.write(render)

        job = ['pdflatex', f'{jobname}.tex']
        subprocess.run(job, shell=True, creationflags=subprocess.IDLE_PRIORITY_CLASS)

        Path(f'{jobname}.log').unlink()
        Path(f'{jobname}.aux').unlink()
        Path(f'{jobname}.tex').unlink()

        if data.get('attachments'):
            attachments = data.get('attachments')
            merge_pdfs([f'{jobname}.pdf', *attachments], f'{jobname}_merged.pdf')


if __name__ == "__main__":
    main()
