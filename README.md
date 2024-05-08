# Paita - Python AI Textual Assistant
<img src="https://github.com/villekr/paita/blob/main/imgs/paita.jpg?raw=true" width="800">

Paita is textual assistant for your terminal that supports multiple AI Services and models.

## Key Features
- **Supports Multiple AI Services:** Paita integrates with a variety of AI services through the [LangChain](https://python.langchain.com) library. If AI service is compatible with LangChain then it can be used also with Paita. Currently OpenAI and AWS Bedrock models are supported.
- **Textual User Interface on your terminal:** Paita is based on [Textual](https://textual.textualize.io/) and provides a sophisticated user interface right within your terminal, combining the complexity of a GUI with console simplicity.                                                                                       
- **Cross-Platform Compatibility:** Paita is compatible with Windows, macOS, and Linux systems across most terminals; if Python runs in your environment and Textual supports it, then Paita will work.

### Supported AI Services
* OpenAI
* AWS Bedrock
* Ollama (local models)
* (More to come soon...)

## Getting Started

### Prerequisites
- Python 3.8.1+
- Access to AI Service and configured in terminal

### Installation and running

Install using pip (or pipx)
```
pip install paita
```

Run and enjoy!
```
paita
```

### Some keyboard shortcuts

Paita is textual ui application so using keyboard shortcuts is recommended:
* Use `tab` and `shift`+`tab` to navigate between input field, send-button and question/answer boxes
* While question/answer box is focus use `enter` to "focus-in" and `esc` to "focus-out"
* Use `c` to copy content from question/answer box
* Contextual keyboard shortcuts are shown at the bottom of the UI

### Configuring AI Service(s) and model access

#### OpenAI

OpenAI usage requires valid api key in environment variable.
```
export OPENAI_API_KEY=<OpenAI API Key>
```

#### AWS Bedrock

Enable AI model access in AWS Bedrock. Configure aws credential access accordingly.

#### Ollama

Ollama enables running chat models locally. 

Install [ollama](https://ollama.com) for operating system or use official (docker image)[https://hub.docker.com/r/ollama/ollama] 

Once ollama installed pull desired [model](https://ollama.com/library) from a registry e.g.
```
ollama pull llama3
```

By default paita connects to local Ollama endpoint. Optionally you can configure endpoint url with env variable:
```
export OLLAMA_ENDPOINT=<protocol>://<ollama-host-address>:<ollama-host-port>
```

## Feedback

* [Issues](https://github.com/villekr/paita/issues)
* [Discussion](https://github.com/villekr/paita/discussions)
