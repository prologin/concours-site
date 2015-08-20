from django.utils.translation import ugettext_lazy as _

from prologin.utils import ChoiceEnum


class LanguageDef:
    """
    Represent a single programming language.
    `name`: the human readable (translated if needed) language name
    `extensions`: the list of corresponding extensions
    `ace_mode`: the name of the Javascript Ace editor 'mode' (ie. syntax highlighter)
    `doc` (optional): the name of the documentation folder for this language
    `correctable`: if programs wrote in this language can be sent to the correction system
                   (typically not true for pseudo-code)
    """
    def __init__(self, name, extensions, ace_mode, doc=None, correctable=True):
        self.name = name
        self.extensions = extensions
        self.ace_mode = ace_mode
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
    c = LanguageDef("C", ['.c'], 'c_cpp', doc='c')
    cpp = LanguageDef("C++", ['.cc', '.c++', '.cpp'], 'c_cpp', doc='cpp')
    pascal = LanguageDef("Pascal", ['.pas', '.pascal'], 'pascal', doc='pascal')
    ocaml = LanguageDef("OCaml", ['.ml', '.ocaml'], 'ocaml', doc='ocaml')
    scheme = LanguageDef("Scheme", ['.scm'], 'scheme', doc='scheme')
    haskell = LanguageDef("Haskell", ['.hs'], 'haskell', doc='haskell')
    java = LanguageDef("Java", ['.java'], 'java', doc='java')
    python2 = LanguageDef("Python 2", ['.py', '.py2'], 'python', doc='python2')
    python3 = LanguageDef("Python 3", ['.py3'], 'python', doc='python3')
    ada = LanguageDef("Ada", ['.adb'], 'ada', doc='ada')
    php = LanguageDef("PHP", ['.php'], 'php', doc='php')
    js = LanguageDef("Javascript", ['.js'], 'javascript')
    vb = LanguageDef("VB", ['.vb'], 'vbscript')
    perl = LanguageDef("Perl", ['.pl', '.perl'], 'perl')
    lua = LanguageDef("Lua", ['.lua'], 'lua')
    csharp = LanguageDef("C#", ['.cs'], 'csharp')
    fsharp = LanguageDef("F#", ['.fs'], 'text')
    brainfuck = LanguageDef("Brainfuck", ['.bf'], 'text')
    pseudocode = LanguageDef(_("Pseudocode"), ['.txt'], 'text', correctable=False)

    @classmethod
    def _get_choices(cls):
        # We hacked the member values to put LanguageDef-s instead of DB values (0-N)
        # so we fix this here.
        # (("c", "C"), ("cpp", "C++"), ("csharp", "C#"), …)
        return tuple((member.name, member.value.name) for member in cls)
