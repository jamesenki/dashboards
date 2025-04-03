# Phase 0: Agentic LLM Architecture Design Document

## Executive Summary

This design document outlines the architecture for Phase 0 of our AI integration strategy. We've designed a pragmatic, development-friendly approach that can run on M1 Mac hardware while incorporating modern agentic techniques, Retrieval Augmented Generation (RAG), and internet search capabilities. This architecture serves as the foundation for our three high-value use cases while enabling smooth transition to more robust deployments in future phases.

## Core Architecture: Development-First Agentic System

Our architecture focuses on practical implementation with minimal hardware requirements while incorporating cutting-edge techniques:

**Figure 1: Core Architecture Components**
```
┌────────────────────────────┐
│   Development Environment  │
│  ┌────────────────────┐    │
│  │ LLM Inference      │    │
│  │ (Transformers+Metal)│   │
│  └────────────────────┘    │
│  ┌────────────────────┐    │
│  │ Vector Database    │    │
│  │ (Chroma)           │    │
│  └────────────────────┘    │
│  ┌────────────────────┐    │
│  │ Agent Framework    │    │
│  │ (Local Python)     │    │
│  └────────────────────┘    │
└──────────┬─────────────────┘
           │
           ▼
┌───────────────────────────┐
│  External Services        │
│  (Cloud or Remote)        │
│ ┌─────────────────────┐   │
│ │ Search API Gateway  │   │
│ └─────────────────────┘   │
│ ┌─────────────────────┐   │
│ │ Fine-tuning (as     │   │
│ │ needed)             │   │
│ └─────────────────────┘   │
└───────────────────────────┘
```

## Detailed Component Specifications

### 1. LLM Inference Engine

**Figure 2: LLM Inference Architecture**
```
┌────────────────────────────────────────┐
│           LLM Interface                │
│  ┌────────────────────────────────┐    │
│  │   HuggingFace Transformers     │    │
│  │   (Metal-accelerated)          │    │
│  └────────────────────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌────────────────────────────────┐    │
│  │   Model Management             │    │
│  │   - Lazy Loading               │    │
│  │   - Context Management         │    │
│  └────────────────────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌────────────────────────────────┐    │
│  │   Generation Interface         │    │
│  │   - Batch & Streaming          │    │
│  │   - Parameter Management       │    │
│  └────────────────────────────────┘    │
└────────────────────────────────────────┘
```

**Primary Technology**: HuggingFace Transformers with PyTorch and Metal Performance Shaders (MPS) acceleration
**Model Selection**:
- Primary: Llama 3 8B or Mistral 7B for Mac M1/M2
- Secondary: Specialized task-specific models or smaller models like GPT-2 for testing

**Implementation Status**:
- Completed LLM interface with full MPS acceleration support for Apple Silicon
- Implemented lazy loading with automatic fallback to smaller models for testing
- Developed streaming text generation with token-by-token delivery
- Environment variable configuration for optimizing Metal performance
- Comprehensive test coverage with proper mocking and TDD approach

**Implementation Specifications**:
- **Optimization**: 8-bit loading for efficient memory usage with PyTorch
- **Context Window**: Configurable with default of 2048 tokens for development
- **Inference Optimization**:
  - Low CPU memory usage settings for efficient operation
  - Dynamic device mapping based on hardware availability
  - PyTorch MPS fallback to ensure compatibility across different operations

**Integration Points**:
- Consistent interface supporting both streaming and blocking generation
- Parameter customization including temperature, token limits, and stop sequences
- Support for both absolute and relative model paths for flexible deployment

**Hardware Requirements**:
- Mac M1/M2 with 16GB RAM (32GB recommended for larger models)
- 5-10GB free disk space for model storage
- Environment variables to enable optimal MPS acceleration

### 2. Vector Database & RAG System

**Figure 3: Vector Database Architecture**
```
┌────────────────────────────────────────┐
│         Vector Store Interface         │
│  ┌────────────────────────────────┐    │
│  │   Chroma DB                    │    │
│  │   (Persistent Document Store)  │    │
│  └────────────────────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌────────────────────────────────┐    │
│  │   Embedding System             │    │
│  │   - Dynamic Model Loading      │    │
│  │   - Metal Acceleration         │    │
│  └────────────────────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌────────────────────────────────┐    │
│  │   Query & Retrieval            │    │
│  │   - Semantic Search            │    │
│  │   - Metadata Filtering         │    │
│  └────────────────────────────────┘    │
└────────────────────────────────────────┘
```

**Primary Technology**: Chroma DB with Sentence Transformers
**Alternative**: Qdrant (if higher performance needed)

**Implementation Specifications**:
- **Embedding Model**: BAAI/bge-small-en-v1.5 (primary) with all-MiniLM-L6-v2 (fallback)
- **Vector Dimensions**: 384 dimensions for efficient storage and retrieval
- **Storage Pattern**:
  - Persistent storage with configurable location
  - Lazy-loaded components for efficient memory usage
- **Metal Acceleration**: MPS support for embedding generation on Apple Silicon

**Implementation Status**:
- Completed Vector Store with dynamic imports for improved testability
- Implemented fallback embedding functions for robust testing
- Added flexible metadata handling and filtering capabilities
- Comprehensive test coverage with proper mocking and assertions

**Advanced Features**:
- **Dynamic Loading**: Runtime module imports to avoid test-time dependency conflicts
- **Fallback Strategy**: Automatic creation of mock embeddings during tests
- **Flexible Query API**: Combining semantic search with metadata filters
- **Score Normalization**: Consistent similarity scoring for ranking results

**Integration Points**:
- Document ingestion with automatic UUID generation
- Query API with customizable result counts and filtering
- Document retrieval by ID with complete metadata

**Hardware Requirements**:
- Runs efficiently on Mac M1/M2 hardware
- SSD storage recommended for larger document collections
- Compatible with MPS acceleration for embedding generation

### 3. Agentic Framework

**Primary Technology**: Custom Python framework using ReAct pattern
**Cognitive Architecture**: Simplified MCP (Multi-Modal Cognitive Protocol)

**Implementation Specifications**:
- **Agent Components**:
  - Task decomposition module
  - Memory management system (short & long-term)
  - Tool integration registry
  - Planning and execution controller

- **Agent Capabilities**:
  - Autonomous multi-step reasoning
  - Tool selection and usage
  - Self-correction through reflection
  - Context management across interactions

- **Specialized Agents**:
  - Support Agent (customer/technician assistance)
  - Document Agent (document processing and analysis)
  - Knowledge Agent (information retrieval and synthesis)

**Integration Points**:
- Agent SDK for custom agent development
- REST API for agent interaction
- Event system for asynchronous processing

**Figure 2: Agentic Framework Detail**
```
┌───────────────────────────────────┐
│        Cognitive Controller       │
├───────────┬───────────┬───────────┤
│ Planning   │ Memory    │ Tool      │
│ Module     │ Manager   │ Registry  │
└───────────┴───────────┴───────────┘
           │
           ▼
┌───────────────────────────────────┐
│          Agent Instances          │
├───────────┬───────────┬───────────┤
│ Support   │ Document  │ Knowledge │
│ Agent     │ Agent     │ Agent     │
└───────────┴───────────┴───────────┘
           │
           ▼
┌───────────────────────────────────┐
│         Tool Integrations         │
├───────────┬───────────┬───────────┤
│ Database  │ Internet  │ API       │
│ Access    │ Search    │ Connector │
└───────────┴───────────┴───────────┘
```

### 4. Internet Search Integration

**Primary Technology**: DuckDuckGo API or SerpAPI
**Alternative**: Bing Search API (if higher quality needed)

**Implementation Specifications**:
- **Search Gateway**: Proxy service for controlled API access
- **Result Processing**:
  - HTML content extraction
  - Main content identification
  - Result summarization
  - Citation tracking
- **Query Construction**: Automatic query refinement

**Usage Optimization**:
- Implement aggressive caching (TTL-based)
- Rate limiting to control costs
- Search trigger determination logic

**Integration Points**:
- REST API for direct search
- Agent tool integration
- Mock service for testing

### 5. Feedback & Continuous Improvement System

**Implementation Specifications**:
- **Feedback Collection**:
  - Explicit feedback UI components (thumbs up/down)
  - Implicit feedback tracking (follow-up questions)
  - Task completion tracking
  - Error logging and categorization

- **Quality Assessment**:
  - Response confidence scoring
  - Relevance evaluation
  - Hallucination detection metrics

- **Improvement Pipeline**:
  - Golden dataset creation from validated interactions
  - Automated prompt refinement
  - A/B testing framework
  - Version control for prompts and configurations

**Integration Points**:
- Feedback API for collecting user responses
- Admin dashboard for reviewing feedback
- Python SDK for accessing training data

## Integration with IoTSphere-Refactor

### Connection Points

1. **API Integration**:
   - REST API endpoints for synchronous requests
   - Webhook support for asynchronous updates
   - Authentication with existing user management

2. **Data Access**:
   - Read-only connection to IoTSphere PostgreSQL database
   - Direct access to document storage for knowledge base building
   - Structured data access pattern for retrieving device information

3. **UI Integration**:
   - Web components for embedding AI features in existing interfaces
   - Chat UI module for conversational interfaces
   - Feedback collection components

### Security Considerations

1. **Authentication & Authorization**:
   - Leverage existing IoTSphere authentication
   - Role-based access control for AI features
   - API key management for external services

2. **Data Protection**:
   - All sensitive data remains within existing database
   - No persistent storage of user queries with PII
   - Audit logging of all AI interactions

3. **External Communications**:
   - Controlled gateway for all external API calls
   - Whitelisted domains for internet search
   - Monitoring and rate limiting

## Development & Deployment Workflow

### Development Environment

1. **Local Setup**:
   - Docker containers for consistent environments
   - Local model files for offline development
   - Documentation for Mac M1/M2 optimization

2. **Testing Approach**:
   - Unit tests for individual components
   - Integration tests for end-to-end flows
   - Automated evaluations for model performance

3. **Debugging Tools**:
   - Agent trace visualization
   - Prompt playground for testing
   - Log analysis dashboard

### Deployment Path

1. **Development** (Mac M1/M2):
   - All components running locally
   - Mock services for external APIs
   - Development-sized models and datasets

2. **Testing** (Cloud Resources):
   - Deployed in isolated environment
   - Integration with test database
   - Load testing and performance evaluation

3. **Production** (Server Hardware):
   - Scaled infrastructure based on testing results
   - Integration with production systems
   - Monitoring and alerting

## Implementation Roadmap for Phase 0

### Month 1: Foundation Setup (Weeks 1-4)

**Week 1-2: Core Infrastructure**
- Set up Docker development environment
- Implement basic LLM inference with llama.cpp
- Create vector database with sample documents

**Week 3-4: Basic Agent Framework**
- Develop cognitive controller with basic planning
- Implement tool registry and integration pattern
- Create simple RAG pipeline with vector database

### Month 2: Agent Development & Integration (Weeks 5-8)

**Week 5-6: Agent Specialization**
- Implement domain-specific agents
- Develop memory management system
- Create internet search integration

**Week 7-8: IoTSphere Integration**
- Establish database connection patterns
- Implement authentication integration
- Create initial API endpoints

### Month 3: Refinement & Evaluation (Weeks 9-12)

**Week 9-10: Feedback System**
- Develop feedback collection interfaces
- Implement quality assessment metrics
- Create improvement pipeline

**Week 11-12: Testing & Optimization**
- Conduct comprehensive testing
- Optimize for performance and resource usage
- Document deployment requirements

## Hardware & Resource Requirements

### Development Phase (Mac M1/M2)
- **Processor**: Apple M1/M2 chip
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 256GB SSD minimum
- **External APIs**: Search API with modest usage plan

### Testing & Evaluation Phase
- **Cloud Resources**: Small VM instance (4-8 vCPUs)
- **Optional**: GPU instance for performance testing
- **External APIs**: Expanded usage plan for realistic testing

### Production Deployment (Future)
- To be determined based on Phase 0 performance metrics
- Will include scaling strategy based on usage patterns

## Risk Assessment & Mitigation

### Technical Risks

1. **Performance Limitations**:
   - **Risk**: M1 Mac performance insufficient for responsive interactions
   - **Mitigation**: Implement aggressive optimization, offload to cloud resources if needed

2. **Integration Challenges**:
   - **Risk**: Difficulties connecting with existing IoTSphere components
   - **Mitigation**: Early integration testing, adapter pattern for flexible connections

3. **Model Quality Issues**:
   - **Risk**: Open-source models insufficient for specialized domain
   - **Mitigation**: Domain-specific fine-tuning, fallback to simpler tasks

### Business Risks

1. **Development Timeline**:
   - **Risk**: Complexity extends Phase 0 beyond 3 months
   - **Mitigation**: Clear prioritization, MVP definition, phased component rollout

2. **User Adoption**:
   - **Risk**: Resistance to AI-assisted workflows
   - **Mitigation**: Early user involvement, clear value demonstration, incremental features

3. **External API Costs**:
   - **Risk**: Search API costs exceed budget
   - **Mitigation**: Aggressive caching, usage monitors, cost controls

## Success Criteria for Phase 0

### Technical Success Metrics
- LLM inference performs at >5 tokens/second on M1 hardware
- RAG retrieval precision >80% for domain-specific queries
- Agents successfully complete multi-step tasks with >70% success rate
- System integration with IoTSphere established with clear API pattern

### Business Success Metrics
- Foundation in place for all three high-value use cases
- Clear data collection mechanisms for continuous improvement
- Demonstrable MVP for at least one use case
- Deployment path documented for production implementation

## Next Steps After Phase 0

Upon successful completion of Phase 0, we will:

1. Evaluate performance metrics against success criteria
2. Determine hardware requirements for production deployment
3. Develop scaling strategy based on usage patterns
4. Begin implementation of high-value use cases
5. Define transition path to more advanced commercial models where justified

## Appendix: Development Setup Instructions

### Docker Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/iotsphere-ai.git
cd iotsphere-ai

# Build Docker image optimized for M1
docker build -t iotsphere-ai-dev -f Dockerfile.m1 .

# Run development container
docker run -it --name iotsphere-ai-dev -p 8000:8000 -v $(pwd):/app iotsphere-ai-dev
```

### Model Download Script

```python
import os
from huggingface_hub import hf_hub_download

# Download quantized LLM
model_path = hf_hub_download(
    repo_id="TheBloke/Llama-3-8B-GGUF",
    filename="llama-3-8b.Q4_K_M.gguf",
    cache_dir="./models"
)

# Download embedding model
embedding_path = hf_hub_download(
    repo_id="BAAI/bge-small-en-v1.5",
    cache_dir="./models/embeddings"
)

print(f"Models downloaded to {os.path.dirname(model_path)}")
```

### Basic Configuration

```yaml
# config.yaml
llm:
  model_path: "./models/llama-3-8b.Q4_K_M.gguf"
  context_size: 2048
  temperature: 0.7

vector_db:
  type: "chroma"
  embedding_model: "./models/embeddings/BAAI/bge-small-en-v1.5"
  persist_directory: "./data/vectordb"

agent:
  planning_steps: 3
  max_iterations: 5
  reflection_enabled: true

search:
  provider: "duckduckgo"
  cache_ttl: 86400  # 24 hours
  rate_limit: 10  # requests per minute
```
