FROM golang:1.17-alpine AS build
WORKDIR /src
COPY src/main.go src/go.mod /src/
RUN CGO_ENABLED=0 go build -o sample ./main.go

FROM gcr.io/distroless/static AS final
USER nonroot:nonroot
LABEL MAINTAINER="sjbodzo"
COPY --from=build /src/sample /app
ENTRYPOINT ["/app"]
