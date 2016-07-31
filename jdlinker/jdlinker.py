from docutils import nodes, utils
from docutils.parsers.rst import Directive


javadoc_imports = dict()


class JavaDocImportDirective(Directive):

    # Allow content in the directive.
    has_content = True

    def run(self):
        # Add a dictionary entry using the file from which this directive originates and the content of that directive.
        # Note that one specific page will only ever have one import directive, so it's okay to potentially overwrite an
        # existing key value here.
        javadoc_imports[self.state.document.settings.env.docname] = self.content
        return []


def javadoc_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    # Fetches the specified JavaDoc links from the configuration file
    javadoc_links = inliner.document.settings.env.app.config.javadoc_links
    # If there are no javadoc links, yell at somebody!
    if not javadoc_links:
        return error(inliner, lineno, rawtext, 'The JavaDoc links have not been set in the configuration!')

    # If we should dump the javadoc links to a file. We'll use this value later, once we actually have the javadoc link.
    dump_links = inliner.document.settings.env.app.config.javadoc_dump

    # Replace any new lines and spaces. This will allow input spanning multiple lines and the spaces have no real
    # effect in the calculation of the display text and the final javadoc link.
    text = text.replace('\n', '').replace(' ', '')

    # Handle any possible imports.
    text = handle_imports(text, inliner.document.settings.env.docname)

    # A boolean value on whether there is a parenthesis in the text. If there is no parenthesis, then it should be
    # assumed that the javadoc role is not attempting to link to a method.
    is_there_parenthesis = False
    # The text before the parenthesis. Specifically the opening (. If there are no parenthesis, then this will default
    # to the original text
    text_before_parenthesis = text
    # The text inside the parenthesis. ()
    text_inside_parenthesis = ''
    # If there is an opening parenthesis in the text, then we know that the link wants to link to a method
    if '(' in text:
        # If there is no closing parenthesis, then we will not bother trying to parsing it
        if ')' not in text:
            return error(inliner, lineno, rawtext, 'A method parenthesis was opened but not closed!')
        # If there is more than one opening parenthesis, error now
        if text.count('(') > 1:
            return error(inliner, lineno, rawtext, 'Found too many opening parenthesis. What are you trying to do?')
        # If there is more than one closing parenthesis, error now
        if text.count(')') > 1:
            return error(inliner, lineno, rawtext, 'Found too many closing parenthesis. What are you trying to do?')
        # We know there are valid parenthesis specified
        is_there_parenthesis = True
        # Set the text before the parenthesis to, well the text before the parenthesis
        text_before_parenthesis = text.rpartition('(')[0]
        # Set the text inside the parenthesis to, well...
        text_inside_parenthesis = text.rpartition('(')[2].rpartition(')')[0]
    # Else if there is a closing parenthesis in the text, but not opening parenthesis, then an error was made
    elif ')' in text:
        return error(inliner, lineno, rawtext, 'A closing method parenthesis was found but an opening one was not!')

    # If there is no dot before the parenthesis...you guessed it, error!
    if '.' not in text_before_parenthesis:
        return error(inliner, lineno, rawtext, 'A dot was not found in the text! Cannot link to a JavaDoc without a'
                                               'package! Default packages are not supported.')

    # The text before the parenthesis, before the last dot...yeah. Example:
    # Text: 'com.some.package.SomeClass'
    # Text Before Parenthesis: ^ Same (there is no parenthesis)
    # Text Before Parenthesis, Before Last Dot: 'com.some.package'
    #
    # Or perhaps with a method:
    # Text: 'com.some.package.SomeClass#someMethod()'
    # Text Before Parenthesis: 'com.some.package.SomeClass#someMethod'
    # Text Before Parenthesis, Before Last Dot: 'com.some.package'
    #
    # Obviously methods cannot have dots in them, so we are guaranteed either a package or an internal class.
    text_before_parenthesis_before_last_dot = text_before_parenthesis.rpartition('.')[0]

    # The text before the parenthesis, after the last dot. Similar to the previous one:
    # Text: 'com.some.package.SomeClass#someMethod()'
    # Text Before Parenthesis: 'com.some.package.SomeClass#someMethod'
    # Text Before Parenthesis, After Last Dot: 'SomeClass#someMethod'
    #
    # Note that this includes the method as well as the method hash. The 'SomeClass' part, is simply what will be
    # referred to as the 'last object'. That is, the text after the last dot is the referring 'last object'. This does
    # not include internal classes, that is calculated separately.
    #
    # Note that we will split the method from this later, that is, if one is there.
    text_before_parenthesis_after_last_dot = text_before_parenthesis.rpartition('.')[2]

    # The text before the parenthesis, before the last object. This one is a bit confusing, and if you're confused
    # about it let's start off with an example:
    #
    # Text: 'com.some.package.SomeClass#someMethod()'
    # Text Before Parenthesis: 'com.some.package.SomeClass#someMethod'
    # Text Before Parenthesis, Before Last Dot: 'com.some.package'
    # Text Before Parenthesis, Before Last Object: 'package'
    #
    # So we know from text_before_parenthesis_after_last_dot that the 'last object' will be 'SomeClass'. However, we
    # want the 'object' before the 'last object'. So we need to get the text before the last dot, that is, the text
    # all before the 'last object'. Then we need to retrieve the 'last object' from that new string. This is our
    # second to last object.
    #
    # We need this for when we go to calculate whether this is linking to a normal class, or an internal class. For a
    # normal class, the second to last object will be part of the package, and thus start with a lowercase letter. If
    # it starts with a capital letter, then we know that this is referencing an internal class.
    text_before_parenthesis_second_to_last_object = text_before_parenthesis_before_last_dot.rpartition('.')[2]

    # If this is internal, then we need to fetch the package for the internal link.
    internal_package = ''
    # Basically we need to check the first character is a capital letter. If it is, then we know we are dealing with an
    # internal class. If it is not, then it is likely a package.
    if text_before_parenthesis_second_to_last_object[0].isupper():
        # The text before the last dot will actually lead to the 'parent' class, instead of the package like we need
        # later on. So we need to partition back even further.
        internal_package = text_before_parenthesis_before_last_dot.rpartition('.')[0] + '.'

    # Now we will split the method off of the 'last object', but only if there is one. If there isn't, then it is fine
    # to leave it as-is.
    last_object = text_before_parenthesis_after_last_dot
    # The method text itself. This does not include the hash that precedes it.
    method_text = ''
    # The field text. This does not include the hash that precedes it.
    field_text = ''
    # If there is a hash in the text, and there are parenthesis, then we know that this is a method link.
    if '#' in text_before_parenthesis_after_last_dot and is_there_parenthesis:
        # Set the method text to what is before the parenthesis, partitioned after the hash. Example:
        #
        # Text: 'com.some.package.SomeClass#someMethod()'
        # Text Before Parenthesis: 'com.some.package.SomeClass#someMethod'
        # Method Text: 'someMethod'
        method_text = text_before_parenthesis_after_last_dot.rpartition('#')[2]
        # Partition the method off for the 'last object'.
        last_object = last_object.rpartition('#')[0]
    # Else if there is a hash in the text, yet there is no parenthesis, then we know that this is referencing a field.
    elif '#' in text:
        # Sets the field text to what is after the hash. Example:
        #
        # Text: 'com.some.package.SomeClass#SOME_FIELD'
        # Field Text: 'SOME_FIELD'
        field_text = text.rpartition('#')[2]
        # Partition the field off for the 'last object'.
        last_object = last_object.rpartition('#')[0]

    # Get the jd url link. We'll need this for the actual jd linking.
    jd_url_link = jd_link(javadoc_links, text_before_parenthesis)

    # If jd_url_link returns None, then we do not have a proper javadoc url to actually work with. Error here.
    if not jd_url_link:
        return error(inliner, lineno, rawtext, 'Could not find an appropriate javadoc url for the specified role!')

    # Check if this is actually a package reference. If so, then link to that instead.
    if not last_object[0].isupper():
        return handle_return(text, jd_url_link + text.replace('.', '/') + '/package-summary.html', rawtext, options,
                             dump_links)

    # Now we can see if method_text and field_text are empty or not. If they are both empty, then we know we are
    # referencing an object and not a method or field. If is_internal is False, then we know we have a regular link to
    # a normal object. The JD link will reflect that.
    if not method_text and not field_text and not internal_package:
        # Create a url using the javadoc url specified in the config, as well as all of the text before the
        # parenthesis replaced with dashes.
        url_text = jd_url_link + text_before_parenthesis.replace('.', '/') + '.html'
        return handle_return(last_object, url_text, rawtext, options, dump_links)
    # If this is not a method or a field, yet is an internal link, then we create a link for an internal javadoc!
    elif not method_text and not field_text and internal_package:
        # Combine the second to last object and the last object to form the display text.
        javadoc_text = text_before_parenthesis_second_to_last_object + '.' + last_object
        # With this, we append the internal package to the url, as well as throw on our already existing javadoc display
        # text.
        url_text = jd_url_link + internal_package.replace('.', '/') + javadoc_text + '.html'
        return handle_return(javadoc_text, url_text, rawtext, options, dump_links)
    # Else if this is a method and is not an internal link, then link to a standard method.
    elif method_text and not internal_package:
        # Create the display text by combining the 'last object' with the method and any text from inside the
        # parenthesis
        javadoc_text = last_object + '#' + method_text + '(' + display_text_in_parenthesis(text_inside_parenthesis) +\
                       ')'
        # Gets the end of the url text by specifying the text inside the parenthesis, as method arguments are specified
        # at the end of the javadoc url.
        url_method_text = in_method_link(text_inside_parenthesis)
        # We need to add a dot to the end of text_before_parenthesis_before_last_dot
        text_before_parenthesis_before_last_dot += '.'
        # Take the javadoc url, the package, the last object, a .html# appending, the method text and the url method
        # text and bring them together to form our method url!
        url_text = jd_url_link + text_before_parenthesis_before_last_dot.replace('.', '/') + last_object + '.html#' +\
            method_text + url_method_text
        return handle_return(javadoc_text, url_text, rawtext, options, dump_links)
    # Else if this is a method and is an internal class reference...
    elif method_text and internal_package:
        # Combine the section to last object with the last object (the internal class). Then append the method to it.
        javadoc_text = text_before_parenthesis_second_to_last_object + '.' + last_object + '#' + method_text + '(' +\
                       display_text_in_parenthesis(text_inside_parenthesis) + ')'
        # Take the jd link and append the internal package, replacing the dots to dashes. Then append the object
        # reference to it and then the .html#. We then just add the method to the end of that.
        url_text = jd_url_link + internal_package.replace('.', '/') + text_before_parenthesis_second_to_last_object +\
            '.' + last_object + '.html#' + method_text + in_method_link(text_inside_parenthesis)
        return handle_return(javadoc_text, url_text, rawtext, options, dump_links)
    # Else if this is a field and not an internal class reference...
    elif field_text and not internal_package:
        # Create the javadoc text by adding the last object and the field text together.
        javadoc_text = last_object + '#' + field_text
        # We need to add a period at the end of the text before the last dot once again.
        text_before_parenthesis_before_last_dot += '.'
        # Build our url with the jd link, text before the last dot with dots replaced with dashes, the last object, the
        # standard .html#. Then we just add the field text to the end of that.
        url_text = jd_url_link + text_before_parenthesis_before_last_dot.replace('.', '/') + last_object + '.html#' +\
            field_text
        return handle_return(javadoc_text, url_text, rawtext, options, dump_links)
    # Else if this is a field in an internal class...
    elif field_text and internal_package:
        # Create the display text by combining the second to last object with the last object and the field text.
        javadoc_text = text_before_parenthesis_second_to_last_object + '.' + last_object + '#' + field_text
        # Create a url with once again the jd link, the internal package that has again replaced dots with dashes, the
        # text before the last object and the last object with the standard .html# and the field text...
        url_text = jd_url_link + internal_package.replace('.', '/') + text_before_parenthesis_second_to_last_object +\
            '.' + last_object + '.html#' + field_text
        return handle_return(javadoc_text, url_text, rawtext, options, dump_links)
    return error(inliner, lineno, rawtext, 'Could not parse the javadoc role! Are you certain that your input is'
                                           'correct?')


def handle_imports(text, page):
    # Set a class to check variable equal to the text. If there is a hash in the text, then we will change the value to
    # just the part before the hash. Otherwise it is safe to assume that this is referencing a class.
    class_to_check = text
    # Create a string to store the inside arguments.
    inside_arguments = ''
    # The text after the hash. We will need to re-append it later.
    method_text = ''
    # If there are parenthesis, then we have a method to work with.
    if '(' in text and ')' in text:
        # Partition out the part from before the method hash.
        class_to_check = text.rpartition('#')[0]
        # Set the arguments equal to the text inside the parenthesis.
        inside_arguments = text.rpartition('(')[2].rpartition(')')[0]
        # We only really want the part before the parenthesis for this.
        method_text = '#' + text.rpartition('#')[2].rpartition('(')[0]
    # If there is more than one dot in class_to_check, then it is likely that this is an absolute javadoc reference. We
    # also need to check if there are any arguments, if there is, then it is possible that one of the arguments
    # reference an import. Unfortunately, there is no reliable way to see if an argument references an import right
    # here, so we'll have to do it later on.
    if class_to_check.count('.') > 1 and not inside_arguments:
        return text
    # Import the specified javadoc class, if necessary. Also appends the method text.
    imported_class = check_against_imports(class_to_check, page) + method_text
    # If there is no method, then there are no arguments we have to match up with and we can return here.
    if not method_text:
        return imported_class
    # Initialize an imported arguments variable to store our imported arguments (obviously :P).
    imported_arguments = '('
    # If there is a comma in the inside arguments, then we have to deal with multiple arguments
    if ',' in inside_arguments:
        # For every argument separated by a comma, check if it is possible an import statement.
        for argument in inside_arguments.split(','):
            # If there is more than one dot in this argument, then it is likely an absolute reference. We can just add
            # the normal argument.
            if argument.count('.') > 1:
                imported_arguments += argument + ','
                continue
            # Append the imported javadoc argument to the imported arguments, as well as a comma.
            imported_arguments += check_against_imports(argument, page) + ','
        # Remove the last comma, as it is an extra comma we do not want to include.
        imported_arguments = imported_arguments[:-1]
    # Else we have a single argument, or no argument!
    else:
        # If there is an actual argument, then check it against the imports. If there are no arguments, then it is safe
        # to continue on.
        if inside_arguments:
            # If there is only one dot or no dots, then it is possible that this is referencing an import.
            if inside_arguments.count('.') <= 1:
                # Now we can check the argument against the imported arguments.
                imported_arguments += check_against_imports(inside_arguments, page)
            # Else it is not referencing an import and we can add it as-is.
            else:
                imported_arguments += inside_arguments
    # Finally append a closing parenthesis here.
    imported_arguments += ')'
    # Now return the imported class and the method arguments.
    return imported_class + imported_arguments


def check_against_imports(text_to_check, page):
    # We need to remove any generics when we are comparing the text_to_check against the imports. So we copy the generic
    # text here to be re-applied later.
    generic_text = ''
    # If there is an arrow in the text_to_check, then we know we have generics.
    if '<' in text_to_check:
        # Set the generic text to what's inside the generic. We also will need to re-apply the arrows after
        # partitioning.
        generic_text = '<' + text_to_check.rpartition('<')[2].rpartition('>')[0] + '>'
        # Set the original text_to_check to the part before the generic.
        text_to_check = text_to_check.rpartition('<')[0]

    # Iterate through the javadoc directives to find the correct page and import for the text_to_check.
    for javadoc_directive in javadoc_imports.items():
        # If the directive page is not equal to the specified page, ignore this directive.
        if javadoc_directive[0] is not page:
            continue
        # Now that we have the correct page, we need to iterate through the directive imports to find one that matches
        # our text_to_check.
        for javadoc_directive_import in javadoc_directive[1]:
            # We need to get the last object for the import so that we can attempt to match it against the
            # text_to_check.
            last_object = javadoc_directive_import.rpartition('.')[2]
            # We need the second to last object in-case this import references an internal class.
            second_to_last_object = javadoc_directive_import.rpartition('.')[0].rpartition('.')[2]
            # If the first character of the second to last object is a capital letter, then we know we are referencing
            # an internal class. We need to check the text as such.
            if second_to_last_object[0].isupper():
                # Check if the text is equal to the import. If it is, then we have the correct import.
                if text_to_check == second_to_last_object + '.' + last_object:
                    # Return the import plus the generic text, if there was any.
                    return javadoc_directive_import + generic_text
            # Else, it is safe to assume that this is a standard object reference, not an internal one.
            else:
                # Check if the text is equal to the last object from the import. If it is, then we have the correct
                # import.
                if text_to_check == last_object:
                    # Return the import plus the generic text, if there was any.
                    return javadoc_directive_import + generic_text
    # If we could not match it against any imports, return the text.
    return text_to_check


def error(inliner, lineno, rawtext, reason):
    # Print an error message with the text that caused the error and the reason why the error occurred
    error_message = inliner.reporter.error('An error has occurred while attempting to evaluate the string "{0}"! {1}'
                                           .format(rawtext, reason), line=lineno)
    return [inliner.problematic(rawtext, rawtext, error_message)], [error_message]


def jd_link(javadoc_links, text_to_check):
    # For each value in the javadoc_links dictionary.
    for value in javadoc_links.items():
        # Iterate through the root packages.
        for root in value[1]:
            # If the text_to_check starts with the root package, then we have the correct JavaDoc url.
            if text_to_check.startswith(root):
                return value[0]


def in_method_link(inside_parenthesis_text):
    # If the text from inside the parenthesis is blank, then this method has no arguments. Javadoc links to methods with
    # no arguments have a '--' at the end of them. Thus we return that.
    if not inside_parenthesis_text:
        return '--'
    # Otherwise, if there is a comma in the parenthesis, then we know we have multiple arguments.
    if ',' in inside_parenthesis_text:
        # The '-' will go at the beginning. We will later append another '-' to the end via the for loop.
        url_end_text = '-'
        # Iterate through each argument inside the parenthesis.
        for argument in inside_parenthesis_text.split(','):
            # Add each argument to the end url.
            url_end_text += handle_url(argument)
        return url_end_text
    # Else this is single argument, so we may add '-' to the beginning of the method url and let the handle_url function
    # handle appending the other '-' to the end of it.
    else:
        return '-' + handle_url(inside_parenthesis_text)


def handle_url(argument):
    # If there is a generic in the argument, do not use it in the url link. Generics do not belong in the url.
    if '<' in argument:
        # If there are ellipsis inside the argument, then when we partition out for the generic, the ellipsis
        # will be removed. We want to add it back.
        if '...' in argument:
            # Partition out the generic while still retaining the ellipsis.
            return argument.rpartition('<')[0] + '...-'
        else:
            # Else we can just partition out the generic for the url. Then add a '-' to the end of it.
            return argument.rpartition('<')[0] + '-'
    else:
        # Else append just the argument and the '-' to the end of it.
        return argument + '-'


def display_text_in_parenthesis(inside_parenthesis_text):
    # If there is a comma inside the parenthesis, then we know we have multiple arguments.
    if ',' in inside_parenthesis_text:
        # We will create a new inside display text formatted the way we want it.
        new_inside_text = ''
        # For each argument inside the parenthesis, split it by the comma.
        for argument in inside_parenthesis_text.split(','):
            new_inside_text += handle_display(argument)
        # Once we have our new text, remove the last two characters from it. This is simply a leftover comma and space
        # from the previous for loop.
        return new_inside_text[:-2]
    # If there is no comma, then we can just call handle_display with the text inside the parenthesis. Then we need to
    # remove the comma that comes at the end of it.
    return handle_display(inside_parenthesis_text)[:-2]


def handle_display(argument):
    display_text = ''
    # If there is a dot, we can safely partition using the dot.
    if '.' in argument:
        # If there is a generic in this argument...
        if '<' in argument:
            # We need to get the text inside this generic.
            argument_generic = argument.rpartition('<')[2].rpartition('>')[0]
            # Now we add the argument to the new inside text by partitioning out the generic, then later adding
            # it back. This is needed as we partition out the period from the regular argument, and we do not
            # want to accidentally partition the period from the generic instead (in the case of an internal
            # generic).
            display_text += argument.rpartition('<')[0].rpartition('.')[2] + '<' + argument_generic + '>'
            # If there is an ellipsis, we want to re-add it back to the end of the new inside text.
            if '...' in argument:
                display_text += '..., '
            # Else, just include the ', ' in-case of other arguments.
            else:
                display_text += ', '
        else:
            # If there are ellipsis in the argument, we need special handling.
            if '...' in argument:
                # Partition out the ellipsis so that we may partition out the display object.
                display_text += argument.rpartition('...')[0].rpartition('.')[2] + '..., '
            else:
                # Partition using the dot to get the object we will display. Add a comma and a space for any
                # consecutive arguments.
                display_text += argument.rpartition('.')[2] + ', '
    else:
        # Else, just append the argument and a comma. It is possible a primitive was specified, and obviously
        # primitive types will not have dots in them.
        display_text += argument + ', '
    return display_text


def strip_generic_url(url):
    # If there is a generic in the url, remove it.
    if '<' in url:
        # Get the part before the generic.
        before_generic = url.rpartition('<')[0]
        # Get the part after the generic.
        after_generic = url.rpartition('>')[2]
        # Add the two pieces together, with the generic now out of the url.
        return before_generic + after_generic
    # If there was no generic in the url, then we have no worries.
    return url


def handle_return(javadoc_text, url, rawtext, options, dump_links):
    # If we need to dump the links, then do so.
    if dump_links:
        # Open the file in 'a' mode, write the javadoc display text and the url text to the file.
        open('javadoc_dump.txt', 'a').write(rawtext.replace('\n', '').replace(' ', '') + '=' + javadoc_text + '=' + url
                                            + '\n')

    return [nodes.reference(rawtext, utils.unescape(javadoc_text), refuri=strip_generic_url(url), **options)], []


def purge_imports(app, env, docname):
    # If the doc has any imports, purge them.
    if docname in javadoc_imports.keys():
        # Delete any imports for the file.
        del javadoc_imports[docname]


def merge_imports(env, docnames, other):
    # Update our imports.
    javadoc_imports.update(other)
