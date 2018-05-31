# networkx

Start jupyter notebook in a docker container. It will print a personal access token to the console, use that in a browser to access the notebook. If you use port forwarding (like below), don't forget to change the port in the link.

```bash
docker pull continuumio/anaconda3

docker run --rm -v "$(pwd):/opt/notebooks" -p 8899:8888 continuumio/anaconda3 jupyter notebook --notebook-dir=/opt/notebooks --ip=* --allow-root
```

create_graph.ipynb - create the graph of the sample material flows that is currently in the sankey diagram

organic_flow.graphml - the graph of the sample material flows that is currently in the sankey diagram

networkx_test.ipynb - analyze the graph
