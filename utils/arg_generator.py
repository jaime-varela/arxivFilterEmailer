import argparse

def get_default_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filter_file', type=str, help='Json file to use in filtering (default is arxivMeta.json)',default="arxivMeta.json")
    parser.add_argument('--use_dropbox', action='store_true', help='Import dropbox file from root path')
    args = parser.parse_args()
    return args
