FROM python:3.6
WORKDIR /usr/src/app
COPY . .
RUN pip install pipenv && \
    pipenv install --system --deploy 
CMD ["python", "service.py"]
