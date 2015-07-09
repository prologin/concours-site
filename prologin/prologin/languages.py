from django.utils.translation import ugettext_lazy as _

from prologin.utils import ChoiceEnum


class LanguageDef:
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

    @classmethod
    def _get_choices(cls):
        # We hacked the member values to put LanguageDef-s instead of DB values (0-N)
        # so we fix this here.
        # (("c", "C"), ("cpp", "C++"), ("csharp", "C#"), …)
        return tuple((member.name, member.value.name) for member in cls)
