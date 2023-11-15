FROM python:3.8-slim

## Step 1:
# Create a working directory
WORKDIR /app

## Step 2:
# Copy source code to working directory
COPY api.py settings.py vars.env requirements.txt /app/
COPY templates /app/templates/

## Step 3:
# Install packages from requirements.txt
RUN pip install -r requirements.txt && \
    rm /app/requirements.txt

# RUN pip install -r requirements.txt -t lib && \
#     rm -R lib/MySQLdb

## Step 4:
# Expose port 8080
EXPOSE 8080

# Run app.py at container launch
CMD ["python", "api.py"]