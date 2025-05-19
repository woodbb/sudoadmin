FROM python:latest
ENV TZ=America/Chicago
ENV DEBIAN_FRONTEND=noninteractive

RUN apt autoremove
RUN apt autoclean -y

RUN apt-get update
# RUN apt install software-properties-common -y
# RUN apt-get install python3-pip libsasl2-dev python3-dev libldap2-dev libssl-dev libnss-ldap libpam-ldap -y
RUN apt-get install python3-pip libsasl2-dev python-dev-is-python3 libldap2-dev libssl-dev libnss-ldap libpam-ldap -y

RUN apt-get upgrade -y
ENV PYTHONUNBUFFERED=1

RUN pip install git+https://github.com/jcrist/msgspec.git@main
ADD application/requirements.txt .
RUN pip install -r requirements.txt

USER root
RUN mkdir -p /app
COPY application/ /app

WORKDIR /app

CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
EXPOSE 8000
