from jdlinker import javadoc_role

__version = '1.0.4'


def setup(app):
    app.info('Initializing sphinx-JDLinker version ' + __version + '!')
    app.add_role('javadoc', javadoc_role)
    app.add_config_value('javadoc_links', [], 'env')
    return {'version': __version}
