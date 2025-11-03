from typing import Dict, Any, Optional, Union
from enum import Enum

class ModelProvider(Enum):
    """Supported model providers"""
    LOCAL = "local"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

class ModelConfig:
    """Configuration for different language models"""
    def __init__(
        self,
        provider: ModelProvider,
        model_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize model configuration

        Args:
            provider: Model provider
            model_name: Specific model name
            api_key: Optional API key
            **kwargs: Additional configuration parameters
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.extra_config = kwargs

class ModelIntegrator:
    """
    Centralized model integration and management utility
    """

    def __init__(self):
        """Initialize model integrator"""
        self._models: Dict[str, ModelConfig] = {}

    def register_model(
        self,
        name: str,
        config: ModelConfig
    ) -> None:
        """
        Register a new model configuration

        Args:
            name: Unique identifier for the model
            config: Model configuration
        """
        self._models[name] = config

    def get_model_config(
        self,
        name: str
    ) -> Optional[ModelConfig]:
        """
        Retrieve model configuration

        Args:
            name: Model identifier

        Returns:
            Model configuration or None
        """
        return self._models.get(name)

    def list_models(self) -> Dict[str, ModelConfig]:
        """
        List all registered models

        Returns:
            Dictionary of registered models
        """
        return self._models

    def create_model_instance(
        self,
        model_name: str,
        **override_params
    ) -> Any:
        """
        Create a model instance based on configuration

        Args:
            model_name: Name of the registered model
            **override_params: Optional parameters to override default config

        Returns:
            Instantiated language model
        """
        model_config = self.get_model_config(model_name)
        if not model_config:
            raise ValueError(f"Model {model_name} not registered")

        # Merge override parameters
        params = {**model_config.extra_config, **override_params}

        # Model instantiation based on provider
        if model_config.provider == ModelProvider.LOCAL:
            return self._create_local_model(model_config, **params)
        elif model_config.provider == ModelProvider.OPENAI:
            return self._create_openai_model(model_config, **params)
        elif model_config.provider == ModelProvider.ANTHROPIC:
            return self._create_anthropic_model(model_config, **params)
        elif model_config.provider == ModelProvider.OLLAMA:
            return self._create_ollama_model(model_config, **params)
        else:
            raise NotImplementedError(f"Provider {model_config.provider} not supported")

    def _create_local_model(
        self,
        config: ModelConfig,
        **kwargs
    ) -> Any:
        """Create local model instance"""
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model = AutoModelForCausalLM.from_pretrained(config.model_name)
        tokenizer = AutoTokenizer.from_pretrained(config.model_name)

        return model, tokenizer

    def _create_openai_model(
        self,
        config: ModelConfig,
        **kwargs
    ) -> Any:
        """Create OpenAI model instance"""
        import openai
        openai.api_key = config.api_key

        return openai.ChatCompletion.create

    def _create_anthropic_model(
        self,
        config: ModelConfig,
        **kwargs
    ) -> Any:
        """Create Anthropic model instance"""
        from anthropic import Anthropic

        client = Anthropic(api_key=config.api_key)
        return client.messages.create

    def _create_ollama_model(
        self,
        config: ModelConfig,
        **kwargs
    ) -> Any:
        """Create Ollama model instance"""
        import ollama

        return ollama.generate