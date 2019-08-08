FROM maxboh/docker-circleci-node-miniconda-gdal:graph_tool_stretch

RUN git clone https://github.com/MaxBo/REPAiR-Web.git $HOME/repairweb
RUN cd $HOME/repairweb

