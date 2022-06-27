import csv


def get_proportions(data_path: str, interesting_tags: list) -> dict:
    """asdf"""
    tag_count = {tag: 0 for tag in interesting_tags}
    total_mails = 0
    with open(data_path, "r", encoding="utf-8") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=",", quotechar='"')
        for row in spamreader:
            tags = row[6][1:-1].split(", ")
            interesting = filter_uninteresting(tags, interesting_tags)
            if len(interesting) == 0:
                continue
            total_mails += 1
            for i in interesting:
                tag_count[i] += 1
    for t, v in tag_count.items():
        tag_count[t] = v / float(total_mails)
    return tag_count


def filter_uninteresting(tags: list, interesting_tags: list) -> list:
    """asdf"""
    interesting = []
    for tag in tags:
        for i in interesting_tags:
            if tag == i:
                interesting.append(tag)
    return interesting


def generate_sample(data_path: str, interesting_tags: list):
    """asf"""
    props = get_proportions(data_path, interesting_tags)
    gen = Generator()
    gen.generate_sample(data_path, props, 120)


class Generator:
    """asdf"""

    best_sample_score = 999999999999999999
    best_sample = None

    def generate_sample(self, data_path: str, proportions: dict, samplesize: int):
        goal = {p_key: p_val * samplesize for p_key, p_val in proportions.items()}
        current_prop = {p_key: 0 for p_key in proportions.keys()}
        with open(data_path, "r", encoding="utf-8") as csv_data:
            reader = csv.reader(csv_data, delimiter=",", quotechar='"')
            lst = []
            for row in reader:
                lst.append(
                    filter_uninteresting(row[6][1:-1].split(", "), proportions.keys())
                )
        sample = [None] * samplesize
        for index in range(len(lst)):
            self.rec_sample_gen(0, index, current_prop, goal, lst, samplesize, sample)

        print(f"{self.best_sample_score=}\n{self.best_sample}")

    def rec_sample_gen(
        self,
        depth: int,
        current: int,
        current_prop: dict,
        goal: dict,
        reader: list,
        samplesize: int,
        sample: list,
    ):
        """asdf"""
        if depth == samplesize:
            difference = 0
            for c_key, c_val in current_prop.items():
                difference += abs(c_val - goal[c_key])
            if difference < self.best_sample_score:
                self.best_sample_score = difference
                self.best_sample = sample
                print(
                    f"Found better one: {self.best_sample_score=}\n{self.best_sample}"
                )
        else:
            for i in range(current + 1, len(reader) - samplesize):
                row = reader[i]
                if len(row) == 0:
                    continue
                sample[depth] = i
                for c_key in row:
                    current_prop[c_key] += 1
                self.rec_sample_gen(
                    depth + 1, i, current_prop, goal, reader, samplesize, sample
                )
                for c_key in row:
                    current_prop[c_key] -= 1


def build_sample(sample: list, data_path: str, output_path: str):
    with open(data_path, "r", encoding="utf-8") as csv_data:
        reader = csv.reader(csv_data, delimiter=",", quotechar='"')

        current: int = 0
        output = [None] * len(sample)

        for index, ele in enumerate(reader):
            if index != sample[current]:
                continue
            output[current] = ele
            current += 1
            if current >= len(sample):
                break

    with open(output_path, "w", encoding="utf-8") as output_file:
        for ele in output:
            entry = ""
            for a in ele:
                entry = f'{entry}, "{a}"'
            output_file.write(f"{entry[2:]}\n")


if __name__ == "__main__":
    DATA_PATH = "./data/sampling/complete_sample.csv"
    OUTPUT_PATH = "./data/sampling/subsample.csv"
    saught_tags = [
        "existence-behavioral",
        "existence-structural",
        "process",
        "property",
        "technology",
    ]

    sample = [
        4,
        5,
        7,
        10,
        13,
        15,
        17,
        18,
        19,
        20,
        24,
        25,
        26,
        27,
        28,
        30,
        32,
        33,
        36,
        37,
        39,
        40,
        42,
        44,
        46,
        49,
        50,
        51,
        52,
        55,
        56,
        58,
        59,
        60,
        63,
        66,
        68,
        69,
        70,
        72,
        74,
        75,
        78,
        79,
        80,
        81,
        84,
        85,
        86,
        87,
        88,
        89,
        90,
        93,
        96,
        97,
        99,
        100,
        101,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
        109,
        110,
        112,
        113,
        115,
        116,
        117,
        120,
        121,
        122,
        123,
        124,
        125,
        127,
        129,
        130,
        132,
        133,
        134,
        138,
        139,
        140,
        141,
        142,
        143,
        144,
        145,
        146,
        147,
        148,
        151,
        153,
        156,
        157,
        158,
        161,
        162,
        164,
        165,
        167,
        168,
        169,
        172,
        173,
        175,
        178,
        179,
        183,
        184,
        219,
        260,
        261,
        391,
        414,
    ]

    build_sample(sample, DATA_PATH, OUTPUT_PATH)
