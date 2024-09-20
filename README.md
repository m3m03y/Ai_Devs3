This is the repository for solving tasks in AiDevs3: https://www.aidevs.pl/

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
.venv - virutal env for Python
.env - file with API_KEY value specified
For JupyterLab env variable must be added with: `%env API_KEY=<your-api-key>`

# Docker
- Add the API_KEY to .env file in project main directory
- /etc/hosts file may be updated to specify domain name for localhost ex. api.aidevs.local