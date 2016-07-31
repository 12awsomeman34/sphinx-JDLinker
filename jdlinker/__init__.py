from . import jdlinker
from os import remove, path

__version = '1.2.1'


def setup(app):
    app.info('Initializing sphinx-JDLinker version ' + __version + '!')
    app.add_role('javadoc', jdlinker.javadoc_role)
    app.add_config_value('javadoc_links', {}, 'env')
    app.add_config_value('javadoc_dump', False, 'env')
    app.add_directive('javadoc-import', jdlinker.JavaDocImportDirective)
    app.connect('env-purge-doc', jdlinker.purge_imports)
    app.connect('env-merge-info', jdlinker.merge_imports)

    # Unfortunately there isn't a reliable way to fetch the javadoc_dump config option from here, so we have to remove
    # the javadoc_dump.txt file and allow the javadoc role to re-generate it if the config option is set from there.
    if path.isfile('javadoc_dump.txt'):
        remove('javadoc_dump.txt')

    return {'version': __version}
