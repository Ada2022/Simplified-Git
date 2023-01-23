# Simplified-Git

## Configuration Requirement

1. Environment Requirement: Ubuntu 18.04 or higher

2. Python Requirement: python 3.6.9 or higher

## Introduction

The project aims to implement a simplified git using python, this code mainly realizes the following functions:

### Basic Function

1. git init : initialize the git

2. git branch: create a new branch

3. git checkout: switch to the specified branch

4. git add: track the specified files

5. git commit: commit the tracked files with comments

6. git status: show the condition of each file

7. git log: show the commit history

### Shortcut Function

1. git active_branch: show the current branch

2. git local_changes: show whether the files have been modified after the lastest commit

3. git recent_commit: show whether the latest commit was authored in the last week

4. git blame_Rufus: show whether the latest commit was authored by Rufus

## Basic Usage

1. git init
   
   ```shell
   python SimplifiedGit.py --git_dir path/to/git/dir --init
   ```

2. git branch
   
   ```shell
   python SimplifiedGit.py --git_dir path/to/git/dir --branch [branch_name]
   ```

3. git checkout
   
   ```shell
   python SimplifiedGit.py --git_dir path/to/git/dir --checkout [branch_name]
   ```

4. git add
   
   ```shell
   python SimplifiedGit.py --git_dir path/to/git/dir --add [filename1 filename2 ...]
   ```

5. git commit
   
   ```shell
   python SimplifiedGit.py --git_dir path/to/git/dir --commit [commit_message commit_author]
   ```

6. git status
   
   ```shell
   python SimplifiedGit.py --git_dir path/to/git/dir --status
   ```

7. git log
   
   ```shell
   python SimplifiedGit.py --git_dir path/to/git/dir --log
   ```

8. git active_branch
   
   ```shell
   python SimplifiedGit.py --git_dir path/to/git/dir --active_branch
   ```

9. git local_changes
   
   ```shell
   python SimplifiedGit.py --git_dir path/to/git/dir --local_changes
   ```

10. git recent_commit
    
    ```shell
    python SimplifiedGit.py --git_dir path/to/git/dir --recent_commit
    ```

11. git blame_Rufus
    
    ```shell
    python SimplifiedGit.py --git_dir path/to/git/dir --blame_Rufus
    ```

## Examples

### Overall Test

1. clone the repository
   
   ```shell
   git clone https://github.com/Ada2022/Simplified-Git.git
   ```

2. cd to source code
   
   ```shell
   cd ./src
   ```

3. basic usage test examples
   
   pending

### Assignment Showcase

pending