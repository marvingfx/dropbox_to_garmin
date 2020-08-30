FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt app.py  ./

COPY /db ./db

COPY /templates ./templates

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python"]

CMD ["app.py"]