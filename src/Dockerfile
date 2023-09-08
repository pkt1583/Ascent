FROM python:3.10 as base
WORKDIR /code

FROM base as dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# ---- Copy Files/Build ----
FROM dependencies AS build  
WORKDIR /code
COPY . .


FROM build as test
RUN python -m pylint app --output-format=parseable --output=pylint.log --fail-under=1
RUN python -m pytest --cov-report xml --cov=app app/tests/ --junit-xml unit_tests.xml


FROM python:3.10 AS release
WORKDIR /code
COPY --from=dependencies /code/requirements.txt ./
# Install app dependencies
RUN pip install -r requirements.txt
COPY --from=build /code/ ./
EXPOSE 3100
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "3100", "--proxy-headers"]