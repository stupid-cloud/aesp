import copy
import ase.db
import itertools
import numpy as np
from aesp.structure import struc_type
from sklearn import cluster

class DataConnection:
    """Class that handles all database communication.

    All data communication is collected in this class in order to
    make a decoupling of the data representation and the GA method.

    A new candidate must be added with one of the functions
    add_unrelaxed_candidate or add_relaxed_candidate this will correctly
    initialize a configuration id used to keep track of candidates in the
    database.
    After one of the add_*_candidate functions have been used, if the candidate
    is further modified or relaxed the functions add_unrelaxed_step or
    add_relaxed_step must be used. This way the configuration id carries
    through correctly.

    Parameters:

    db_file_name: Path to the ase.db data file.
    """

    def __init__(self, db_file_name):
        self.db_file_name = db_file_name
        # if not os.path.isfile(self.db_file_name):
        #     raise IOError('DB file {0} not found'.format(self.db_file_name))
        self.db = ase.db.connect(self.db_file_name)
        self.already_returned = set()
    
    def get_number_of_candidates(self, **kwargs):
        """ Returns the number of candidates not yet queued or relaxed. """
        ar_list = list(self.db.select(**kwargs))
        if len(ar_list) == 0:
            return 0
        ar_list = self.__delete_duplicate__(ar_list)
        return len(ar_list)
    
    def __delete_duplicate__(self, allcands):
        """ Method for obtaining the latest traj
            file for a given configuration.
            There can be several traj files for
            one configuration if it has undergone
            several changes (mutations, pairings, etc.)."""
        allcands.sort(key=lambda x: x.mtime)
        g_s_s = []
        for idx, cand in enumerate(allcands):
            l_key = "{}-{}-{}".format(
                cand.key_value_pairs['generation'], 
                cand.key_value_pairs['stage'],
                cand.key_value_pairs['s_id']
                )
            if l_key not in g_s_s:
                g_s_s.append(l_key)
            else:
                allcands.pop(idx)

        # return self.get_atoms(all[-1].gaid)
        return allcands
    
    def get_candidates(self, value="all", **kwargs):
        """Return all unrelaxed candidates,
        useful if they can all be evaluated quickly."""
        
        ar_list = list(self.db.select(**kwargs))
        if len(ar_list) == 0:
            return []
        ar_list = self.__delete_duplicate__(ar_list)
        res = []
        if value != "all":
            ar_list = ar_list[:value]
        for ar in ar_list:
            a = self.get_atoms(ar.id)
            a = struc_type[a.info['key_value_pairs']['struc_type']]().from_atoms(a)
            res.append(a)
        return res
    
    def get_energy_base_operator(self, oper_type_list, **kwargs):
        e_info = {}
        e_info_type_list = []
        for oper_type in oper_type_list:
            e_info_type = {}
            ar_list = list(self.db.select(oper_type=oper_type, **kwargs))
            if len(ar_list) != 0:
                e_dict = {}
                for ar in ar_list:
                    if e_dict.get(ar.key_value_pairs['oper_name'], False):
                        e_dict[ar.key_value_pairs['oper_name']].append(ar.key_value_pairs["fitness"])
                    else:
                        e_dict[ar.key_value_pairs['oper_name']] = [ar.key_value_pairs["fitness"]]
                for k, v, in e_dict.items():
                    e_info_type[k] = sum(v) / len(v)
                e_info_type_list.append(e_info_type)
                if len(e_dict) != 0:
                    mean_e = sum(e_info_type.values()) / len(e_info_type.values())
                    e_info[oper_type] = mean_e

        mean_e = sum(e_info.values()) / len(e_info.values())
        e_info['operator'] = mean_e
        for e_info_type in e_info_type_list:
            e_info.update(**e_info_type)  
        return e_info

    def get_max_stage(self, generation):
        stage = set(t.stage for t in self.db.select(generation=generation))
        return max(stage)

    def get_max_generation(self):
        generation = set(t.generation for t in self.db.select())
        return max(generation)

    def get_next_id(self):
        """Get the id of the next candidate to be added to the database.
        This is a hacky way of obtaining the id and it only works on a
        sqlite database.
        """
        con = self.db._connect()
        last_id = self.db.get_last_id(con.cursor())
        con.close()
        return last_id + 1
    
    def get_next_s_id(self):
        """获得下一个s_id"""
        s_ids = {i.s_id for i in list(self.db.select("s_id"))}
        if len(s_ids) == 0:
            s_id = 1
        else:
            s_id = max(s_ids) + 1
        return s_id

    def add_unrelaxed_candidate(self, candidate, **kwargs):
        """ Adds a new candidate which needs to be relaxed. """
        s_id = self.get_next_s_id()
        candidate.info['s_id'] = s_id
        self.db.write(candidate, **candidate.info, **kwargs)

    def add_relaxed_stage(self, candidate, **kwargs):
        self.db.write(candidate, **candidate.info, **kwargs)

    def get_diversity(self, **kwargs):
        """种群的多样性"""
        atom_list = self.get_candidates(**kwargs)
        # atom_list.append(3)
        total_simi = 0
        num = 0

        for a, b in itertools.combinations(atom_list, 2):
            simi = a.get_fp_similarity(b)
            total_simi += simi
            num += 1
        total_simi /= num
        return 1-total_simi

    # @staticmethod
    # def get_fp_similarity(atom1, atom2):
    #     fp1 = np.array(atom1.info['data']['fp'])
    #     fp2 = np.array(atom2.info['data']['fp'])
    #     simi = np.dot(fp1, fp2) / (np.linalg.norm(fp1) * np.linalg.norm(fp2))
    #     return float(simi)

    # def looks_like(self, atom1, atom2, simi_thres):
    #     simi = self.get_fp_similarity(atom1, atom2)
    #     return simi < simi_thres

    def update_population(self, generation, pop_size):
    
        max_stage = self.get_max_stage(generation)
        ar_list = list(self.db.select(stage=max_stage))

        # 最优的结构信息更新
        ar_list.sort(key=lambda x: x.key_value_pairs['fitness'])
        if ar_list[0].key_value_pairs.get('opt_pop_idx', None) is None:
            opt_pop_idxs = [generation]
        else:
            opt_pop_idxs = copy.deepcopy(ar_list[0].data['opt_pop_idxs'])
            opt_pop_idxs.append(generation)
        self.db.update(ar_list[0].id, data={'opt_pop_idxs': opt_pop_idxs}, opt_pop_idx=generation) 
        # 前50%进入候选列表
        ar_list = ar_list[:int(len(ar_list)/2)]
        # 种群更新
        fp = np.array([ar.data['fp'] for ar in ar_list])
        if pop_size > len(fp):
            pop_size = len(fp)
        labels = cluster.KMeans(n_clusters=pop_size, n_init='auto').fit_predict(fp).tolist()
 
        pop = []
        for num in range(pop_size):
            index = labels.index(num)
            pop.append(ar_list[index])
  
        for ar in pop:
            if ar.key_value_pairs.get('population', None) is None:
                pop_list = [generation]
            else:
                pop_list = copy.deepcopy(ar.data['pop_list'])
                pop_list.append(generation)
            self.db.update(ar.id, data={'pop_list': pop_list}, population=generation)
        
    def get_max_continuous_opt_num(self, population):
        opt_list = [dt.data['opt_pop_idxs'] for dt in self.db.select(opt_pop_idx=population)]
        if len(opt_list) == 0:
            return None
        max_continue_opt_num = len(max(opt_list, key=len))
        return max_continue_opt_num


    def get_participation_in_pairing(self):
        """ Get information about how many direct
            offsprings each candidate has, and which specific
            pairings have been made. This information is used
            for the extended fitness calculation described in
            L.B. Vilhelmsen et al., JACS, 2012, 134 (30), pp 12807-12816
        """
        entries = self.db.select(pairing=True)
        frequency = dict()
        pairs = []
        for e in entries:
            c1, c2 = e.data['parents']
            pairs.append(tuple(sorted([c1, c2])))
            if c1 not in frequency.keys():
                frequency[c1] = 0
            frequency[c1] += 1
            if c2 not in frequency.keys():
                frequency[c2] = 0
            frequency[c2] += 1
        return (frequency, pairs)

    
    def get_atoms(self, id, add_info=True):
        """Return the atoms object with the specified id"""
        a = self.db.get_atoms(id, add_additional_information=add_info)
        return a

    def get_param(self, parameter):
        """ Get a parameter saved when creating the database. """
        if self.db.get(1).get('data'):
            return self.db.get(1).data.get(parameter, None)
        return None


    def is_duplicate(self, **kwargs):
        """Check if the key-value pair is already present in the database"""
        return len(list(self.db.select(**kwargs))) > 0




