#!/bin/sh

cd "$(dirname $0)"

echo Building Docker container...

docker build \
    --build-arg https_proxy=$https_proxy \
    --build-arg http_proxy=$http_proxy \
    --rm=false \
    -t quizbot \
    .
