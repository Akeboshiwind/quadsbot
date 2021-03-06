FROM alpine as builder

# Install build deps
RUN apk add --no-cache \
    'cargo' \
    'openssl-dev'

# Build app
WORKDIR /usr/src/myapp
COPY . .
RUN cargo build --release


FROM alpine

# Install runtime deps
RUN apk add --no-cache \
    'openssl-dev' \
    'libgcc' \
    'tzdata'

# Set timezone to BST
ENV TZ Europe/London

# Copy binary
COPY --from=builder /usr/src/myapp/target/release/quadsbot /quadsbot

CMD ["/quadsbot"]
