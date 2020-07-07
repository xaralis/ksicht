FROM python:3.7-alpine3.11 as build

ENV PYTHONUNBUFFERED 1

# Install dependencies
RUN apk add --no-cache \
    nodejs \
    nodejs-npm  \
    bash \
    git \
    openssh \
    postgresql-dev \
    jpeg-dev \
    zlib-dev \
    build-base && \
    mkdir -p /build/wheels

# Install python requirements, collect as wheels and re-install
# later on in the `production` stage
COPY ./requirements.txt /build/wheels/
WORKDIR /build/wheels
RUN pip install -U pip && \
    pip wheel -r requirements.txt

# Install node-based requirements
WORKDIR /build
COPY ./package.json ./
RUN npm install

# Copy assets and build static file bundles
COPY ./webpack.config.js ./
COPY ./assets/ ./assets/
RUN ./node_modules/.bin/webpack --config webpack.config.js --mode production


FROM python:3.7-alpine3.11 as production

ENV PYTHONPATH /ksicht
ENV DJANGO_SETTINGS_MODULE ksicht.settings
ENV PATH "/home/ksicht/.local/bin:${PATH}"

# Create custom user to avoid running as a root
RUN addgroup -g 990 ksicht && \
    adduser -D -u 994 -G ksicht ksicht && \
    mkdir /ksicht && \
    chown ksicht:ksicht /ksicht

# Install dependencies
RUN apk add --no-cache \
    bash \
    git \
    postgresql-dev \
    build-base \
    jpeg-dev \
    zlib-dev \
    nginx \
    supervisor && \
    rm /etc/nginx/conf.d/default.conf && \
    echo "daemon off;" >> /etc/nginx/nginx.conf && \
    mkdir /run/nginx

# Supervisor and Nginx configs
COPY ./docker/supervisor.conf /etc/supervisor/conf.d/supervisor.conf
COPY ./docker/nginx.conf /etc/nginx/conf.d/ksicht.conf

# Copy over collected wheels and build artifacts from build stage
COPY --from=build --chown=ksicht /build/wheels /wheels
COPY --from=build --chown=ksicht /build/assets /ksicht/assets
COPY --from=build --chown=ksicht /build/webpack-stats.json /ksicht/

# Copy over entrypoint file
COPY --chown=ksicht docker/entrypoint.sh /ksicht/

# Prepare media directory
RUN mkdir -p /media && chown ksicht:ksicht /media

USER ksicht
WORKDIR /ksicht

# Install wheels under user priviledges
RUN pip install -r /wheels/requirements.txt -f /wheels --user

# Rest of source files
COPY --chown=ksicht ./ksicht ./ksicht/
COPY --chown=ksicht ./fonts ./fonts/
COPY --chown=ksicht ./fixtures ./fixtures/

# Collect static files
RUN mkdir /ksicht/static && \
    SECRET_KEY=x DEBUG=1 django-admin collectstatic --noinput --verbosity=0

USER root

# Get rid of useless files
RUN rm -rf /wheels && \
    rm -rf /home/ksicht/.cache/pip

EXPOSE 80

CMD ["sh", "./entrypoint.sh"]
