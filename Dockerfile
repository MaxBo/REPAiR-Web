FROM circleci/python:3.6.2-stretch-browsers

ENV CIRCLECIPATH $PATH

USER root

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
 
RUN apt-get update --fix-missing && apt-get install -y wget bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    git mercurial subversion 
    
RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-4.3.27-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh 
    
RUN apt-get install -y curl grep sed dpkg && \
    TINI_VERSION=`curl https://github.com/krallin/tini/releases/latest | grep -o "/v.*\"" | sed 's:^..\(.*\).$:\1:'` && \
    curl -L "https://github.com/krallin/tini/releases/download/v${TINI_VERSION}/tini_${TINI_VERSION}.deb" > tini.deb && \
    dpkg -i tini.deb && \
    rm tini.deb && \
    apt-get clean 

RUN chown -R circleci /opt/conda

USER circleci

ENV PATH /opt/conda/bin:$CIRCLECIPATH
RUN echo $PATH
RUN conda create -y -n repair python=3.6
ENV PATH /opt/conda/envs/repair:/opt/conda/envs/repair/Scripts:$PATH

RUN conda install -y -c conda-forge gdal=2.1
