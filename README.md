# sphinx-JDLinker
sphinx-JDLinker is a custom Sphinx extension that allows you to link to a JavaDoc website through your documentation.

sphinx-JDLinker does not require local jars, nor does it attempt to connect to any JavaDoc website. Instead, what it
does is attempt to parse a JavaDoc role in order to produce the desired output: a link to the JavaDoc website.

## Installing
sphinx-JDLinker is available on PyPI:

```pip install sphinx-JDLinker```

## Minimum Requirements
There's a few requirements to keep in mind when using sphinx-JDLinker. Because sphinx-JDLinker relies completely on
string manipulation, it can be easy to mess up. However this comes at the advantage of not having to use local jars, or
connect to any JavaDoc website.

- Sphinx 1.3
- Online JavaDoc Website (I hope you have this if you're here!)
- Java packages must be lower case. The reason for this is that sphinx-JDLinker has to determine the difference between
a normal class and an internal class. Hopefully your project should already follow this. If it doesn't, I'd highly
advise fixing this!
- Default packages are not supported. Again, fix this if your project is using default packages!

Most projects should already easily meet these requirements anyway, so no worries here.

## Usage
Using sphinx-JDLinker is relatively simple. The first thing you must do is add the `javadoc_links` config option to
your `conf.py`:

```python
javadoc_links = {'http://myjavadocwebsite.com/': ['my.root.package']}
```

Now let's explain this a bit. The `javadoc_links` variable must be a dictionary, storing the JavaDoc url as well as a
list of 'root packages'. The root package is essentially what sphinx-JDLinker uses to identify a JavaDoc reference, so
that the linking to multiple JavaDoc websites does not collide. So if your Java files begin at `com.my.package`, then when
sphinx-JDLinker sees a JavaDoc reference in your documentation that begins with `com.my.package`, it will know that
you're attempting to link to the corresponding `com.my.package` JavaDoc website.

The root packages are stored as a list as to allow multiple root packages. An example of multiple root packages may be
found below:

```python
javadoc_links = {'http://myjavadocwebsite.com/': ['my.root.package', 'some.other.package']}
```

Now we need to add sphinx-JDLinker to sphinx itself. In your `conf.py` file, add `jdlinker` to your extensions:

```python
extensions = ['jdlinker']
```

Now that we've set the config options, it's time to create JavaDoc links in our sphinx documentation. We need to create
a JavaDoc role:

```
:javadoc:`com.my.package.MyJavaClass`
```

It's as simple as that. This will create a reference to MyJavaClass pointing to the set JavaDoc website for
`com.my.package`. Of course, more advanced linkages are supported as well:

```
:javadoc:`com.my.package.MyClass.MyInternalClass#myMethod(com.my.package.MyJavaClass, com.my.package.MyOtherClass)`
```

This will point to the method `myMethod(MyJavaClass, MyOtherClass)` for `MyClass.MyInternalClass`, automatically
creating a reference to the method specified. Note that generics are also supported:

```
:javadoc:`com.my.package.MyClass<Foo>`
```

Since the generic isn't used in the url, it is not necessary to specify the full package of `Foo`. The generic is only
used for display.

We can also link to fields:

```
:javadoc:`com.my.package.MyClass#MY_FIELD`
```

We can even link to the page for a specified package:

```
:javadoc:`com.my.package`
```

### Imports

Of course, if you want to keep the source documentation clean from all of these long packages that are required for
linking, we can use imports. Imports are specified via a `javadoc-import` directive:

```
.. javadoc-import::
    com.my.package.MyClass
    com.my.package.MyOtherClass
```

Now when we want to link to `MyClass` or `MyOtherClass`, it's as simple as this:

```
:javadoc:`MyClass`
:javadoc:`MyOtherClass`
```

Imports will also work for method parameters:

```
:javadoc:`MyClass#myMethod(MyOtherClass)`
```

## Advanced

An advanced debug option is available that you may specify in your `conf.py` file. If enabled, the `javadoc_dump`
option will dump all of the JavaDoc references into a `javadoc_dump.txt` file. It is highly recommended to keep this
disabled in production!

## Updating

If there comes to be a time that the documentation project's JavaDoc links need to be updated, you may use
[jdlinker-parser](https://github.com/12AwsomeMan34/jdlinker-parser) to help identify what needs to be updated.
It will tell you what specific JavaDoc links that could not be found, as well as where the link was found.
