import sys
import graph_tool.generation as gt
import numpy as np

def sample_k(max):
     accept = False
     while not accept:
         k = np.random.randint(1,max+1)
         accept = np.random.random() < 1.0/k
     print(k)
     return k

def deg_sample():
   if np.random.random() > 0.5:
       return np.random.poisson(4), np.random.poisson(4)
   else:
       return np.random.poisson(20), np.random.poisson(20)

#g = gt.random_graph(int(sys.argv[1]), lambda: sample_k(int(sys.argv[2])), 
#        model="probabilistic-configuration",
#        edge_probs=lambda i, k: 1.0 / (1 + abs(i - k)),
#        directed=True, parallel_edges=False, n_iter=int(sys.argv[3])
#    )

#g = gt.random_graph(1000, lambda: sample_k(40), model="probabilistic-configuration", edge_probs=lambda i, k: 1.0 / (1 + abs(i - k)), n_iter=100)

g = gt.random_graph(int(sys.argv[1]), deg_sample)

n = int(sys.argv[1]) / 1000
#n = "tmp"
f = "/tmp/random_" + str(int(n)) + "k.xml.gz"
f2 = "/tmp/random_" + str(int(n)) + "k.gt"
print("saving", f)
print("saving", f2)
g.save(f)
g.save(f2)
