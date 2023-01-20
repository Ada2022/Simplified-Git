import os
import hashlib
import json
import datetime

import zlib
import argparse


class Git:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.current_branch = ''
        self.commit_hash = ''
        self.commits = []
        self.branches = {}

        self.staged_files = []
        self.modified_files = []
        self.untracked_files = []

    def init(self):
        if os.path.exists(os.path.join(self.repo_path, '.git')):  # already init
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

    def is_init(self):
        if os.path.exists(os.path.join(self.repo_path, '.git')):
            print(f'Git has been initialized')
        else:
            print(f'Git initialization is successful, the default branch is master')

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

    def commit(self, message, author):
        commit_data = {
            'hash': None,
            'parent': self.commit_hash,
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'author': author,
            'message': message,
        }
        commit_json = json.dumps(commit_data, sort_keys=True)
        commit_hash = hashlib.sha1(commit_json.encode()).hexdigest()
        with open(os.path.join(self.repo_path, '.git', 'objects', commit_hash), 'w') as commit_file:
            commit_file.write(commit_json)
        with open(os.path.join(self.repo_path, '.git', 'refs', 'heads', self.current_branch), 'w') as branch_file:
            branch_file.write(commit_hash)
        self.commit_hash = commit_hash
        commit_data["hash"] = commit_hash
        self.commits.append(commit_data)
        print(f'Committed changes with message: {message}')

    def log(self):
        path = os.path.join(self.repo_path, ".git", "objects")
        print("commit history")
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                continue
            with open(os.path.join(path, file)) as f:
                data = f.readline()
                print(data)

    def active_branch(self):
        print(f'Current active branch: {self.current_branch}')

    def status(self):
        self.find_modified()
        self.find_untracked_files()

        if len(self.modified_files):
            print("Modified Files:")
            for file in self.modified_files:
                print(f'    {file}')
        if len(self.staged_files):
            print("Staged Files:")
            for file in self.staged_files:
                print(f'    {file}')
        if len(self.untracked_files):
            print('Find Untracked Files:')
            for file in self.untracked_files:
                print(f'    {file}')

        if not self.modified_files and not self.staged_files:
            print("No changes to files.")

    def add(self, add_file):
        with open(os.path.join(self.repo_path, ".git", "index"), 'a') as index_file:
            for file in add_file:
                with open(os.path.join(self.repo_path, file), 'rb') as f:
                    data = f.read()
                    data = b'blob' + b' ' + str(len(data)).encode() + data
                    data_hash = hashlib.sha1(data).hexdigest()

                    # write object files
                    os.makedirs(os.path.join(self.repo_path,
                                '.git', 'objects', data_hash[0:2]))
                    with open(os.path.join(self.repo_path, '.git', 'objects', data_hash[0:2], data_hash[2:]), 'wb') as obj_file:
                        obj_file.write(zlib.compress(data))

                    # write index files
                    index_file.write("10064 " + data_hash +
                                     " 0 " + file + "\n")
                print(f'sucessfully add file {file}')

    def checkout(self, branch_name):
        if branch_name not in self.branches:
            print(f"Branch {branch_name} does not exist.")
            return

        self.current_branch = branch_name
        self.commit_hash = self.branches[branch_name]

        with open(os.path.join(self.repo_path, '.git', 'HEAD'), 'w') as head_file:
            head_file.write(f'ref: refs/heads/{self.current_branch}')
        print(f"Switched to branch {branch_name}")

    def find_untracked_files(self):
        existing_objs = os.listdir(os.path.join(
            self.repo_path, '.git', 'objects'))
        existing_objs = dict(zip(existing_objs, [0]*len(existing_objs)))

        self.untracked_files = []
        for file in os.listdir(self.repo_path):
            if file.endswith('git') or file in self.staged_files:
                continue
            with open(os.path.join(self.repo_path, file), 'rb') as f:
                data = f.read()
                data = b'blob' + b' ' + str(len(data)).encode() + data
                data_hash = hashlib.sha1(data).hexdigest()
                if data_hash[0:2] in existing_objs:
                    obj_name = os.listdir(os.path.join(
                        self.repo_path, '.git', 'objects', data_hash[0:2]))[0]
                    if data_hash[2:] == obj_name:
                        continue

                self.untracked_files.append(file)

    def find_modified(self):
        if not os.path.exists(os.path.join(self.repo_path, ".git", "index")):
            return

        for line in open(os.path.join(self.repo_path, ".git", "index"), 'r'):
            line = line.split(" ")
            staged_file = line[3][0:-1]
            staged_sha1 = line[1]
            self.staged_files.append(staged_file)

            # check deleted files
            if not os.path.exists(os.path.join(self.repo_path, staged_file)):
                self.modified_files.append(staged_file)
                continue
            # check modified files
            with open(os.path.join(self.repo_path, staged_file), "rb") as f:
                data = f.read()
                data = b'blob' + b' ' + str(len(data)).encode() + data
                data_hash = hashlib.sha1(data).hexdigest()
                if data_hash != staged_sha1:
                    self.modified_files.append(staged_file)

    def is_modified(self):
        self.find_modified()
        if len(self.modified_files):
            print("Find modified Files")
            for mod_file in self.modified_files:
                print(f"    {mod_file} was modified")
            return True
        return False

    def find_head_commit(self):
        path = os.path.join(self.repo_path, ".git", "objects")
        current_time = datetime.datetime.now()
        head_commit = None
        min_time_diff = None

        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                continue
            with open(os.path.join(path, file)) as f:
                data = f.readline()
                data = data.split(",")
                commit = {}
                for item in data:
                    item = item.split(":", maxsplit=1)
                    commit[item[0].strip(" \"\"{}")] = item[1].strip(" \"\"{}")

                commit_time = datetime.datetime.strptime(
                    commit['time'], '%Y-%m-%d %H:%M:%S')
                time_diff = current_time - commit_time

                if not min_time_diff or time_diff < min_time_diff:
                    min_time_diff = time_diff
                    head_commit = commit

        return head_commit

    def is_authored(self):
        current_time = datetime.datetime.now()

        head_commit = self.find_head_commit()
        commit_time = datetime.datetime.strptime(
            head_commit["time"], '%Y-%m-%d %H:%M:%S')
        time_diff = current_time - commit_time

        if time_diff.days <= 7:
            print(
                f'Commit {head_commit["message"]} was authored in the last week')
            return True

        print(
            f'Commit {head_commit["message"]} was not authored in the last week')
        print(f'Commit was authored by {head_commit["author"]}')
        return False

    def is_rufus(self):
        head_commit = self.find_head_commit()
        if head_commit["author"] == "Rufus":
            return True

        return False


def process_args(args):
    git = Git(args.git_dir)
    if args.init:
        git.is_init()
    git.init()

    if args.active_branch:
        git.active_branch()
    if args.local_changes:
        print(git.is_modified())
    if args.recent_commit:
        print(git.is_authored())
    if args.blame_Rufus:
        print(git.is_rufus())

    if args.branch:
        git.branch(args.branch)
    if args.checkout:
        git.checkout(args.checkout)
    if args.status:
        git.status()
    if args.add:
        git.add(args.add)
    if args.commit:
        git.commit(args.commit[0], args.commit[1])
    if args.log:
        git.log()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--git_dir', required=True)

    parser.add_argument('--active_branch', action="store_true")
    parser.add_argument('--local_changes', action="store_true")
    parser.add_argument('--recent_commit', action="store_true")
    parser.add_argument('--blame_Rufus', action="store_true")

    parser.add_argument('--init', action="store_true")
    parser.add_argument('--branch', type=str, default='')
    parser.add_argument('--checkout', type=str, default='')
    parser.add_argument('--status', action="store_true")
    parser.add_argument('--add', type=str, nargs="+", default=[])
    parser.add_argument('--commit', type=str, nargs="+", default=[])
    parser.add_argument('--log', action="store_true")

    args = parser.parse_args()
    process_args(args)
