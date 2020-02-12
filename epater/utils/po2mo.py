import polib

# FIXME localization must be adapted for setuptools distribution...
# Maybe check some hints here: https://stackoverflow.com/questions/53285634/is-there-a-portable-way-to-provide-localization-of-a-package-distributed-on-pypi

languages = [
    'en',
    'fr',
]

files = [
    'interface',
    'interpreter',
]

for lang in languages:
    path = './locale/{}/LC_MESSAGES'.format(lang)
    for file in files:
        po = polib.pofile(path + '/{}.po'.format(file))
        po.save_as_mofile(path + '/{}.mo'.format(file))

