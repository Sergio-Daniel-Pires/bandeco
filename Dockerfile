from python:3.11-slim

# Fix pt_BR locale
RUN apt-get update
RUN apt-get install -y locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/'        /etc/locale.gen \
 && sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen \
 && locale-gen

# Env dependencies
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright

WORKDIR /bandeco

# Install requirements
COPY requirements.txt whatsapp_bot-0.1.0-py3-none-any.whl ./

RUN pip install -r requirements.txt
RUN pip install whatsapp_bot-0.1.0-py3-none-any.whl

# Install playwright deps
RUN apt-get update
RUN apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils
RUN PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright python -m playwright install --with-deps chromium
