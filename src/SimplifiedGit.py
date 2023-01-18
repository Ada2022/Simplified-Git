import os
import hashlib
import json
import datetime


class Git:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.current_branch = 'master'
        self.commit_hash = ''
        self.commits = []
        self.branches = {'master': None}
        self.staged_files = []
        self.modified_files = []
        self.deleted_files = []

    def init(self):
        os.makedirs(os.path.join(self.repo_path, '.git', 'objects'))
        os.makedirs(os.path.join(self.repo_path, '.git', 'refs', 'heads'))
        os.makedirs(os.path.join(self.repo_path, '.git', 'refs', 'tags'))
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

    def commit(self, message, author):
        commit_data = {
            'hash': None,
            'message': message,
            'parent': self.commit_hash,
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'author': author
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
        if self.commit_hash is None:
            print("No commits yet")
            return
        head_commit = next(
            (commit for commit in self.commits if commit["hash"] == self.commit_hash), None)
        if head_commit is None:
            print("No commits yet")
            return
        current_time = datetime.datetime.now()
        commit_time = datetime.datetime.strptime(
            head_commit["time"], '%Y-%m-%d %H:%M:%S')
        time_diff = current_time - commit_time
        if time_diff.days < 7:
            print(
                f'Commit {head_commit["hash"]} was authored in the last week')
        else:
            print(
                f'Commit {head_commit["hash"]} was not authored in the last week')
        print(f'Commit was authored by {head_commit["author"]}')

    def active_branch(self):
        print(f'Current active branch: {self.current_branch}')

    def status(self):
        if self.modified_files:
            print("Modified Files:")
            for file in self.modified_files:
                print(file)
        if self.staged_files:
            print("Staged Files:")
            for file in self.staged_files:
                print(file)
        if self.deleted_files:
            print("Deleted Files:")
            for file in self.deleted_files:
                print(file)
        if not self.modified_files and not self.staged_files and not self.deleted_files:
            print("No changes to files.")

    def add_file(self, file_name, file_content):
        with open(os.path.join(self.repo_path, file_name), 'w') as file:
            file.write(file_content)
        self.staged_files.append(file_name)
        print(f"File {file_name} added.")

    def checkout(self, branch_name):
        if branch_name not in self.branches:
            print(f"Branch {branch_name} does not exist.")
            return
        self.current_branch = branch_name
        self.commit_hash = self.branches[branch_name]
        print(f"Switched to branch {branch_name}")


class File:
    def __init__(self, file_path):
        self.file_path = file_path
        self.content = ""

    def is_modified(self):
        with open(self.file_path, 'r') as f:
            current_content = f.read()
            if current_content != self.content:
                self.content = current_content
                return True
        return False


if __name__ == '__main__':
    repo_path = '/home/ada/Desktop/Simplified-Git/src'
    git = Git(repo_path)
    git.init()
    git.active_branch()
    git.branch('Hao_dev')
    git.checkout('Hao_dev')
    git.active_branch()

    git.status()
    git.add_file('test.txt', 'This is a test file.')
    git.status()

    git.commit('Hello World', 'Hao')
    git.log()

    git.commit('Initial commit', 'Rufus')
    git.log()
