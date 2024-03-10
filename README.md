# paita - Python AI Textual Assistant
<img src="https://s3.dualstack.us-east-2.amazonaws.com/pythondotorg-assets/media/files/python-logo-only.svg" height="20"> 🅰 ️ℹ️ <img src="https://textual.textualize.io/images/icons/logo%20light%20transparent.svg" height="20"> 🔧

Textual asssistant on your terminal that supports multiple AI Services' Chat Models.

## Key Features
1. **Supports Multiple AI Services:** paita integrates a variety of AI services through the [LangChain](https://python.langchain.com) library, which means any service compatible with LangChain can be added to paita for use. Currently OpenAI and AWS Bedrock are supported.                                                                                          
2. **Use Your Own AI Model:** You have full control over your AI model deployment and configuration when using Bedrock within paita, ensuring exclusive access and extensive customization of model parameters.
3. **Sophisticated Terminal UI Based on [Textual](https://textual.textualize.io/):** paita uses the Textual framework to provide an advanced user interface right within your terminal, combining the complexity of a GUI with console simplicity.                                                                                       
4. **Easy Installation and Setup:** Installing paita is as simple as running 'pip install paita', followed by configuring your chosen AI service and model according to their specific 
5. **Cross-Platform Compatibility:** Compatible with Windows, macOS, and Linux systems across most terminals; if Python runs in your environment and Textual supports it, then so does paita.

## Getting Started

### Prerequisites
- Python 3.8+

### Installation
```
pip install paita
```

### Configuring AI Service and AI Model access

```
export OPENAI_API_KEY=<OpenAI API Key>
export AWS_PROFILE=<aws-profile-name>
export AWS_DEFAULT_REGION=eu-central-1
```

```
cd paita/tui
poetry run textual run --dev app.py
```

### Development

Run debug console on 1st terminal window:
```
poetry run textual console
```

Run application on 2nd terminal window:
```
export OPENAI_API_KEY=<OpenAI API Key>
export AWS_PROFILE=<aws-profile-name>
export AWS_DEFAULT_REGION=eu-central-1

cd paita/tui
poetry run textual run --dev app.py
```
