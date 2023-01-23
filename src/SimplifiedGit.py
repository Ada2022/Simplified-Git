import os
import hashlib
import json
import datetime

import zlib
import argparse

from collections import deque

class Git:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.current_branch = ''
        self.commit_hash = ''
        self.commits = []
        self.branches = {}

        self.modified_files = []
        self.untracked_files = []
        self.modified_tracked_files = []

    def is_init(self):
        if os.path.exists(os.path.join(self.repo_path, '.git')):
            print(f'Git has been initialized')
        else:
            print(f'Git initialization is successful, the default branch is master')

    def init(self):
        if os.path.exists(os.path.join(self.repo_path, '.git')): # already init
            for branch_name in os.listdir(os.path.join(self.repo_path, '.git', 'refs', 'heads')):
                self.branches[branch_name] = None  

            with open(os.path.join(self.repo_path, '.git', 'HEAD')) as head_file:
                data = head_file.readline()
                data = data.split("/")
                self.current_branch = data[-1]
        else: 
            os.makedirs(os.path.join(self.repo_path, '.git', 'objects'))
            os.makedirs(os.path.join(self.repo_path, '.git', 'refs', 'heads'))
            os.makedirs(os.path.join(self.repo_path, '.git', 'refs', 'tags'))
            self.current_branch = "master"
            self.branches = {"master": None}
            with open(os.path.join(self.repo_path, '.git', 'HEAD'), 'w') as head_file:
                head_file.write(f'ref: refs/heads/{self.current_branch}')

    def branch(self, branch_name):
        if not os.path.exists(os.path.join(self.repo_path, '.git', 'refs', 'heads', branch_name)):
            with open(os.path.join(self.repo_path, '.git', 'refs', 'heads', branch_name), 'w') as branch_file:
                branch_file.write(self.commit_hash)
            self.branches[branch_name] = None
            with open(os.path.join(self.repo_path, '.git', 'HEAD'), 'w') as head_file:
                head_file.write(f'ref: refs/heads/{self.current_branch}')
            print(f'Created new branch {branch_name}')
        else:
            print(f'Branch {branch_name} already exists')


    '''
    This command updates the index using the current content found in the working tree, 
    to prepare the content staged for the next commit.
    '''
    def add(self, add_file):
        with open(os.path.join(self.repo_path, ".git", "index"), 'a') as index_file:
            for file in add_file:
                with open(os.path.join(self.repo_path, file), 'rb') as f:
                    data = f.read()
                    data = b'blob' + b' ' + str(len(data)).encode() + data
                    data_hash = hashlib.sha1(data).hexdigest()

                    # write object files
                    if not os.path.exists(os.path.join(self.repo_path, '.git', 'objects', data_hash[0:2])):
                        os.mkdir(os.path.join(self.repo_path, '.git', 'objects', data_hash[0:2]))
                    with open(os.path.join(self.repo_path, '.git', 'objects', data_hash[0:2],data_hash[2:]), 'wb') as blob_file:
                        blob_file.write(zlib.compress(data))

                    # write simplied index files, only contains path and content
                    index_file.write(os.path.join(self.repo_path, file) + " " + data_hash + "\n") 
            
                print(f'sucessfully add file {file}')
            index_file.write("#\n") # add a flag

    def find_head_index(self, index):
        st_index = -1
        ed_index = len(index) - 2
        for i in range(ed_index, st_index, -1):
            if index[i] == "#\n": 
                st_index = i
                break

        return index[st_index + 1: ed_index + 1]


    def parser_index(self, index):
        result = {}
        head_index = self.find_head_index(index)

        for item in head_index:
            item = item.split(" ")
            result[item[0].strip("\'\'")] = item[1].strip("\'\'\n")

        return result

    def parser_index_full(self, index):
        result = {}
        for item in index:
            if item == "#\n": continue
            item = item.split(" ")
            result[item[0].strip("\'\'")] = item[1].strip("\'\'\n")
        return result

        

    def commit_tree(self):
        # create a simplified tree object, deleted "mode" field and do not compress the content
        # tree content: path_to_file + space + obj_hash + \n 

        if not os.path.exists(os.path.join(self.repo_path, ".git", "index")): return 

        with open(os.path.join(self.repo_path, ".git", "index"), 'rb') as index_file:
            index_content = index_file.read()
            index_content = index_content.split(b"#")
            head_index = index_content[-2]

        tree_content = b'tree' + b' ' + str(len(head_index)).encode() +head_index
        tree_hash = hashlib.sha1(tree_content).hexdigest()

        if not os.path.exists(os.path.join(self.repo_path, ".git", "objects", tree_hash[0:2])): 
            os.mkdir(os.path.join(self.repo_path, ".git", "objects", tree_hash[0:2]))
        with open(os.path.join(self.repo_path, ".git", "objects", tree_hash[0:2], tree_hash[2:]), 'wb') as tree_file:
            # tree_file.write(zlib.compress(tree_content))
            tree_file.write(head_index)

        return tree_hash

    def parser_tree(self, tree):
        result = {}
        for item in tree:
            if item == "\n": continue
            item = item.split(' ')
            result[item[0]] = item[1].strip('\n')
        return result


    def commit(self, message, author):
        
        commit_data = { 
            'tree': None,
            'parent': None,
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'author': author,
            'committer':author,
            'message': message,
        }

        commit_data['tree'] = self.commit_tree()

        if os.path.exists(os.path.join(self.repo_path, ".git", "refs", "heads", self.current_branch)): 
            with open(os.path.join(self.repo_path, ".git", "refs", "heads", self.current_branch), 'r') as head_commit:
                commit_data['parent'] = head_commit.readline()

        commit_json = json.dumps(commit_data, sort_keys=True)
        commit_hash = hashlib.sha1(commit_json.encode()).hexdigest()
        if self.find_head_commit() == commit_hash: 
            print('Nothing to commit')
            return
        if not os.path.exists(os.path.join(self.repo_path, ".git", "objects", commit_hash[0:2])): 
            os.mkdir(os.path.join(self.repo_path, ".git", "objects", commit_hash[0:2]))
        with open(os.path.join(self.repo_path, '.git', 'objects', commit_hash[0:2], commit_hash[2:]), 'w') as commit_file:
            commit_file.write(commit_json)
        with open(os.path.join(self.repo_path, '.git', 'refs', 'heads', self.current_branch), 'w') as head_commit:
            head_commit.write(commit_hash)

        self.commits.append(commit_data)
        print(f'Committed changes with message: {message}')

    def parser_commit(self, commit):
        result = {}
        commit = commit.split(',')
        for item in commit:
            item = item.split(':', maxsplit = 1)
            result[item[0].strip("\"\"{ ")] = item[1].strip("\"\" }")
        return result

    def log(self):
        print("commit history")
        cur_commit_hash = self.find_head_commit()
        if cur_commit_hash == None:
            return

        while os.path.exists(os.path.join(self.repo_path, ".git", "objects", cur_commit_hash[0:2], cur_commit_hash[2:])):
            with open(os.path.join(self.repo_path, ".git", "objects", cur_commit_hash[0:2], cur_commit_hash[2:]), 'r') as commit_obj:
                cur_commit = self.parser_commit(commit_obj.readline())
                author = cur_commit['author']
                time = cur_commit['time']
                print(f'commit author: {author}, commit time: {time}')
                cur_commit_hash = cur_commit['parent']
                if cur_commit_hash == None: 
                    break

    def active_branch(self):
        print(f'Current active branch: {self.current_branch}')

    '''
    Displays paths that have differences between the index file and the
    current HEAD commit, paths that have differences between the working
    tree and the index file, and paths in the working tree that are not
    tracked by Git. The first are what you _would_ commit by running `git commit`; 
    the second and third are what you _could_ commit by running 'git add' before running `git commit`.
    '''
    def status(self):

        self.find_modified_files()
        self.find_untracked_files()
        if len(self.modified_files):
            print("Changes to be committed") # differences between the index file and the current HEAD commit
            for file in self.modified_files:
                print(f'    {file}')
        if len(self.modified_tracked_files):
            print("Changes not staged for commit:") # paths that have differences between the working tree and the index file
            for file in self.modified_tracked_files:
                print(f'    {file}')
        if len(self.untracked_files):
            print('Untracked files:') # paths in the working tree that are not tracked by Git 
            for file in self.untracked_files:
                print(f'    {file}')
        if (len(self.modified_files) + len(self.untracked_files) + len(self.modified_tracked_files)) == 0:
            print("No changes, your repository is clean")

    def checkout(self, branch_name):
        if branch_name not in self.branches:
            print(f"Branch {branch_name} does not exist.")
            return
        
        self.current_branch = branch_name
        self.commit_hash = self.branches[branch_name]

        with open(os.path.join(self.repo_path, '.git', 'HEAD'), 'w') as head_file:
            head_file.write(f'ref: refs/heads/{self.current_branch}')
        print(f"Switched to branch {branch_name}")


    '''
    Find paths in the working tree that are not tracked by Git 
    and paths that have differences between the working tree and the index file
    '''
    def find_untracked_files(self):
        if not os.path.exists(os.path.join(self.repo_path, ".git", "index")): 
            index_map = {}
        else:
            with open(os.path.join(self.repo_path, ".git", "index"), 'r') as index_file:
                index_map = self.parser_index_full(index_file.readlines())

        files_in_working_tree = []
        for file in os.listdir(self.repo_path):  
            if os.path.isdir(os.path.join(self.repo_path, file)):
                if file.endswith('git'): continue
                file_in_sub_dir = deque([file])
                while file_in_sub_dir:
                    cur_path = file_in_sub_dir.popleft()
                    if os.path.isdir(os.path.join(self.repo_path, cur_path)):
                        files =  os.listdir(os.path.join(self.repo_path, cur_path))
                        for file in files:
                            cur_path = os.path.join(cur_path, file)
                            file_in_sub_dir.append(cur_path)
                    else:
                        if not os.path.isfile(os.path.join(self.repo_path, cur_path)): continue
                        files_in_working_tree.append(cur_path)
            else:
                files_in_working_tree.append(file)


        for file in files_in_working_tree:
            if os.path.join(self.repo_path, file) not in index_map: # files not in index map, so untracked
                self.untracked_files.append(file)
            else:
                with open(os.path.join(self.repo_path, file), 'rb') as blob_obj:
                    data = blob_obj.read()
                    data = b'blob' + b' ' + str(len(data)).encode() + data
                    data_hash = hashlib.sha1(data).hexdigest()
                if data_hash != index_map[os.path.join(self.repo_path, file)]: # files in index map, but has been modified
                    self.modified_tracked_files.append(file)

        for _, path in enumerate(index_map):
            key = path[len(self.repo_path):]
            if key not in files_in_working_tree:
                self.modified_tracked_files.append(key)
            


    def find_head_commit(self):
        path = os.path.join(self.repo_path, ".git", "refs", "heads", self.current_branch)
        if not os.path.exists(path): return None
        with open(path) as head_commit_file:
            head_commit = head_commit_file.readline()
        
        return head_commit

    def find_modified_files(self):
        # find index
        if not os.path.exists(os.path.join(self.repo_path, ".git", "index")): return # the repo has been initialized and nothing is staged 
        with open(os.path.join(self.repo_path, ".git", "index"), 'r') as index_file:
            index_content = self.parser_index(index_file.readlines())

        # find tree
        head_commit = self.find_head_commit()
        if head_commit:
            with open(os.path.join(self.repo_path, ".git", "objects", head_commit[0:2], head_commit[2:]), 'r') as commit_obj:
                commit = commit_obj.readline()
                tree_hash = self.parser_commit(commit)['tree']
            if tree_hash == "null": return
            with open(os.path.join(self.repo_path, ".git", "objects", tree_hash[0:2], tree_hash[2:]), 'r') as tree_obj:
                tree_content = self.parser_tree(tree_obj.readlines())
        else: tree_content = None

        if not tree_content:
            for item in index_content:
                
                self.modified_files.append(item.split('/')[-1])
            return
        
        for _, key in enumerate(index_content):
            if key in tree_content:   
                if tree_content[key] == index_content[key]: continue
                self.modified_files.append(key.split('/')[-1])
            else:
                self.modified_files.append(key.split('/')[-1])
        return 
 

    def is_modified(self):
        self.find_modified_files()
        self.find_untracked_files()
        return True if (len(self.modified_files) + len(self.untracked_files) + len(self.modified_tracked_files)) else False

    def is_authored(self):
        head_commit_hash = self.find_head_commit()
        if head_commit_hash == None: return False
        with open(os.path.join(self.repo_path, ".git", "objects", head_commit_hash[0:2], head_commit_hash[2:]), 'r') as commit_obj:
            head_commit = self.parser_commit(commit_obj.readline())

        current_time = datetime.datetime.now()
        commit_time = datetime.datetime.strptime(
                    head_commit["time"], '%Y-%m-%d %H:%M:%S')
        time_diff = current_time - commit_time

        return True if time_diff.days <= 7 else False


    def is_rufus(self):
        head_commit_hash = self.find_head_commit()
        if head_commit_hash == None: return False
        with open(os.path.join(self.repo_path, ".git", "objects", head_commit_hash[0:2], head_commit_hash[2:]), 'r') as commit_obj:
            head_commit = self.parser_commit(commit_obj.readline())

        return True if head_commit["author"] == "Rufus" else False



def process_args(args):

    git = Git(args.git_dir)
    if args.init:
        git.is_init()
    git.init()

    if args.active_branch: git.active_branch()
    if args.local_changes: print(git.is_modified())
    if args.recent_commit: print(git.is_authored())
    if args.blame_Rufus: print(git.is_rufus())



    if args.branch: git.branch(args.branch) 
    if args.checkout: git.checkout(args.checkout)
    if args.status: git.status()
    if args.add: git.add(args.add)
    if args.commit: git.commit(args.commit[0], args.commit[1])
    if args.log: git.log()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--git_dir', required = True)

    parser.add_argument('--active_branch',action="store_true")
    parser.add_argument('--local_changes',action="store_true")
    parser.add_argument('--recent_commit',action="store_true")
    parser.add_argument('--blame_Rufus',action="store_true")

    parser.add_argument('--init', action="store_true")
    parser.add_argument('--branch', type = str, default='')
    parser.add_argument('--checkout', type = str ,default = '')
    parser.add_argument('--status', action="store_true")
    parser.add_argument('--add', type=str, nargs="+", default=[])
    parser.add_argument('--commit', type = str, nargs="+", default=[])
    parser.add_argument('--log',action="store_true")

    args = parser.parse_args()
    process_args(args)



