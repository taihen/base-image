# Multi-Arch Distroless glibc Base Image

This repository builds, updates, and secures a multi-arch (`x86_64` + `arm64`) distroless `glibc` Docker base image. The image is published to GitHub Container Registry (GHCR) at `ghcr.io/taihen/base-image`.

This project has been configured to use the Chainguard `apko` toolchain, which is the best-in-class method for building minimal, secure, and reproducible container images.

## Build Process

Instead of a `Dockerfile`, this project uses a declarative [`apko.yaml`](./apko.yaml) file to define the image contents. This file specifies:
- The minimal set of packages required from the [Wolfi](https://github.com/wolfi-dev) repository (`glibc`, `ca-certificates`, etc.).
- A non-root user (`65532:65532`) for secure execution.
- The target architectures (`linux/amd64`, `linux/arm64`).

This declarative approach, inspired by Google Distroless and perfected by Chainguard, ensures the resulting image contains only what is explicitly defined, drastically reducing the attack surface.

## Features

- **Declarative & Reproducible:** The `apko.yaml` file provides a clear, auditable, and reproducible definition of the image.
- **Multi-Arch:** Natively builds and pushes a multi-arch manifest for `linux/amd64` and `linux/arm64`.
- **Minimal & Secure:**
  - Built from trusted, minimal [Wolfi](https://github.com/wolfi-dev) packages.
  - Contains no shell, package manager, or other unnecessary components.
  - Runs as a non-root user (`65532:65532`).
  - Automatically rebuilt daily to incorporate the latest security patches from upstream packages.
  - Images are signed with Cosign using keyless signing.
  - A high-quality SBOM (Software Bill of Materials) is generated natively by `apko` during the build.
- **CI/CD:** A streamlined GitHub Actions workflow using [`wolfi-act`](https://github.com/wolfi-dev/wolfi-act) handles the entire build, publish, and sign process in a single, efficient step.

This approach aligns with NIS2 and SOC2 best practices for supply chain security, minimal images, non-root execution, and continuous patching.

## How to Use

You can use this image as a secure and minimal base for your applications.

### Example: Go (CGO-enabled)

```dockerfile
FROM golang:1.23 as builder
WORKDIR /src
COPY main.go .
ARG TARGETARCH
ENV CGO_ENABLED=1 GOOS=linux GOARCH=$TARGETARCH
RUN go build -o /hello main.go

FROM ghcr.io/taihen/base-image:latest
COPY --from=builder /hello /hello
USER 65532:65532
ENTRYPOINT ["/hello"]
```

### Example: Java (custom JRE with jlink)

```dockerfile
FROM eclipse-temurin:17-jdk as builder
WORKDIR /app
COPY Hello.java .
RUN javac Hello.java
RUN echo "Main-Class: Hello" > manifest.txt && jar cfm hello.jar manifest.txt Hello.class
RUN $JAVA_HOME/bin/jlink --add-modules java.base --strip-debug --no-man-pages --no-header-files --compress=2 --output /jre

FROM ghcr.io/taihen/base-image:latest
COPY --from=builder /jre /jre
COPY --from=builder /app/hello.jar /app/hello.jar
ENTRYPOINT ["/jre/bin/java", "-jar", "/app/hello.jar"]
```

## Local Testing

To build the image locally, you need Docker with BuildKit enabled.

1.  **Enable BuildKit:**
    ```sh
    export DOCKER_BUILDKIT=1
    ```

2.  **Build for multiple platforms:**
    ```sh
    docker buildx create --use
    docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/taihen/base-image:latest --push .
    ```

3.  **Run the test suite:**
    ```sh
    # Test the latest published image
    ./test/test-image.sh
    
    # Test a specific image
    ./test/test-image.sh ghcr.io/taihen/base-image:latest
    ```

    The test script will:
    - Build and run a Go hello world application using the base image
    - Verify the non-root user configuration
    - Run a security scan with Trivy
    - Report any issues found

## Automation

The [`.github/workflows/build.yml`](./.github/workflows/build.yml) workflow handles the entire build, push, and sign process. It is triggered on:

-   A `push` to the `main` branch.
-   A daily schedule (`cron: "0 5 * * *"`) to ensure the image is kept up-to-date with upstream packages.

## Automatic Release System

This repository includes an intelligent automatic release system that creates GitHub releases only when there are actual changes in the built image. This prevents unnecessary releases when the daily cron job runs but no packages have been updated.

### How it Works

1. **Digest Comparison**: After each build, the workflow captures the image digest (a unique identifier based on the image's content).
2. **Change Detection**: The digest is compared with the previous build's digest stored as a GitHub artifact.
3. **Conditional Release**: A new GitHub release is created only if:
   - No previous digest exists (first run)
   - The current digest differs from the previous one (indicating changes)
4. **Release Contents**: Each release includes:
   - The image digest for verification
   - The SBOM (Software Bill of Materials) as an attachment
   - Instructions for verifying the image signature

### Benefits

- **Meaningful Releases**: Only creates releases when there are actual changes
- **Audit Trail**: Each release documents what changed and when
- **Resource Efficiency**: Avoids cluttering the releases page with identical builds
- **Supply Chain Security**: Every release includes verification instructions and SBOM

### Release Naming

Releases are automatically tagged with a date-based version format: `vYYYY.MM.DD` (e.g., `v2024.01.15`). If multiple releases occur on the same day, a counter is appended (e.g., `v2024.01.15.1`).

## Automated Testing

Before creating a release, the workflow runs comprehensive tests to ensure the base image works correctly:

### Test Suite

1. **Go Application Test**: Builds and runs a hello world Go application on the base image
   - Verifies CGO compatibility (glibc linkage)
   - Tests both `linux/amd64` and `linux/arm64` architectures
   - Confirms non-root user execution (UID/GID 65532)
   - Validates environment variable handling

2. **Multi-Platform Build Test**: Ensures the image works correctly in multi-architecture builds

3. **Security Scan**: Runs Trivy to scan for vulnerabilities and reports any critical or high-severity issues

### Test Failure Handling

If any test fails:
- The workflow stops immediately
- No release is created
- The build artifacts remain available for debugging
- The next scheduled run will retry if the issues are resolved

This ensures that only fully functional and tested images are released.
