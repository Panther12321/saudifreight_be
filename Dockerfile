ARG FRAPPE_IMAGE=frappe/erpnext:v15
FROM ${FRAPPE_IMAGE}

USER root
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends nginx \
  && rm -rf /var/lib/apt/lists/*
COPY --chown=frappe:frappe naqil /home/frappe/frappe-bench/apps/naqil
COPY --chown=frappe:frappe docker/boot.sh /usr/local/bin/naqil-boot
COPY --chown=frappe:frappe docker/migrate.sh /usr/local/bin/naqil-migrate
RUN chmod 0755 /usr/local/bin/naqil-boot /usr/local/bin/naqil-migrate

USER frappe
WORKDIR /home/frappe/frappe-bench
ENV PYTHONPATH="/home/frappe/frappe-bench/apps/naqil:${PYTHONPATH}"

# The Frappe image already provides framework dependencies. --no-deps avoids
# replacing the framework package while registering this custom application.
RUN pip install --no-deps --editable apps/naqil \
  && python -c "import naqil; print(naqil.__file__)" \
  && test -x /home/frappe/frappe-bench/env/bin/gunicorn

USER root
ENTRYPOINT ["/usr/local/bin/naqil-boot"]
CMD ["combined"]
