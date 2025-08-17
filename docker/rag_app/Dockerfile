FROM python:3.9

ARG APP_ENV
ENV APP_ENV=$APP_ENV

# Set the working directory inside the container
WORKDIR /app
# Copy the requirements file first (leveraging Docker cache)
COPY docker/rag_app/entrypoint_app.sh .
RUN chmod +x entrypoint_app.sh
COPY requirements.txt .
COPY $APP_ENV .
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Copy the application source code
COPY src /app/src
# Default command (adjust if needed)
#CMD ["sleep", "infinity"]
ENTRYPOINT ["/app/entrypoint_app.sh"]