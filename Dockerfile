FROM python:2.7-slim-jessie

RUN mkdir /app /app/var /app/var/run
RUN mkdir /app/var/edrpou \
    && curl -s http://ed.org.ua/edrpou/latest/uo_uniq.db.gz > /app/var/edrpou/uo_uniq.db.gz \
    && gzip -fd /app/var/edrpou/uo_uniq.db.gz \
    && mv /app/var/edrpou/uo_uniq.db /app/var/edrpou/edrpou.db \
    && chmod 0444 /app/var/edrpou/edrpou.db
COPY requirements.txt /app/
WORKDIR /app

RUN easy_install distribute
RUN pip install setuptools==33.1.1

RUN pip install -r requirements.txt
COPY . /app/
RUN pip install .

EXPOSE 80
CMD ["gunicorn", "-c", "/app/etc/gunicorn.conf", "--paste", "/app/etc/search.ini"]
