FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /src
COPY Main.java .
RUN javac Main.java

# Extract a minimal JRE using jlink
RUN jlink \
    --add-modules java.base,java.logging \
    --strip-debug \
    --no-man-pages \
    --no-header-files \
    --compress=2 \
    --output /javaruntime

FROM ghcr.io/taihen/base-image:latest
# Copy the minimal JRE from the builder
COPY --from=builder /javaruntime /opt/java
# Copy the compiled class
COPY --from=builder /src/Main.class /app/Main.class
WORKDIR /app
USER 65532:65532
ENTRYPOINT ["/opt/java/bin/java", "Main"]