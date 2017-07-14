FROM kbase/kbase:sdkbase.latest
MAINTAINER William Riehl
ENV JBROWSE_TAG 1.12.3-release
ENV SAMTOOLS_VER 1.4.1
# -----------------------------------------

WORKDIR /kb/module

RUN pip install coverage

# update security libraries in the base image
RUN pip install cffi --upgrade \
    && pip install pyopenssl --upgrade \
    && pip install ndg-httpsclient --upgrade \
    && pip install pyasn1 --upgrade \
    && pip install requests --upgrade \
    && pip install 'requests[security]' --upgrade

# Install JBrowse
RUN git clone https://github.com/GMOD/jbrowse -b $JBROWSE_TAG && \
    cd jbrowse && \
    ./setup.sh

# Install Samtools
RUN cd /opt \
    && wget https://github.com/samtools/samtools/releases/download/$SAMTOOLS_VER/samtools-$SAMTOOLS_VER.tar.bz2 \
    && tar xvjf samtools-$SAMTOOLS_VER.tar.bz2 \
    && rm -f samtools-$SAMTOOLS_VER.tar.bz2 \
    && cd samtools-$SAMTOOLS_VER \
    && ./configure \
    && make \
    && make install

ENV PATH $PATH:/opt/samtools-$SAMTOOLS_VER


# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
