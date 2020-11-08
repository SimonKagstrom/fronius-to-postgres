FROM fronius-base-os:latest

COPY ./fronius-to-postgres.py .

WORKDIR /root
CMD /fronius-to-postgres.py ${FRONIUS_IP} ${DATABASE_HOST} ${DATABASE_NAME} ${DATABASE_USER} ${DATABASE_PASS}
