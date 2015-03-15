from prologin.utils import ChoiceEnum


class LanguageDef:
    def __init__(self, name, exts, doc=None, checkable=True):
        self.name = name
        self.exts = exts
        self.doc = doc
        self.checkable = checkable

    def __str__(self):
        return self.name

    def serialize(self):
        return str(self)


class Language(ChoiceEnum):
    c = LanguageDef("C", ['.c'], doc='c')
    cpp = LanguageDef("C++", ['.cc', '.c++', '.cpp'], doc='cpp')
    pascal = LanguageDef("Pascal", ['.pas', '.pascal'], doc='pascal')
    ocaml = LanguageDef("OCaml", ['.ml', '.ocaml'], doc='ocaml')
    scheme = LanguageDef("Scheme", ['.scm'], doc='scheme')
    haskell = LanguageDef("Haskell", ['.hs'], doc='haskell')
    java = LanguageDef("Java", ['.java'], doc='java')
    python2 = LanguageDef("Python2", ['.py', '.py2'], doc='python2')
    python3 = LanguageDef("Python3", ['.py3'], doc='python3')
    ada = LanguageDef("Ada", ['.adb'], doc='ada')
    php = LanguageDef("PHP", ['.php'], doc='php')
    js = LanguageDef("Javascript", ['.js'])
    vb = LanguageDef("VB", ['.vb'])
    perl = LanguageDef("Perl", ['.pl'])
    lua = LanguageDef("Lua", ['.lua'])
    csharp = LanguageDef("C#", ['.cs'])
    fsharp = LanguageDef("F#", ['.fs'])
    brainfuck = LanguageDef("Brainfuck", ['.bf'])
    pseudocode = LanguageDef("Pseudo-code", ['.txt'], checkable=False)
