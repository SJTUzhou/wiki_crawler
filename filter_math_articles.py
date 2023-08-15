import os
import glob
import pandas as pd

_CRAWLED_WIKI_DATA_DIR = r"./ray_wiki_output_unique/"
_MATH_OUTPUT_DIR = r"./wiki_math_output/"

def filter_wiki_math_articles(crawled_src_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    jsonl_files = glob.glob(os.path.join(crawled_src_dir, "*.jsonl"))
    dfs = []
    for f in jsonl_files:
        df = pd.read_json(f, lines=True)
        df = df[df.apply(lambda x: "\displaystyle" in x["text"], axis=1)]
        dfs.append(df)
    df_all = pd.concat(dfs)
    print("filtered math data shape: ", df_all.shape)
    df_all.to_json(os.path.join(output_dir, "wiki_math_data.jsonl"), orient="records", lines=True)


if __name__ == "__main__":
    filter_wiki_math_articles(_CRAWLED_WIKI_DATA_DIR, _MATH_OUTPUT_DIR)