from github import Github
import os

# Class to handle files between flask and github
class git_file_server:

    # Initialing with path_of_upload_folder as the path where the uploaded files will be
    # Needs a environmental variable with GITHUB_TOKEN as the github api token and 
    # GITHUB_REPO as the link to the github repository where the files will be stored
    def __init__(self,path_of_upload_folder,token,repo,branch):
        self.path_of_upload_folder=path_of_upload_folder
        self.token = token
        self.github_object = Github(self.token)
        self.branch = branch # Branch of github repository
        self.pushed_files=[] # Files pushed till now
        self.files_in_github=[] # Files that are in github_repository
        self.repo = repo
        self.repository = self.github_object.get_repo(self.repo)
    
    # Intend to push file to github_repo
    def push_file(self,filename):
        self.pushed_files.append(filename)
        f = open(filename,"rb")
        content = f.read()
        f.close()
        self.repository.create_file(filename,f"Updated {filename}",content,branch=self.branch)
        if os.path.exists(filename):
            os.remove(filename)

    # Intended to push all files in upload_folder to github_repository
    def push_all_files(self):
        for filename in os.scandir(self.path_of_upload_folder):
            if filename.is_file():
                self.push_file(filename.path)
                
    # Intend to return an array of all files in image directory
    def pull_all_filename(self):
        self.files_in_github=[]
        contents=self.repository.get_contents("",ref=self.branch)
        while contents:
            file_content=contents.pop(0)
            if file_content.type == "dir":
                contents.extend(self.repository.get_contents(file_content.path))
            else:
                self.files_in_github.append(file_content.path)
        return self.files_in_github
    
    # Intend to get file content from github
    def pull_file_content(self,filename):
        contents = self.repository.get_contents(filename, ref=self.branch)
        return contents.decoded_content
    
    # Intend to get file and save it in image directory
    def pull_file(self,filename):
        file_content=self.pull_file_content(filename)
        f=open(filename,"wb")
        f.write(file_content)
    
    # Intend to download all files in image directory
    def pull_all_files(self):
        for i in self.pull_all_filename():
            self.pull_file(i)   
    
    # Intend to return file link of given filename
    def pull_file_link(self,filename):
        filename=filename.replace(" ","%20")
        return f"https://github.com/{self.repo}/blob/main/{filename}?raw=true"

    # Intend to return all file link
    def pull_all_file_link(self):
        file_name_array = self.pull_all_filename()
        file_link_array = []
        for i in file_name_array:
            file_link_array.append(self.pull_file_link(i))
            file_name_array.remove(i)
        return file_link_array
    
    # Intend to delete a file in github repository
    def delete_file(self,filename):
        contents = self.repository.get_contents(filename, ref=self.branch)
        self.repository.delete_file(contents.path, f"{contents.path} Deleted", contents.sha)
    
    # Intend to delete all files in github repo
    def delete_all_files(self):
        filename_array = self.pull_all_filename()
        for i in filename_array:
            self.delete_file(i)
    
    def push_file_get_link(self,filename):
        self.push_file(filename)
        return self.pull_file_link(filename)


# class github_store:
#     def __init__(self,file_path=None):
#         if file_path == None:
#             self.file_path = "chat_log.txt"
#         self.token = os.getenv("GITHUB_TOKEN")
#         self.github_object = Github(self.token)
#         self.branch = "main"
#         self.repository = self.github_object.get_repo("marsha-nicky/my_knowledge")
    
#     def pull_data(self):
#         contents = self.repository.get_contents(self.file_path, ref=self.branch)
#         return contents.decoded_content.decode()

#     def push(self,path=None, message=None, content=None, branch=None, update=False):

#         if path == None:
#             path = self.file_path
#         if message == None:
#             message = "Added chat knowledge"
#         if content == None:
#             content = self.data
#         if branch == None:
#             branch = self.branch

#         source = self.repository.get_branch(branch)
#         if update:  # If file already exists, update it
#             contents = self.repository.get_contents(path, ref=branch)  # Retrieve old file to get its SHA and path
#             self.repository.update_file(contents.path, message, content, contents.sha, branch=branch)  # Add, commit and push branch
#             print("github_storage : updated content")
#         else:  # If file doesn't exist, create it
#             self.repository.create_file(path, message, content, branch=branch)  # Add, commit and push branch