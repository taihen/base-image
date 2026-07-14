# Distroless Base Images

<div align="center">
  <img src="docs/logo.png" alt="Base Image Logo" width="300">
</div>

This repository builds, updates, and secures multi-arch (currently only `x86_64` and `arm64`) **distroless Docker base images**. Three variants are published to GitHub Container Registry (GHCR) at `ghcr.io/taihen/base-image`:

- **Base image** (`:latest`) - Minimal distroless image with no libc, for statically-linked binaries
- **glibc image** (`:glibc`) - Includes GNU libc for better compatibility  
- **Debug image** (`:debug`) - Development variant with shell and debugging tools

All images are available with both convenience tags and version tags (e.g., `v2025.06.13`) for reproducible builds.

This project has been configured to use the Chainguard `apko` toolchain, which is the best-in-class method for building minimal, secure, and reproducible container images.

Curious about distroless, checkout my [blog post](https://taihen.org/posts/distroless/).

## Why You Need a Secure and Simple Base Image

Modern containerized applications face increasing security threats and compliance requirements. Traditional base images often include unnecessary packages, tools, and potential vulnerabilities that expand your attack surface. A secure and simple base image is essential because:

- **Reduced Attack Surface**: By including only the bare minimum required to run your application (CA certificates, timezone data, and optionally glibc), there are fewer components that could contain vulnerabilities
- **Compliance**: Many security standards and regulations require minimizing unnecessary software in production environments
- **Smaller Images**: Minimal images mean faster pulls, reduced storage costs, and quicker deployments
- **No Shell or Package Manager**: Without these tools, attackers have fewer options if they manage to breach your container
- **Immutable Infrastructure**: Distroless images encourage building immutable containers where everything is defined at build time
- **Supply Chain Security**: Using a well-maintained base image with automated security updates helps protect against supply chain attacks

## Build Process

Instead of `Dockerfile`s, this project uses declarative `apko` YAML files to define the image contents:

- **[`base.yaml`](./base.yaml)** - Base distroless image with minimal packages (ca-certificates, tzdata, wolfi-baselayout)
- **[`glibc.yaml`](./glibc.yaml)** - Extends base.yaml and adds the `glibc` package for compatibility
- **[`debug.yaml`](./debug.yaml)** - Extends glibc.yaml and adds debugging tools (`wolfi-base` with busybox and apk)

Each configuration specifies:
- The minimal set of packages required from the [Wolfi](https://github.com/wolfi-dev) repository
- A non-root user (`65532:65532`) for secure execution (except debug which runs as root)
- The target architectures (`linux/amd64`, `linux/arm64`)

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
  - A high-quality SBOM (Software Bill of Materials) is generated natively by `apko` during the build and attached to each image as a signed in-registry attestation (`cosign attest --type spdxjson`).
  - SLSA build provenance is attached to each image via GitHub artifact attestations.
- **Reproducible:** Package versions are pinned in committed `apko lock` files (`base.lock.json`, `glibc.lock.json`, `debug.lock.json`) and image timestamps derive from the commit date (`SOURCE_DATE_EPOCH`), so rebuilding the same commit yields the same image. A daily workflow opens a PR when Wolfi package versions move.
- **CI/CD:** A GitHub Actions workflow builds and publishes images under ephemeral run-scoped tags, tests and vulnerability-scans them, and only then signs, attests, and promotes the floating tags (`latest`, `glibc`, `debug`). An unscanned image is never reachable through a consumable tag.

## Image Variants

This repository provides three distinct image variants to meet different use cases:

### Base Image (`:latest`)
The default minimal distroless image. It ships no libc at all, making it the most minimal option, suitable for statically-linked binaries.

### glibc Image (`:glibc`)
Extends the base image with GNU libc for maximum compatibility with dynamically-linked applications that expect glibc. Recommended for most applications requiring C library compatibility.

### Debug Image (`:debug`)
While the production images are designed for production use without a shell or debugging tools, sometimes you need these capabilities during development or troubleshooting. The debug variant provides these tools.

### Debug Image Configuration

The debug image is defined in [`debug.yaml`](./debug.yaml) and extends the base configuration with:

- **`wolfi-base` package**: Adds busybox (providing common Unix utilities) and apk-tools (package manager)
- **Root user**: Runs as root instead of the non-root user (65532:65532)
- **Shell entrypoint**: Sets `/bin/sh -l` as the default entrypoint

### When to Use the Debug Image

⚠️ **Warning**: The debug image should **NEVER** be used in production as it significantly increases the attack surface by including a shell and running as root.

Use cases for the debug image:

- Local development and testing
- Debugging application issues in non-production environments
- Exploring the container filesystem
- Installing additional packages for testing
- Troubleshooting permission or dependency issues

### Available Image Tags

**Base Production Image (static, no libc):**
- `ghcr.io/taihen/base-image:latest` - Latest base image build
- `ghcr.io/taihen/base-image:v2025.06.13` - Specific version tag

**glibc Production Image (GNU libc):**
- `ghcr.io/taihen/base-image:glibc` - Latest glibc image build  
- `ghcr.io/taihen/base-image:v2025.06.13-glibc` - Specific version glibc tag

**Debug Development Image:**
- `ghcr.io/taihen/base-image:debug` - Latest debug build
- `ghcr.io/taihen/base-image:v2025.06.13-debug` - Specific version debug tag

### Building Images Locally

To build any variant using apko:

```sh
# Build base image (static, no libc)
docker run -v $PWD:/work cgr.dev/chainguard/apko build base.yaml base:test base.tar
docker load < base.tar

# Build glibc image  
docker run -v $PWD:/work cgr.dev/chainguard/apko build glibc.yaml glibc:test glibc.tar
docker load < glibc.tar

# Build debug image
docker run -v $PWD:/work cgr.dev/chainguard/apko build debug.yaml debug:test debug.tar
docker load < debug.tar

# Run the debug image interactively
docker run -it --rm debug:test
```

## What is apko and Wolfi?

### apko

[apko](https://github.com/chainguard-dev/apko) is a declarative tool for building container images using Alpine APK packages. Unlike traditional Dockerfiles that use imperative commands, apko uses a YAML configuration to define exactly what goes into an image. This approach:

- Produces minimal, reproducible images
- Generates SBOMs (Software Bill of Materials) automatically
- Eliminates unnecessary build artifacts and package managers
- Creates truly distroless images without shells or other debugging tools

### Wolfi

[Wolfi](https://github.com/wolfi-dev) is a Linux distribution designed specifically for containers, created by Chainguard. Key features:

- **glibc-based**: Unlike Alpine (which uses musl), Wolfi uses glibc for better compatibility
- **Security-focused**: Rapid CVE patching and minimal attack surface
- **Supply chain hardened**: All packages are signed and built with provenance
- **Container-native**: Designed from the ground up for containerized workloads
- **Daily updates**: Packages are rebuilt frequently to incorporate the latest security patches

Together, apko and Wolfi provide a secure foundation for building container images that meet range of requirements while maintaining minimal size and attack surface.

## How to Use

You can use these images as secure and minimal bases for your applications. Choose the appropriate variant based on your application's requirements:

- Use `:latest` for statically-linked binaries
- Use `:glibc` for applications that require GNU libc compatibility  
- Use `:debug` only for development and troubleshooting

### Example: Go Application (CGO-enabled, glibc)

```dockerfile
FROM golang:1.23 AS builder
WORKDIR /src
COPY main.go .
ARG TARGETARCH
ENV CGO_ENABLED=1 GOOS=linux GOARCH=$TARGETARCH
RUN go build -o /hello main.go

# Use glibc variant for CGO-enabled applications
FROM ghcr.io/taihen/base-image:glibc
# OR use a specific version for reproducible builds
# FROM ghcr.io/taihen/base-image:v2025.06.13-glibc
COPY --from=builder /hello /hello
USER 65532:65532
ENTRYPOINT ["/hello"]
```

### Example: Static Binary (no libc)

```dockerfile  
FROM golang:1.23-alpine AS builder
WORKDIR /src
COPY main.go .
ARG TARGETARCH
ENV CGO_ENABLED=0 GOOS=linux GOARCH=$TARGETARCH
RUN go build -ldflags="-s -w" -o /hello main.go

# Use base variant for static binaries
FROM ghcr.io/taihen/base-image:latest
COPY --from=builder /hello /hello
USER 65532:65532
ENTRYPOINT ["/hello"]
```

### Example: Java (custom JRE with jlink)

```dockerfile
FROM eclipse-temurin:17-jdk AS builder
WORKDIR /app
COPY Hello.java .
RUN javac Hello.java
RUN echo "Main-Class: Hello" > manifest.txt && jar cfm hello.jar manifest.txt Hello.class
RUN $JAVA_HOME/bin/jlink --add-modules java.base --strip-debug --no-man-pages --no-header-files --compress=2 --output /jre

# Use glibc variant for Java applications  
FROM ghcr.io/taihen/base-image:glibc
COPY --from=builder /jre /jre
COPY --from=builder /app/hello.jar /app/hello.jar
ENTRYPOINT ["/jre/bin/java", "-jar", "/app/hello.jar"]
```

### Using the Debug Image for Development

```dockerfile
# For development and debugging
FROM ghcr.io/taihen/base-image:debug

# You can install additional packages with apk
RUN apk add --no-cache curl jq

# Debug your application interactively
COPY my-app /usr/local/bin/
ENTRYPOINT ["/bin/sh"]  # or ["/usr/local/bin/my-app"]
```

**Quick debugging session:**

```bash
# Run the debug image interactively
docker run -it --rm ghcr.io/taihen/base-image:debug

# Inside the container, you have shell access and tools
/ # apk add --no-cache curl
/ # curl -s https://httpbin.org/json | jq
/ # ps aux
/ # ls -la /
```

## Local Testing

To build the image locally, you need Docker with BuildKit enabled.

1. **Enable BuildKit:**

    ```sh
    export DOCKER_BUILDKIT=1
    ```

2. **Build for multiple platforms:**

    ```sh
    docker buildx create --use
    docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/taihen/base-image:latest --push .
    ```

3. **Run the test suite:**

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

The [`.github/workflows/build.yml`](./.github/workflows/build.yml) workflow handles the entire build, test, sign, and publish process for all three image variants. It is triggered on:

- A `push` to the `main` branch.
- A daily schedule (`cron: "0 5 * * *"`) to ensure images are kept up-to-date with upstream packages.

The pipeline runs in stages so that no unscanned image is ever reachable through a consumable tag:

1. **build** - builds each variant with `apko` (constrained by the committed lockfiles) and publishes it under an ephemeral run-scoped tag (`build-<run_id>-<variant>`).
2. **test** - runs the Go smoke tests on both architectures and a Trivy vulnerability scan against the freshly built digests. Any failure stops the pipeline here.
3. **promote** - signs each digest with Cosign (keyless), attaches the SPDX SBOM as a signed attestation and SLSA build provenance, then moves the floating tags:
   - **Base images**: `latest` and version tags (e.g., `v2025.06.13`)
   - **glibc images**: `glibc` and version-glibc tags (e.g., `v2025.06.13-glibc`)
   - **Debug images**: `debug` and version-debug tags (e.g., `v2025.06.13-debug`)
4. **release** - creates a GitHub release with version tags when package contents changed.

The [`.github/workflows/update-locks.yml`](./.github/workflows/update-locks.yml) workflow regenerates the `apko lock` files daily and opens a PR when Wolfi package versions have moved, keeping builds reproducible while still tracking upstream security patches.

### Verifying Images

All artifacts are verifiable from the registry, without trusting this README:

```bash
IMAGE=ghcr.io/taihen/base-image:latest
IDENTITY=https://github.com/taihen/base-image/.github/workflows/build.yml@refs/heads/main
ISSUER=https://token.actions.githubusercontent.com

# Signature
cosign verify "$IMAGE" --certificate-identity="$IDENTITY" --certificate-oidc-issuer="$ISSUER"

# SBOM attestation (SPDX)
cosign verify-attestation "$IMAGE" --type spdxjson \
  --certificate-identity="$IDENTITY" --certificate-oidc-issuer="$ISSUER"

# SLSA build provenance
gh attestation verify "oci://$IMAGE" --repo taihen/base-image
```

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
   - **Detailed package changelog** showing what changed since the last release

### Package Change Tracking

The release system automatically compares the SBOMs from the current and previous releases to generate a detailed changelog that shows:

- **Added packages**: New packages introduced in this release
- **Updated packages**: Packages with version changes
- **Removed packages**: Packages that were removed
- **Summary statistics**: Total package counts and change counts for both images

If no package changes are detected (e.g., only metadata or rebuild changes), the release notes will indicate "No package changes detected (metadata or rebuild only)".

### Benefits

- **Meaningful Releases**: Only creates releases when there are actual changes
- **Transparent Changes**: Every release documents exactly what packages changed
- **Audit Trail**: Each release documents what changed and when
- **Resource Efficiency**: Avoids cluttering the releases page with identical builds
- **Supply Chain Security**: Every release includes verification instructions and SBOM

### Release Naming

Releases are automatically tagged with a date-based version format: `vYYYY.MM.DD` (e.g., `v2025.06.13`). If multiple releases occur on the same day, a counter is appended (e.g., `v2025.06.13.1`).

Each release creates:

- A GitHub release with the version tag
- A Docker image tagged with the same version (e.g., `ghcr.io/taihen/base-image:v2025.06.13`)
- The `latest` tag is also updated to point to the newest release

## Automated Testing

Before creating a release, the workflow runs comprehensive tests to ensure all three image variants work correctly:

### Test Suite

1. **Go Application Test**: Builds and runs a hello world Go application on all three image variants
   - Verifies glibc/static-binary compatibility as appropriate
   - Tests both `linux/amd64` and `linux/arm64` architectures
   - Confirms correct user execution (UID 65532 for production variants, UID 0 for debug)
   - Validates environment variable handling

2. **Multi-Platform Build Test**: Ensures all images work correctly in multi-architecture builds

3. **Security Scan**: Runs Trivy to scan all image variants for vulnerabilities and reports any critical or high-severity issues

### Test Failure Handling

If any test fails:

- The workflow stops immediately
- No release is created
- The build artifacts remain available for debugging
- The next scheduled run will retry if the issues are resolved

This ensures that only fully functional and tested images are released.

## Projects using it

- [MCP RIPEStat](https://github.com/taihen/mcp-ripestat)
