from debian:latest as builder

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
		autoconf \
		automake \
		bison \
		build-essential \
		git \
		libbz2-dev \
		libcurl4-openssl-dev \
		libltdl-dev \
		libtool \
		pkg-config \
		python3-pip \
		python3-setuptools \
		python3-wheel \
		python-dev \
		re2c \
		scons \
		wget \
	&& rm -rf /var/lib/apt/lists/*

# Based on https://github.com/hexhex/core/blob/master/scripts/build-linux.sh

ARG BOOST_VERSION="1.59.0"
ARG BUILD_DIR=/root/build
ARG LIB_DIR=$BUILD_DIR/out

WORKDIR $BUILD_DIR

RUN wget -O boost.tar.gz https://sourceforge.net/projects/boost/files/boost/$BOOST_VERSION/boost_$(echo $BOOST_VERSION | tr . _).tar.gz \
	&& mkdir boost \
	&& tar xzC boost --strip-components=1 -f boost.tar.gz \
	&& rm boost.tar.gz \
	&& cd boost \
	&& ./bootstrap.sh --prefix=$LIB_DIR \
	&& ./b2 -q cxxflags=-fPIC link=static runtime-link=static install

RUN git clone --recursive https://github.com/hexhex/core.git dlvhex \
	&& cd dlvhex \
	&& ./bootstrap.sh \
	&& ./configure --prefix $LIB_DIR \
		CXXFLAGS=-fPIC \
		PKG_CONFIG_PATH=$LIB_DIR/lib/pkgconfig \
		--enable-release \
		--enable-shared=no \
		--enable-static-boost \
		--with-boost=$LIB_DIR \
		--with-included-ltdl \
	&& make && make install

RUN git clone --recursive https://github.com/hexhex/nestedhexplugin.git \
	&& cd nestedhexplugin \
	&& ./bootstrap.sh \
	&& ./configure --prefix $LIB_DIR PKG_CONFIG_PATH=$LIB_DIR/lib/pkgconfig --with-boost=$LIB_DIR \
	&& make && make install

RUN wget -O clingo.tar.gz https://github.com/potassco/clingo/releases/download/v5.2.2/clingo-5.2.2-linux-x86_64.tar.gz \
	&& mkdir clingo \
	&& tar xzC clingo --strip-components=1 -f clingo.tar.gz \
	&& rm clingo.tar.gz \
	&& cd clingo \
	&& cp -a clasp clingo gringo lpconvert reify $LIB_DIR/bin

WORKDIR $LIB_DIR/wheels

RUN pip3 wheel git+https://github.com/hexhex/ehex.git

from debian:latest

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8
ARG LIB_DIR=/root/build/out


COPY --from=builder $LIB_DIR/bin/* /usr/local/bin/
COPY --from=builder $LIB_DIR/wheels /tmp/wheels

RUN apt-get update && apt-get install -y --no-install-recommends \
	libcurl3 \
	python3-pip \
	vim \
	&& rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-index --find-links=/tmp/wheels ehex

COPY --from=builder $LIB_DIR/lib/dlvhex2/plugins /root/.dlvhex2/plugins
COPY examples /examples
WORKDIR /examples
