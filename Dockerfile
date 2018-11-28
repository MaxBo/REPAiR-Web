FROM maxboh/docker-circleci-node-miniconda-gdal

RUN git clone https://github.com/H2020Cinderela/Cinderela-Web.git $HOME/repairweb
RUN cd $HOME/repairweb

