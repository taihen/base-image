#!/bin/bash
# Test script for the base image
# Usage: ./test-image.sh [image-name]

set -e

IMAGE="${1:-ghcr.io/taihen/base-image:latest}"
TEMP_DIR=$(mktemp -d)

echo "Testing image: $IMAGE"
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
    fmt.Printf("Hello from base-image test!\n")
    fmt.Printf("OS: %s\n", runtime.GOOS)
    fmt.Printf("Arch: %s\n", runtime.GOARCH)
    fmt.Printf("Go version: %s\n", runtime.Version())
    fmt.Printf("User: %d\n", os.Getuid())
    fmt.Printf("Group: %d\n", os.Getgid())
    
    // Test that we can read environment variables
    if testVar := os.Getenv("TEST_VAR"); testVar != "" {
        fmt.Printf("TEST_VAR: %s\n", testVar)
    }
    
    // Test that we're running as non-root (65532)
    if os.Getuid() != 65532 {
        fmt.Printf("ERROR: Expected UID 65532, got %d\n", os.Getuid())
        os.Exit(1)
    }
    
    fmt.Println("All tests passed!")
}
EOF

# Create Dockerfile
cat > "$TEMP_DIR/Dockerfile" << EOF
# Build stage
FROM golang:1.24-alpine as builder
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

# Build and test
cd "$TEMP_DIR"

echo ""
echo "Building test application..."
docker build -t base-image-test:latest .

echo ""
echo "Running test application..."
docker run --rm -e TEST_VAR="Hello from test" base-image-test:latest

echo ""
echo "Running security scan with Trivy..."
docker run --rm aquasecurity/trivy:latest image --severity HIGH,CRITICAL "$IMAGE" || true

# Cleanup
cd - > /dev/null
rm -rf "$TEMP_DIR"
docker rmi base-image-test:latest > /dev/null 2>&1 || true

echo ""
echo "✅ All tests completed!" 