"""asdf"""

import csv


def load_dataset(data_path: str, interesting_tags: list) -> list:
    """sdf"""
    data = []
    with open(data_path, "r", encoding="utf-8") as csv_data:
        for index, ele in enumerate(csv.reader(csv_data, delimiter=",", quotechar='"')):
            tags = []
            for tag in ele[6][1:-1].split(", "):
                for itag in interesting_tags:
                    if tag == itag:
                        tags.append(tag)
            if len(tags) > 0:
                data.append({"id": index, "subject": ele[3], "tags": tags})
    return data


def generate_proportions(data: list) -> dict:
    """asdf"""
    proportions = {}
    for ele in data:
        for tag in ele["tags"]:
            if tag in proportions:
                proportions[tag] += 1
            else:
                proportions[tag] = 1
    return {k: p / float(len(data)) for k, p in proportions.items()}


def generate_threads(data: list) -> list:
    """asdf"""
    thr = {}
    for ele in data:
        subject: str = ele["subject"]
        if subject.startswith("Re: "):
            subject = subject[4:]
        if subject in thr:
            thr[subject].append(ele)
        else:
            thr[subject] = [ele]
    return thr.values()


def calculate_thread_distribution(thr: list) -> list:
    """asdf"""
    results = [None] * len(thr)
    for index, thr in enumerate(thr):
        distr = {}
        for ele in thr:
            for tag in ele["tags"]:
                if tag in distr:
                    distr[tag] += 1
                else:
                    distr[tag] = 1
        results[index] = {"distr": distr, "emails": thr}
    return results


class Generator:
    """asdf"""

    def __init__(self, thr: list, prp: dict, samplesize: int):
        self.threads = thr
        self.props = {p_key: p_value * samplesize for p_key, p_value in prp.items()}
        self.samplesize = samplesize
        self.sample_score = 9999999999
        self.sample = []

    def generate(self):
        """asf"""
        distr = {k: 0 for k in self.props.keys()}
        sample = [None] * len(self.threads)
        for i in range(len(self.threads)):
            self.generate_helper(0, i, 0, sample, distr)

    def generate_helper(
        self, depth: int, current: int, size: int, sample: list, distr: dict
    ):
        """asdf"""
        if size > self.samplesize:
            difference = 0
            for c_key, c_val in distr.items():
                difference += abs(c_val - self.props[c_key])
            if difference < self.sample_score:
                self.sample_score = difference
                self.sample = list.copy(sample)
                print(f"Found better one:\n{self.sample_score=},\n{self.sample=}\n\n")
        else:
            for i in range(current + 1, len(self.threads)):
                # addition
                sample[depth] = self.threads[i]
                for mail in self.threads[i]["emails"]:
                    for tag in mail["tags"]:
                        distr[tag] += 1
                size += len(self.threads[i]["emails"])

                # recursion
                self.generate_helper(depth + 1, i, size, sample, distr)

                # cleanup
                sample[depth] = None
                for mail in self.threads[i]["emails"]:
                    for tag in mail["tags"]:
                        distr[tag] -= 1
                size -= len(self.threads[i]["emails"])


DATA_PATH = "./data/sampling/complete_sample.csv"
INTERESTING_TAGS = [
    "existence-behavioral",
    "existence-structural",
    "process",
    "property",
    "technology",
]
data_set = load_dataset(DATA_PATH, INTERESTING_TAGS)
props = generate_proportions(data_set)
threads = generate_threads(data_set)
threads = calculate_thread_distribution(threads)
gen = Generator(threads, props, 120)
gen.generate()
