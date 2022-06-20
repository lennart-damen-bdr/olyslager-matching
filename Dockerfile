FROM python:3.7.5
WORKDIR /usr/src

ADD setup.py .
ADD README.md .
ADD oly_matching ./oly_matching

RUN pip install --upgrade pip &&\
    pip install wheel &&\
    pip install --no-cache-dir .

CMD olyslager match