from django.utils.translation import ugettext_lazy as _

from prologin.utils import ChoiceEnum


class LanguageDef:
    """
    Represent a programming language and its properties.
    """
    identity = lambda e: e

    def __init__(self, name, extensions, camisole=None, doc=None, time=identity, memory=identity):
        """
        :param name: the language full, human name
        :param extensions: file extension(s) accepted for this language
        :param camisole: the corresponding camisole language name, if correctable
        :param doc: the documentation name for this language
        :param time: a callable giving the maximum user time limit given the raw user time limit
        :param memory: a callable giving the maximum memory limit given the raw memory limit
        """
        self.name = name
        self.extensions = extensions
        self.doc = doc
        self.camisole_name = camisole
        self.time_limit = time

        # Hardcoded increase to account for various external factors and because
        # we don't want those limits to be really tight, we mainly want to avoid
        # really consuming programs asymptotically. Therefore, we always add
        # 4MB of padding memory and multiply the displayed constraint by two.
        self.memory_limit = lambda x: 4096 + memory(x) * 2

    def __str__(self):
        return str(self.name)  # force gettext resolution

    def serialize(self):
        return str(self)

    @property
    def correctable(self):
        return self.camisole_name is not None


@ChoiceEnum.sort()
class Language(ChoiceEnum):
    """
    Machine-name (member name, left of equal sign) must be less than
    16 character long.
    """
    c = LanguageDef("C", ['.c'], doc='c',
        camisole='c', memory=lambda m: m + 4096)
    cpp = LanguageDef("C++", ['.cc', '.c++', '.cpp'], doc='cpp',
        camisole='c++', memory=lambda m: m + 4096)
    csharp = LanguageDef("C#", ['.cs'],
        camisole='c#', memory=lambda m: m + 50000, time=lambda t: t + 0.038)
    haskell = LanguageDef("Haskell", ['.hs'], doc='haskell',
        camisole='haskell', memory=lambda m: 5 * m + 30000, time=lambda t: 4 * t + 0.200)
    java = LanguageDef("Java", ['.java'], doc='java',
        camisole='java', memory=lambda m: 5 * m + 30000, time=lambda t: 4 * t + 0.200)
    ocaml = LanguageDef("OCaml", ['.ml', '.ocaml'], doc='ocaml',
        camisole='ocaml', memory=lambda m: 2 * m + 15000)
    python = LanguageDef("Python", ['.py'], doc='python',
        camisole='python', memory=lambda m: 5 * m + 9000, time=lambda t: 15 * t)
    php = LanguageDef("PHP", ['.php'], doc='php',
        camisole='php', memory=lambda m: 5 * m + 36384, time=lambda t: 8 * t)
    rust = LanguageDef("Rust", ['.rs'],
        camisole='rust', memory=lambda m: m + 4096)

    ada = LanguageDef("Ada", ['.adb'], doc='ada',
        camisole='ada', memory=lambda m: m + 4096)
    js = LanguageDef("Javascript", ['.js'],
        camisole='javascript', memory=lambda m: 5 * m + 26000, time=lambda t: 5 * t)
    lua = LanguageDef("Lua", ['.lua'],
        camisole='lua', memory=lambda m: m + 5000, time=lambda t: 10 * t)
    pascal = LanguageDef("Pascal", ['.pas', '.pascal'], doc='pascal',
        camisole='pascal', memory=lambda m: m + 4096)
    perl = LanguageDef("Perl", ['.pl', '.perl'],
        camisole='perl', memory=lambda m: m + 5000, time=lambda t: 10 * t)
    scheme = LanguageDef("Scheme", ['.scm'], doc='scheme',
        camisole='scheme', memory=lambda m: m + 36384, time=lambda t: 3 * t)

    pseudocode = LanguageDef(_("Pseudocode"), ['.txt'])

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
    def guess(cls, obj):
        if isinstance(obj, cls):
            return obj
        if isinstance(obj, LanguageDef):
            return cls(obj)
        # assume string
        obj = obj.lower().strip()
        # some special cases
        obj = {
            'caml': 'ocaml',
        }.get(obj, obj)
        try:
            # 'cpp', 'PYTHON'
            return cls[obj]
        except KeyError:
            pass
        # try harder
        for lang in cls:
            if lang.name_display().lower() == obj:
                return lang
            if obj in lang.extensions() or '.' + obj in lang.extensions():
                return lang
        return None

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
    'python': 'python',
    'js': 'javascript',
    'rust': 'rust',
}

PYGMENTS_LEXER_MAPPING = {
    'c': 'c',
    'cpp': 'cpp',
    'pascal': 'pascal',
    'ocaml': 'ocaml',
    'scheme': 'scheme',
    'haskell': 'haskell',
    'java': 'java',
    'python': 'python',
    'ada': 'ada',
    'php': 'php',
    'js': 'javascript',
    'perl': 'perl',
    'lua': 'lua',
    'csharp': 'csharp',
    'rust': 'rust',
}
