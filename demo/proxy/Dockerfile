FROM nginx

ARG DOMAIN

ADD default.conf /etc/nginx/conf.d/default.conf
ADD run.sh /run.sh

RUN sed -i "s/DOMAIN/${DOMAIN}/g" /etc/nginx/conf.d/default.conf

CMD ["/run.sh"]
