FROM python:3.12-slim AS builder
WORKDIR /src
COPY main.py .
# Install PyInstaller
RUN pip install --no-cache-dir pyinstaller
# Create a standalone executable
RUN pyinstaller --onefile --name hello main.py

FROM ghcr.io/taihen/base-image:latest
COPY --from=builder /src/dist/hello /hello
USER 65532:65532
ENTRYPOINT ["/hello"] 