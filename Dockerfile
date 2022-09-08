FROM python:bullseye

## RUNTIME Deps
ENV COMMON_DEPS='ca-certificates bash-completion curl git wget lsb-release gnupg htop unzip tar jq sudo gcc vim build-essential'
ENV PIP_USER=false
RUN apt update -y && apt upgrade -y && \
    apt install -y $COMMON_DEPS

## Docker update
ARG DEBIAN_FRONTEND=noninteractive
RUN sudo mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt update && \
    apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

## Gitpod user ##
# '-l': see https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
RUN useradd -l -u 33333 -G sudo -md /home/gitpod -s /bin/bash -p gitpod gitpod \
    # passwordless sudo for users in the 'sudo' group
    && sed -i.bkp -e 's/%sudo\s\+ALL=(ALL\(:ALL\)\?)\s\+ALL/%sudo ALL=NOPASSWD:ALL/g' /etc/sudoers
ENV HOME=/home/gitpod
WORKDIR $HOME
# custom Bash prompt
RUN { echo && echo "PS1='\[\033[01;32m\]\u\[\033[00m\] \[\033[01;34m\]\w\[\033[00m\]\$(__git_ps1 \" (%s)\") $ '" ; } >> .bashrc

## Gitpod user (2) #
USER gitpod
# use sudo so that user does not get sudo usage info on (the first) login
RUN sudo echo "Running 'sudo' for Gitpod: success" && \
    # create .bashrc.d folder and source it in the bashrc
    mkdir -p /home/gitpod/.bashrc.d && \
    (echo; echo "for i in \$(ls -A \$HOME/.bashrc.d/); do source \$HOME/.bashrc.d/\$i; done"; echo) >> /home/gitpod/.bashrc

## docker rootless
RUN sudo usermod -aG docker gitpod

## Poetry Installation    
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/home/gitpod/.local python
RUN pip install --user -U pip wheel setuptools httpx[http2] lxml
ENV PATH="/home/gitpod/.local/bin:$PATH"
RUN sudo mkdir -p /workspace && sudo chown -R gitpod:gitpod /workspace
RUN id && \
    poetry --version && \
    pip --version

COPY scripts/download_exts.py download_exts.py
RUN mkdir -p $HOME/extensions && \
    python download_exts.py && \ 
    pip uninstall -y httpx[http2] lxml && \
    rm -rf download_exts.py

CMD [ "bash" ]

