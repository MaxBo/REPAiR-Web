# first start a container and install jupyter

docker run --name gt_test -v "$(pwd)":/tmp -p 8888:8888 -p 6006:6006 -it -u root -w /home/user tiagopeixoto/graph-tool bash

# start the notebook

jupyter notebook --ip=0.0.0.0 --allow-root --notebook-dir=/tmp
