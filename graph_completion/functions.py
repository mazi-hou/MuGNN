import numpy as np
import multiprocessing
from scipy import spatial as spatial

from tools.print_time_info import print_time_info


def str2int4triples(triples):
    return [(int(head), int(tail), int(relation)) for head, tail, relation in triples]


def get_hits(sim, top_k=(1, 10, 50, 100)):
    test_num = sim.shape[0]

    # sim = spatial.distance.cdist(Lvec, Rvec, metric='minkowski', p=2)
    # sim = spatial.distance.cdist(Lvec, Rvec, metric='cityblock')
    def top_get(sim, top_k):
        top_x = [0] * len(top_k)
        for i in range(sim.shape[0]):
            rank = sim[i, :].argsort()
            rank_index = np.where(rank == i)[0][0]
            for j in range(len(top_k)):
                if rank_index < top_k[j]:
                    top_x[j] += 1
        return top_x

    top_lr = multiprocess_topk(sim, top_k)
    top_rl = multiprocess_topk(sim.T, top_k)
    for i in range(len(top_rl)):
        top_lr[i] = top_lr[i] / test_num * 100
        top_rl[i] = top_rl[i] / test_num * 100

    print_time_info('For each source:')
    for i in range(len(top_lr)):
        print_time_info('Hits@%d: %.2f%%' % (top_k[i], top_lr[i]))
    print('')
    print_time_info('For each target:')
    for i in range(len(top_rl)):
        print_time_info('Hits@%d: %.2f%%' % (top_k[i], top_rl[i]))
    # return Hits@10
    return top_lr, top_rl


def multiprocess_topk(sim, top_k=(1, 10, 50, 100)):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    n_p = 4

    # top_x = [0] * len(top_k)
    def top_get(sim, top_k, id, return_dict, chunk_size):
        top_x = [0] * len(top_k)
        s = chunk_size * id
        for i in range(sim.shape[0]):
            rank = sim[i, :].argsort()
            rank_index = np.where(rank == i + s)[0][0]
            for j in range(len(top_k)):
                if rank_index < top_k[j]:
                    top_x[j] += 1
        return_dict[id] = top_x

    test_num = sim.shape[0]
    chunk = test_num // n_p + 1
    sim_chunked = [sim[i:chunk + i, :] for i in range(0, test_num, chunk)]
    assert len(sim_chunked) == n_p
    pool = []
    for i, sim_chunk in enumerate(sim_chunked):
        p = multiprocessing.Process(target=top_get, args=(sim_chunk, top_k, i, return_dict, chunk))
        pool.append(p)
        p.start()
    for p in pool:
        p.join()
    top_x = [0] * len(top_k)
    for i, top_kk in return_dict.items():
        assert len(top_x) == len(top_kk)
        for j in range(len(top_kk)):
            top_x[j] += top_kk[j]
    return top_x


def multi_process_get_nearest_neighbor(sim, ranks, nega_sample_num=25):
    assert len(sim) == len(ranks)
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    n_p = 4
    # top_x = [0] * len(top_k)
    def nega_get(sim, c_ranks, ranks, nega_sample_num, return_dict):
        for i in range(len(sim)):
            rank = sim[i, :].argsort()
            nega_sample = rank[1:nega_sample_num + 1]
            nega_sample = [ranks[sample] for sample in nega_sample]
            assert len(nega_sample) == nega_sample_num
            return_dict[c_ranks[i]] = nega_sample

    test_num = len(sim)
    chunk = test_num // n_p + 1
    sim_chunked = [sim[i:chunk + i, :] for i in range(0, test_num, chunk)]
    rank_chunked = [ranks[i:chunk +i] for i in range(0, test_num, chunk)]
    assert len(sim_chunked) == n_p
    pool = []
    for i, sim_chunk in enumerate(sim_chunked):
        p = multiprocessing.Process(target=nega_get, args=(sim_chunk, rank_chunked[i], ranks, nega_sample_num, return_dict))
        pool.append(p)
        p.start()
    for p in pool:
        p.join()
    return dict(return_dict)
