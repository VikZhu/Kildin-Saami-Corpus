FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP myapp.py

EXPOSE 5000

CMD ["python3", "myapp.py", "--host", "0.0.0.0", "-p", "5000"]

