## riff create python3

Create a python3 function

### Synopsis

Create the function based on the function source code specified as the filename, handler,
name, artifact and version specified for the function image repository and tag.

For example, type:

    riff create python3 -i words -n uppercase --handler=process

to create the resource definitions, and apply the resources, using sensible defaults.


```
riff create python3 [flags]
```

### Options

```
      --handler string           the name of the function handler (default "{{ .FunctionName }}")
  -h, --help                     help for python3
      --invoker-version string   the version of invoker to use when building containers (default "0.0.6-snapshot")
      --namespace string         the namespace used for the deployed resources (defaults to kubectl's default)
      --push                     push the image to Docker registry
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

* [riff create](https://github.com/projectriff/riff/blob/master/riff-cli/docs/riff_create.md)	 - Create a function (equivalent to init, build, apply)

