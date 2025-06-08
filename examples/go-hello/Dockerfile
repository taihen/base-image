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