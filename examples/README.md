# Examples

This directory contains example applications that demonstrate how to use the base image.

## Go Hello World

A simple Go application that demonstrates CGO compatibility with the glibc base image.

### Building

```bash
cd go-hello
docker build -t go-hello .
```

### Running

```bash
docker run --rm go-hello
```

Expected output:
```
Hello from <container-id>!
Running on linux/amd64
Built with Go go1.23.x
```

### Multi-arch build

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t go-hello:multi .
``` 