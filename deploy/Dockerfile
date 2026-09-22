FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY apps ./apps
COPY examples ./examples
ENV CREATOR_ROOT=/app CREATOR_DATA=/data
VOLUME /data
EXPOSE 8890
CMD ["creator-network", "serve", "--host", "0.0.0.0", "--external-worker"]
