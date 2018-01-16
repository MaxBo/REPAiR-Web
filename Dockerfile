FROM maxboh/docker-circleci-node-miniconda-gdal

RUN git clone git@github.com:MaxBo/REPAiR-Web.git repairweb
RUN cd repairweb

