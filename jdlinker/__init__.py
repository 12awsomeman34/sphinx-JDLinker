
from . import jdlinker

__version = '2.0'

def setup(app):
    app.add_role('javadoc', jdlinker.javadoc_role)
    app.add_config_value('javadoc_links', {}, 'env')
    app.add_config_value('javadoc_dump', False, 'env')
    app.add_directive('javadoc-import', jdlinker.JavaDocImportDirective)
    app.connect('env-purge-doc', jdlinker.purge_imports)
    app.connect('env-merge-info', jdlinker.merge_imports)
