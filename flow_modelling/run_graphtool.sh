#!/bin/bash
docker run --rm -v "$(pwd)":/tmp -p 8888:8888 -p 6006:6006 -it -u user -w /home/user tiagopeixoto/graph-tool jupyter notebook --ip=0.0.0.0 --notebook-dir=/tmp

