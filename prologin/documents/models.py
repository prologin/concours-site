import os
import re
import subprocess
import tempfile


class SubprocessFailedException(Exception):
    def __init__(self, message, returncode, stdout, stderr):
        self.message = message
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


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
        '^': r'\^{}',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless',
        '>': r'\textgreater',
    }
    regex = re.compile('|'.join(re.escape(key) for key in sorted(conv.keys(), key=len, reverse=True)))
    return regex.sub(lambda match: conv[match.group()], value)


class DocumentContext:
    def __init__(self, cwd, source):
        self.cwd = cwd
        self.source = source

    def __enter__(self):
        self.output_dir = tempfile.TemporaryDirectory(prefix='prologin_tex_gen_')

        in_file = os.path.join(self.output_dir.name, 'input.tex')
        out_file = os.path.join(self.output_dir.name, 'input.pdf')

        with open(in_file, 'wb') as source_file:
            source_file.write(self.source)

        with open('/tmp/lol.tex', 'wb') as fuck:
            fuck.write(self.source)

        proc = subprocess.Popen([
            'pdflatex', '-halt-on-error', '-interaction=errorstopmode',
            '-output-format=pdf', '-no-shell-escape',
            '-output-directory', self.output_dir.name, in_file,
        ], cwd=self.cwd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            outs, errs = proc.communicate(timeout=60)
            if proc.returncode != 0:
                raise SubprocessFailedException("pdflatex failed", proc.returncode, outs, errs)
            # `out_file` should exist by now
            self.output = open(out_file, 'rb')
            return self.output
        except subprocess.SubprocessError:
            proc.kill()
            outs, errs = proc.communicate()
            raise SubprocessFailedException("pdflatex failed", proc.returncode, outs, errs)

    def __exit__(self, exc_type, exc_value, traceback):
        self.output.close()
        self.output_dir.cleanup()


def generate_tex_pdf(template_fname, context):
    cwd = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tex_templates")

    with open(os.path.join(cwd, template_fname), 'rb') as template:
        source = template.read()

    for key, value in context.items():
        source = source.replace('#{}#'.format(key).encode('ascii'), value.encode('utf-8'))

    return DocumentContext(cwd, source)