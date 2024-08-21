from python:3.12-slim

WORKDIR /whatsapp-bot-gateway

# FIXME need to install from pypi when updated
# Install requirements
COPY pyproject.toml python_whatsapp_wrapper-0.0.12-py3-none-any.whl ./

RUN pip install .[gateway]
RUN pip install python_whatsapp_wrapper-0.0.12-py3-none-any.whl
