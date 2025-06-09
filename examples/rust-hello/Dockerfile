FROM rust:1.75 AS builder
WORKDIR /src
# Install musl-dev for static linking
RUN apk add --no-cache musl-dev
# Copy the source files
COPY Cargo.toml main.rs ./
# Build the binary with static linking based on target architecture
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then \
    rustup target add aarch64-unknown-linux-musl && \
    cargo build --release --target aarch64-unknown-linux-musl; \
    else \
    cargo build --release --target x86_64-unknown-linux-musl; \
    fi

FROM ghcr.io/taihen/base-image:latest
ARG TARGETARCH
COPY --from=builder /src/target/*/release/hello /hello
USER 65532:65532
ENTRYPOINT ["/hello"] 