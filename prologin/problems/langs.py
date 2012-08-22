from collections import namedtuple

Language = namedtuple('Language', ['ext', 'title', 'doc'])

langs = {
    0: Language(ext=['.c'], title='C', doc='c'),
    1: Language(ext=['.cc', '.c++', '.cpp'], title='C++', doc='cpp'),
    2: Language(ext=['.pas', '.pascal'], title='Pascal', doc='pascal'),
    3: Language(ext=['.ml', '.ocaml'], title='OCaml', doc='ocaml'),
    4: Language(ext=['.java'], title='Java', doc='java'),
    6: Language(ext=['.cs'], title='C#', doc=''),
    9: Language(ext=['.py', '.python'], title='Python', doc='python'),
    10: Language(ext=['.adb'], title='Ada', doc='ada'),
    11: Language(ext=['.php'], title='PHP', doc='php'),
    12: Language(ext=['.fs'], title='F#', doc=''),
    13: Language(ext=['.scm'], title='Scheme', doc='scheme'),
    14: Language(ext=['.hs'], title='Haskell', doc='haskell'),
    15: Language(ext=['.vb'], title='VB', doc=''),
    16: Language(ext=['.bf'], title='Brainf*ck', doc=''),
    17: Language(ext=['.js'], title='Javascript', doc=''),
}
