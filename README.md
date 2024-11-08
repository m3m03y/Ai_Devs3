This is the repository for solving tasks in AiDevs3:
This repository contains notes, solutions, and resources from the [AI Devs](https://www.aidevs.pl/) course on building AI-integrated applications. The course covers a broad range of topics related to developing with large language models (LLMs), including API integration, prompt engineering, vector databases, and real-world AI applications.

# Install OLLAMA
## Linux
Resources: https://ollama.com/download/linux
```
curl -fsSL https://ollama.com/install.sh | sh
```

## Windows
Resources: https://ollama.com/download/windows

# Working with Python

## Virtual environment
*https://docs.python.org/3/library/venv.html*

```
python -m venv /path/to/new/virtual/environment # in my case: .venv
source .venv/bin/activate
pip -V # should be path to virtual env
```

### Prerequisites
- .venv - virutal env for Python
- .env - file with env variables including apis keys and task urls
- For JupyterLab env variable must be added with: `%env API_KEY=<your-api-key>`

# Docker
- use template .env.example to create .env file
- /etc/hosts file may be updated to specify domain name for localhost ex. api.aidevs.local

# Prompts
## Promptfoo
**Installation**:
```
npm install -g promptfoo
```
