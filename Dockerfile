FROM python:3

WORKDIR /usr/src/app

COPY app.py requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python"]

CMD ["app.py"]