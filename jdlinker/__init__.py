from .jdlinker import javadoc_role
from os import remove

__version = '1.0.8'


def setup(app):
    app.info('Initializing sphinx-JDLinker version ' + __version + '!')
    app.add_role('javadoc', javadoc_role)
    app.add_config_value('javadoc_links', [], 'env')
    app.add_config_value('javadoc_dump', False, 'env')
    # Unfortunately there isn't a reliable way to fetch the javadoc_dump config option from here, so we have to remove
    # the javadoc_dump.txt file and allow the javadoc role to re-generate it if the config option is set from there.
    # We also stumble across the problem of if the file isn't there and we try to remove it. We have to swallow the
    # error and move on from there.
    try:
        # Try to remove the javadoc_dump.txt file if it exists.
        remove('javadoc_dump.txt')
    except Exception:
        # If there is an error, ignore it.
        pass

    return {'version': __version}
