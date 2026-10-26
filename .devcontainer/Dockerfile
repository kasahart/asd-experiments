# syntax=docker/dockerfile:1
# Python 3.11 as in README.md "実行環境" and the CI workflow.
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# Audio decoding used by soundfile/torchaudio/librosa. The base image's yarn
# source has an expired key and would fail apt-get update; yarn is not used.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*
