FROM maxboh/docker-circleci-node-miniconda-gdal

RUN git clone https://github.com/H2020Cinderela/Cinderela-Web.git $HOME/cinderelaweb
RUN cd $HOME/cinderelaweb

