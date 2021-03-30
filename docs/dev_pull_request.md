# Pull requests

Below are the steps on how to Fork a GitHub Repository and Submit a Pull Request.

Before you continue you may want to check how to
[Creating a personal access token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
on your GitHub account.


1. [Fork](http://help.github.com/fork-a-repo/) the project, clone your fork,
   and configure the remotes:

   ```bash
   # Clone your fork of the repo into the current directory
   git clone https://github.com/<your-username>/cbm.git
   # Navigate to the newly cloned directory
   cd cbm
   # Assign the original repo to a remote called "upstream"
   git remote add upstream https://github.com/ec-jrc/cbm.git
   ```


2. If you cloned a while ago, get the latest changes from upstream:

   ```bash
   git checkout main
   git pull upstream main
   ```


3. (Optional) Create a new topic branch (off the main project development branch) to
   contain your feature, change, or fix:

   ```bash
   git checkout -b <topic-branch-name>
   ```


4. Commit your changes in logical chunks. For any Git project, some good rules
   for commit messages are
   * the first line is commit summary, 50 characters or less,
   * followed by an empty line
   * followed by an explanation of the commit, wrapped to 72 characters.

   See [a note about git commit messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)
   for more.


5. Push your topic branch up to your fork:

   ```bash
   git push origin <topic-branch-name>
   ```


6. [Open a Pull Request](https://help.github.com/articles/using-pull-requests/)
   with title and description.


7. When your commit is merged to `main` branch you you can delete your branch:

   ```bash
   git checkout main
   git branch -D <topic-branch-name>
   ```