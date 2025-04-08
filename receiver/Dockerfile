FROM python:3

LABEL maintainer="maksymzhos@proton.me"

# Create app directory
RUN mkdir -p /app

# Copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

# Set the working directory
WORKDIR /app

# Install dependencies
RUN pip3 install -r requirements.txt

# Copy the source code
COPY . /app

# Change permissions and become a non-privileged user
RUN chown -R nobody:nogroup /app
USER nobody

# Tells on which port the service listens in the container
EXPOSE 8080

# Entrypoint = run Python
ENTRYPOINT ["python3"]

# Default = run app.py
CMD ["app.py"]
