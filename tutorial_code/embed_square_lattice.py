# Copyright 2023 D-Wave
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os

import dimod
import numpy as np
import time 

from minorminer.utils.raster_embedding import (raster_embedding_search,
                                               embeddings_to_ndarray,
                                               raster_breadth_subgraph_lower_bound)


def embed_square_lattice(sampler, L, try_to_load=True, **kwargs):
    """Embeds a square lattice of length `L` (LxL cylinder).

    Args:
        L (int): lattice length
        try_to_load (bool, optional): Flag for whether to load from cached data. Defaults to True.

    Returns:
        Tuple[np.ndarray, dimod.BQM]: A matrix of embeddings and BQM for the lattice.
    """

    bqm = dimod.BinaryQuadraticModel(vartype='SPIN')

    for x in range(L):
        for y in range(L):
            bqm.add_variable(x * L + y)

    for x in range(L):
        for y in range(L):
            if (x + y) % 2:
                bqm.set_quadratic(x * L + y, x * L + ((y + 1) % L), 1)
            else:
                bqm.set_quadratic(x * L + y, x * L + ((y + 1) % L), -1)
            if x < L - 1:
                bqm.set_quadratic(x * L + y, (x + 1) * L + y, 1)

    G = dimod.to_networkx_graph(bqm)
    A = sampler.to_networkx_graph()

    solver_name = sampler.properties['chip_id'] # sampler.solver.name
    cache_filename = f'cached_embeddings/{solver_name}__L{L:02d}_square_embeddings_cached.txt'
    if try_to_load:
        try:
            print(f"Trying to load cache file from: {cache_filename}")
            embeddings = np.loadtxt(cache_filename, dtype=int)
            print(f'Loaded embedding from file {cache_filename}')
            return embeddings, bqm
        except (ValueError, FileNotFoundError) as e:
            print(f"Failed to load {cache_filename} with `np.loadtxt`")
            print("Error:", e)
            print("Finding embedding via raster embedding search instead.")

        lower_bound = raster_breadth_subgraph_lower_bound(S=G, T=A)
        print(lower_bound)

        start_time = time.time() 
        # put a timer and print a time for the process, try raster_breath = 4, 5, 6
        embeddings = embeddings_to_ndarray(raster_embedding_search(S=G, T=A, timeout=10, raster_breadth=6),
                                           node_order=sorted(G.nodes()))
        elapsed_time = time.time() - start_time  # Calculate elapsed time
        print(f"Execution Time: {elapsed_time:.6f} seconds")

    os.makedirs('cached_embeddings/', exist_ok=True)
    np.savetxt(cache_filename, embeddings, fmt='%d')

    return embeddings, bqm


def main():
    L = 12  # Linear size of square lattice to embed (LxL cylinder)
    embeddings, bqm = embed_square_lattice(L, raster_breadth=5, max_num_emb=1,
                                           timeout=100)


if __name__ == "__main__":
    main()
