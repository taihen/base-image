#!/bin/bash
# Test script for the base images
# Usage: ./test-image.sh [image-name] [variant]
# Examples:
#   ./test-image.sh                                    # Test latest (base)
#   ./test-image.sh ghcr.io/taihen/base-image:glibc   # Test glibc variant
#   ./test-image.sh ghcr.io/taihen/base-image:debug   # Test debug variant

set -e

IMAGE="${1:-ghcr.io/taihen/base-image:latest}"
VARIANT="${2:-base}"

# Auto-detect variant from image name if not provided
if [[ "$IMAGE" == *":glibc"* ]]; then
    VARIANT="glibc"
elif [[ "$IMAGE" == *":debug"* ]]; then  
    VARIANT="debug"
elif [[ "$IMAGE" == *":latest"* ]] || [[ "$IMAGE" != *":"* ]]; then
    VARIANT="base"
fi

TEMP_DIR=$(mktemp -d)

echo "Testing image: $IMAGE (variant: $VARIANT)"
echo "Working directory: $TEMP_DIR"

# Create test Go application
cat > "$TEMP_DIR/main.go" << 'EOF'
package main

import (
    "fmt"
    "os"
    "runtime"
)

func main() {
    variant := os.Getenv("IMAGE_VARIANT")
    fmt.Printf("Hello from base-image test (%s variant)!\n", variant)
    fmt.Printf("OS: %s\n", runtime.GOOS)
    fmt.Printf("Arch: %s\n", runtime.GOARCH)
    fmt.Printf("Go version: %s\n", runtime.Version())
    fmt.Printf("User: %d\n", os.Getuid())
    fmt.Printf("Group: %d\n", os.Getgid())
    
    // Test that we can read environment variables
    if testVar := os.Getenv("TEST_VAR"); testVar != "" {
        fmt.Printf("TEST_VAR: %s\n", testVar)
    }
    
    // Test user based on variant
    expectedUID := 65532 // default for base/glibc
    if variant == "debug" {
        expectedUID = 0 // root for debug
    }
    
    if os.Getuid() != expectedUID {
        fmt.Printf("ERROR: Expected UID %d for %s variant, got %d\n", expectedUID, variant, os.Getuid())
        os.Exit(1)
    }
    
    fmt.Println("All tests passed!")
}
EOF

# Create Dockerfile based on variant
if [ "$VARIANT" = "debug" ]; then
    # Debug image runs as root and doesn't need USER directive
    cat > "$TEMP_DIR/Dockerfile" << EOF
# Build stage
FROM golang:1.23-alpine AS builder
WORKDIR /build
COPY main.go .
ARG TARGETARCH
RUN CGO_ENABLED=1 go build -ldflags="-s -w" -o hello main.go

# Runtime stage using debug image (already runs as root)
FROM $IMAGE
COPY --from=builder /build/hello /hello
ENTRYPOINT ["/hello"]
EOF
else
    # Base and glibc images run as non-root user
    cat > "$TEMP_DIR/Dockerfile" << EOF
# Build stage
FROM golang:1.23-alpine AS builder
WORKDIR /build
COPY main.go .
ARG TARGETARCH
RUN CGO_ENABLED=1 go build -ldflags="-s -w" -o hello main.go

# Runtime stage using our base image
FROM $IMAGE
COPY --from=builder /build/hello /hello
USER 65532:65532
ENTRYPOINT ["/hello"]
EOF
fi

# Build and test
cd "$TEMP_DIR"

echo ""
echo "Building test application..."
docker build -t base-image-test:latest .

echo ""
echo "Running test application..."
docker run --rm \
    -e TEST_VAR="Hello from $VARIANT test" \
    -e IMAGE_VARIANT="$VARIANT" \
    base-image-test:latest

echo ""
echo "Running security scan with Trivy..."
docker run --rm aquasecurity/trivy:latest image --severity HIGH,CRITICAL "$IMAGE" || true

# Cleanup
cd - > /dev/null
rm -rf "$TEMP_DIR"
docker rmi base-image-test:latest > /dev/null 2>&1 || true

echo ""
echo "✅ All tests completed!" 