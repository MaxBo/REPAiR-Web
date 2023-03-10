FROM osgeo/gdal:ubuntu-small-latest
RUN curl -sL https://deb.nodesource.com/setup_14.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get -y install git \
    && apt-get -y install nodejs \
    && apt-get -y install python3-pip \
    && apt-get -y install libpq-dev \
    && apt-get -y install binutils libproj-dev libgeos-dev \
    && apt-get -y install osmium-tool \
    && apt-get -y install language-pack-de wget \
    && apt-get -y install libxcursor1 libgtk-3-0 \
    && apt-get install -y libpq-dev \
    && apt-get install -y gettext imagemagick ghostscript

RUN mkdir /root/miniconda3
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /root/miniconda3/miniconda.sh
RUN bash /root/miniconda3/miniconda.sh -b -u -p /root/miniconda3
RUN /root/miniconda3/bin/conda create -n repair -c conda-forge graph-tool gdal python=3.10

RUN git clone https://github.com/MaxBo/REPAiR-Web.git /root/repairweb
WORKDIR /root/repairweb
RUN git pull
RUN git checkout feature/update

ENV PATH="${PATH}:/root/miniconda3/bin"
SHELL ["conda", "run", "-n", "repair", "/bin/bash", "-c"]

RUN python -m pip install --upgrade pip
RUN pip install -r /root/repairweb/requirements.txt


