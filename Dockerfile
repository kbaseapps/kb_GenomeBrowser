FROM kbase/kbase:sdkbase.latest
MAINTAINER William Riehl
ENV JBROWSE_TAG 1.12.3-release
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

RUN git clone https://github.com/GMOD/jbrowse -b $JBROWSE_TAG && \
    cd jbrowse && \
    ./setup.sh

# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
