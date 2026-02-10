FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY main.go .
RUN go mod init auth-bypass && \
    CGO_ENABLED=0 GOOS=linux go build -o auth-bypass main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/auth-bypass .
EXPOSE 8080
CMD ["./auth-bypass"]