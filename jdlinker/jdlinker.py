
from docutils import nodes, utils
from docutils.parsers.rst import Directive
import re

javadoc_imports = dict()

class JavaDocImportDirective(Directive):
    has_content = True

    def run(self):
        new_content = []
        for jdlink in self.content:
            if ':' in jdlink:
                shorthand = jdlink.rpartition(':')[0]
                for javadoc_linker in self.state.document.settings.env.app.config.javadoc_links.values():
                    if len(javadoc_linker) == 2:
                        if shorthand == javadoc_linker[1]:
                            full_import = javadoc_linker[0] + '.' + jdlink.rpartition(':')[2]
                            new_content.append(full_import)
                            continue
            new_content.append(jdlink)
        # Note that one specific page should only ever have one import directive, so it's okay to potentially
        # overwrite an existing key-value pair here.
        javadoc_imports[self.state.document.settings.env.docname] = new_content
        return []

def javadoc_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    javadoc_links = inliner.document.settings.env.app.config.javadoc_links
    if not javadoc_links:
        return error(inliner, lineno, rawtext, 'The javadoc links have not been set in the configuration.')

    # This is the text that will be displayed on the actual html page.
    display_text = ''
    # Part of the jdlinker specification. If curly braces appear in the text, the text inside the curly braces will
    # override any display text on the html page.
    if '{' and '}' in text:
        display_text = text.rpartition('{')[2].rpartition('}')[0] # Only display the text inside the {}
        text = text.rpartition('{')[0] # Strip the curly braces from the text we will need for the jd link
    else:
        # todo, if no display text, need to set our own
        # problem with this current implementation: if you don't use the javadoc import directive, but instead manually
        # import, very ugly display text is shown
        display_text = text

    # Remove any whitespace in the text, this will be added back later as necessary
    text = text.replace('\n', '').replace(' ', '')

    if '<' in text:
        text = re.sub("[<>].*[<>]", "", text)

    full_imported_txt = text
    import_txt = text
    post_import_txt = ''
    if '#' in import_txt:
        import_txt = text.rpartition('#')[0]
        post_import_txt = '#' + text.rpartition('#')[2]
    full_imported_txt = get_full_import_package(inliner, import_txt) + post_import_txt

    package_str = ''
    post_package_str = ''
    for java_text in full_imported_txt.split('.'):
        post = False
        if not java_text:
            package_str += '.'
        elif not java_text[0].isupper() and not post:
            package_str += java_text + '.'
        else:
            post_package_str += java_text + '.'
            post = True
    post_package_str = post_package_str[:-1]

    class_str = ''
    method_str = ''
    arg_str = ''
    if '#' in post_package_str:
        class_str = post_package_str.rpartition('#')[0]
        method_str += '#' + post_package_str.rpartition('#')[2].rpartition('(')[0]
        arg_str = post_package_str.rpartition('(')[2].rpartition(')')[0]
        if arg_str:
            new_arg_str = ''
            if ',' in arg_str:
                for arg in arg_str.split(','):
                    new_arg_str += get_full_import_package(inliner, arg) + ','
                arg_str = new_arg_str[:-1]
            else:
                arg_str = get_full_import_package(inliner, arg_str)

    else:
        if not post_package_str:
            class_str = 'package-summary'
        else:
            class_str = post_package_str # note: assumes no generics

    url_params = package_str.replace('.', '/') + class_str + '.html'
    if method_str:
        url_params += method_str
        if arg_str:
            url_params += '-' + arg_str.replace(',', '-') + '-'
        else:
            url_params += '--'

    url = ''
    for jd_link in javadoc_links.keys():
        if javadoc_links[jd_link][0] in package_str:
            url += jd_link + url_params
            break

    if not url:
        return error(inliner, lineno, rawtext, 'No jd link found for package ' + package_str)

    return [nodes.reference(rawtext, utils.unescape(display_text), refuri=url, **options)], []

def get_full_import_package(inliner, java_class):
    for jd_directive in javadoc_imports.items():
        # We have to manually check each directive to see if it is the appropriate one for the current page.
        if jd_directive[0] is not inliner.document.settings.env.docname:
            continue
        for jd_directive_import in jd_directive[1]:
            if jd_directive_import.endswith(java_class):
                return jd_directive_import
    return java_class

def error(inliner, lineno, rawtext, reason):
    error_message = inliner.reporter.error('An error has occurred while attempting to evaluate the string "{0}"! {1}'
                                           .format(rawtext, reason), line=lineno)
    return [inliner.problematic(rawtext, rawtext, error_message)], [error_message]

def purge_imports(app, env, docname):
    if docname in javadoc_imports.keys():
        del javadoc_imports[docname]

def merge_imports(env, docnames, other):
    javadoc_imports.update(other)
