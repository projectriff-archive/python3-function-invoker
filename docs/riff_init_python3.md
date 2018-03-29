## riff init python3

Initialize a python3 function

### Synopsis

Generate the function based on the function source code specified as the filename, handler,
name, artifact and version specified for the function image repository and tag.

For example, type:

    riff init python3 -i words -n uppercase --handler=process

to generate the resource definitions using sensible defaults.


```
riff init python3 [flags]
```

### Options

```
      --handler string           the name of the function handler (default "{{ .FunctionName }}")
  -h, --help                     help for python3
      --invoker-version string   the version of invoker to use when building containers (default "0.0.6-snapshot")
```

### Options inherited from parent commands

```
  -a, --artifact string      path to the function artifact, source code or jar file
      --config string        config file (default is $HOME/.riff.yaml)
      --dry-run              print generated function artifacts content to stdout only
  -f, --filepath string      path or directory used for the function resources (defaults to the current directory)
      --force                overwrite existing functions artifacts
  -i, --input string         the name of the input topic (defaults to function name)
  -n, --name string          the name of the function (defaults to the name of the current directory)
  -o, --output string        the name of the output topic (optional)
  -u, --useraccount string   the Docker user account to be used for the image repository (default "current OS user")
  -v, --version string       the version of the function image (default "0.0.1")
```

### SEE ALSO

* [riff init](https://github.com/projectriff/riff/blob/master/riff-cli/docs/riff_init.md)	 - Initialize a function

