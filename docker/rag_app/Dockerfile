FROM python:3.9


# Set the working directory inside the container
WORKDIR /app
# Copy the requirements file first (leveraging Docker cache)
COPY ../../requirements.txt .
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Copy the application source code
COPY ../../src/* /app
# Default command (adjust if needed)
#CMD ["sleep", "infinity"]
CMD ["python", "main.py"]