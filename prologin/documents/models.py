import subprocess

import os
import re
import tempfile
from django.conf import settings
from django.template import loader
from django.utils import translation

from prologin.utils import SubprocessFailedException


def latex_escape(value):
    """
        :param value: a plain text message
        :return the message LaTeX-escaped
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '°': r'o',  # FIXME
        '^': r'\^{}',
        '~': r'\textasciitilde{}',
        '\n': r'\\',
        '\\': r'\textbackslash{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless',
        '>': r'\textgreater',
    }
    regex = re.compile('|'.join(re.escape(key) for key in sorted(conv.keys(), key=len, reverse=True)))
    return regex.sub(lambda match: conv[match.group()], value)


class DocumentContext:
    def __init__(self, template, context):
        self.template = template
        self.context = context

    def __enter__(self):
        self.output_dir = tempfile.TemporaryDirectory(prefix='prologin_tex_gen_')

        in_file = os.path.join(self.output_dir.name, 'input.tex')
        out_file = os.path.join(self.output_dir.name, 'input.pdf')

        with translation.override('fr'):
            data = self.template.render(self.context).encode('utf-8')

        with open(in_file, 'wb') as source_file:
            source_file.write(data)

        proc = subprocess.Popen([
            'pdflatex', '-halt-on-error', '-interaction=errorstopmode',
            '-output-format=pdf', '-no-shell-escape',
            '-output-directory', self.output_dir.name, in_file,
        ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            outs, errs = proc.communicate(timeout=settings.LATEX_GENERATION_PROC_TIMEOUT)
            if proc.returncode != 0:
                raise SubprocessFailedException("pdflatex exited with non-zero", proc.returncode, outs, errs)
            if not os.path.exists(out_file):
                raise SubprocessFailedException("pdflatex did not create output file (empty contents?)", proc.returncode, outs, errs)
            return out_file
        except subprocess.SubprocessError:
            proc.kill()
            outs, errs = proc.communicate()
            raise SubprocessFailedException("pdflatex failed", proc.returncode, outs, errs)

    def __exit__(self, exc_type, exc_value, traceback):
        self.output_dir.cleanup()


def generate_tex_pdf(template_name, context):
    template = loader.get_template(template_name)
    return DocumentContext(template, context)
