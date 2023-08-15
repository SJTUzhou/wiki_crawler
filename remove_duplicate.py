import os
import glob

import json



def remove_duplicate_lines(input_file, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    lines_seen = set()
    
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if line not in lines_seen:
                outfile.write(line)
                lines_seen.add(line)
    
    print("Duplicate lines removed and saved to", output_file)


def remove_duplicate_lines_in_jsonl_files(input_directory, output_directory):
    os.makedirs(output_directory, exist_ok=True)
    urls_seen = set()
    def remove_duplicate_lines_by_url_key(input_file, output_file):
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            for line in infile:
                data = json.loads(line)
                url = data.get('url', None)
                
                if url is not None and url not in urls_seen:
                    outfile.write(json.dumps(data) + '\n')
                    urls_seen.add(url)
        
        print("Duplicate lines removed and saved to", output_file)

    for filename in os.listdir(input_directory):
        if filename.endswith('.jsonl'):
            input_file_path = os.path.join(input_directory, filename)
            output_file_path = os.path.join(output_directory, filename)
            remove_duplicate_lines_by_url_key(input_file_path, output_file_path)







if __name__ == "__main__":
    # Replace these with your input and output file paths
    input_session_file = "./ray_wiki_output/session_visited_urls.txt"
    output_session_file = "./ray_wiki_output_unique/session_visited_urls.txt"
    remove_duplicate_lines(input_session_file, output_session_file)

    # Replace these with your input and output directory paths
    input_directory = './ray_wiki_output'
    output_directory = './ray_wiki_output_unique'
    remove_duplicate_lines_in_jsonl_files(input_directory, output_directory)