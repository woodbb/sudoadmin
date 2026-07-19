# To build:
# docker build --tag harbor.example.com/lsudo/sudoadmin:latest \
#   --build-arg https_proxy=http://10.0.0.250:80 \
#   --build-arg http_proxy=http://10.0.0.250:80 .

FROM registry.access.redhat.com/ubi10/ubi

ENV TZ=America/Chicago
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

RUN dnf clean all && \
    dnf update -y && \
    dnf install -y python3 python3-pip python3-devel openldap-clients openldap-devel gcc && \
    dnf clean all

# ADD certificates/root/* /etc/pki/ca-trust/source/anchors/
# RUN update-ca-trust

ADD application/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app
COPY application/ /app

WORKDIR /app
EXPOSE 8000
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
