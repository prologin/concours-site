from django.utils.translation import ugettext_lazy as _

from prologin.utils import ChoiceEnum


class LanguageDef:
    """
    Represent a single programming language.
    `name`: the human readable (translated if needed) language name
    `extensions`: the list of corresponding extensions
    `doc` (optional): the name of the documentation folder for this language
    `correctable`: if programs wrote in this language can be sent to the correction system
                   (typically not true for pseudo-code)
    """
    def __init__(self, name, extensions, doc=None, correctable=True):
        self.name = name
        self.extensions = extensions
        self.doc = doc
        self.correctable = correctable

    def __str__(self):
        return self.name

    def serialize(self):
        return str(self)


@ChoiceEnum.sort()
class Language(ChoiceEnum):
    """
    Machine-name (member name, left of equal sign) must be less than
    16 characters long.
    """
    c = LanguageDef("C", ['.c'], doc='c')
    cpp = LanguageDef("C++", ['.cc', '.c++', '.cpp'], doc='cpp')
    pascal = LanguageDef("Pascal", ['.pas', '.pascal'], doc='pascal')
    ocaml = LanguageDef("OCaml", ['.ml', '.ocaml'], doc='ocaml')
    scheme = LanguageDef("Scheme", ['.scm'], doc='scheme')
    haskell = LanguageDef("Haskell", ['.hs'], doc='haskell')
    java = LanguageDef("Java", ['.java'], doc='java')
    python2 = LanguageDef("Python 2", ['.py', '.py2'], doc='python2')
    python3 = LanguageDef("Python 3", ['.py3'], doc='python3')
    ada = LanguageDef("Ada", ['.adb'], doc='ada')
    php = LanguageDef("PHP", ['.php'], doc='php')
    js = LanguageDef("Javascript", ['.js'])
    vb = LanguageDef("VB", ['.vb'])
    perl = LanguageDef("Perl", ['.pl', '.perl'])
    lua = LanguageDef("Lua", ['.lua'])
    csharp = LanguageDef("C#", ['.cs'])
    fsharp = LanguageDef("F#", ['.fs'])
    brainfuck = LanguageDef("Brainfuck", ['.bf'])
    pseudocode = LanguageDef(_("Pseudocode"), ['.txt'], correctable=False)

    def name_display(self):
        return self.value.name

    def extensions(self):
        return self.value.extensions

    def doc(self):
        return self.value.doc

    def correctable(self):
        return self.value.correctable

    def ace_lexer(self):
        return ACE_LEXER_MAPPING.get(self.name, 'text')

    def pygments_lexer(self):
        return PYGMENTS_LEXER_MAPPING.get(self.name, 'text')

    def __str__(self):
        return self.name_display()

    def __repr__(self):
        return '<{}.{}>'.format(self.__class__.__name__, self.name)

    @classmethod
    def _get_choices(cls):
        # We hacked the member values to put LanguageDef-s instead of DB values
        # so we fix this here.
        # (("c", "C"), ("cpp", "C++"), ("csharp", "C#"), …)
        return tuple((member.name, member.name_display()) for member in cls)


ACE_LEXER_MAPPING = {
    'c': 'c_cpp',
    'cpp': 'c_cpp',
    'pascal': 'pascal',
    'ocaml': 'ocaml',
    'scheme': 'scheme',
    'haskell': 'haskell',
    'java': 'java',
    'ada': 'ada',
    'php': 'php',
    'perl': 'perl',
    'lua': 'lua',
    'csharp': 'csharp',
    'python2': 'python',
    'python3': 'python',
    'vb': 'vbscript',
    'js': 'javascript',
}

PYGMENTS_LEXER_MAPPING = {
    'c': 'c',
    'cpp': 'cpp',
    'pascal': 'pascal',
    'ocaml': 'ocaml',
    'scheme': 'scheme',
    'haskell': 'haskell',
    'java': 'java',
    'python2': 'python',
    'python3': 'python',
    'ada': 'ada',
    'php': 'php',
    'js': 'javascript',
    'vb': 'vb.net',
    'perl': 'perl',
    'lua': 'lua',
    'csharp': 'csharp',
    'fsharp': 'fsharp',
    'brainfuck': 'brainfuck',
}
