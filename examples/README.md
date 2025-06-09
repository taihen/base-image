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

## Java Hello World

A Java application using OpenJDK with a minimal JRE created by jlink for a smaller footprint in a distroless environment.

### Building

```bash
cd java-hello
docker build -t java-hello .
```

### Running

```bash
docker run --rm java-hello
```

Expected output:
```
Hello from <container-id>!
Running on Linux/amd64
Built with Java 21.x.x
```

### Multi-arch build

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t java-hello:multi .
```

## Python Hello World

A Python application bundled as a standalone executable using PyInstaller for distroless compatibility.

### Building

```bash
cd python-hello
docker build -t python-hello .
```

### Running

```bash
docker run --rm python-hello
```

Expected output:
```
Hello from <container-id>!
Running on Linux/x86_64
Built with Python 3.12.x
```

### Multi-arch build

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t python-hello:multi .
```

## Rust Hello World

A Rust application statically linked with musl for maximum portability in a distroless environment.

### Building

```bash
cd rust-hello
docker build -t rust-hello .
```

### Running

```bash
docker run --rm rust-hello
```

Expected output:
```
Hello from <container-id>!
Running on linux/x86_64
Built with Rust 1.75
```

### Multi-arch build

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t rust-hello:multi .
```

## Notes

All examples:
- Use multi-stage builds to minimize the final image size
- Run as non-root user (UID 65532)
- Support multi-architecture builds (linux/amd64 and linux/arm64)
- Produce standalone executables that work in the distroless environment 