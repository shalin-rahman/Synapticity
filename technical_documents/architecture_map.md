# Synapticity 3.3: Master Architecture Map

This map shows how the different parts of Synapticity work together. You can use it to understand how the system moves from your initial goal to a finished software project.

---

## System Component Map

```mermaid
flowchart TD
    subgraph CLI ["CLI Hub"]
        Main["main.py"]
        Registry["Command Registry"]
        Handlers["Command Handlers"]
    end

    subgraph CORE ["Orchestration Engine"]
        Engine["MissionEngine"]
        Review["ProjectReviewEngine"]
        SelfLearn["ReflectionEngine"]
        Phases["Mission Phases"]
    end

    subgraph AGENT ["Agent Management"]
        Dispatcher["Agent Dispatcher"]
        Runner["AgentRunner"]
    end

    subgraph STATE ["State & Sandbox"]
        Workspace["MissionWorkspace"]
        StateMgr["MissionStateManager"]
        Runtime["RuntimeRunner"]
        Skills["SkillRegistry"]
    end

    subgraph MODELS ["Intelligence Adapters"]
        Base["AbstractModel"]
        Ollama["OllamaAdapter"]
        Gemini["GeminiAdapter"]
        Claude["ClaudeAdapter"]
    end

    subgraph UTILS ["System Utilities"]
        Deployer["GitDeployer"]
        Indexer["ProjectIndexer"]
        Logger["MemoryLogger"]
        Doctor["SynapticDoctor"]
        Sensory["SensoryCortex Firecrawl"]
        Metabolic["MetabolicManager"]
    end

    subgraph MEMORY
        Buffer["SynapticBuffer"]
        Hippocampus["Hippocampus Logseq"]
        Offline["OfflineConsolidator"]
    end

    Main --> Registry
    Registry --> Handlers
    Handlers --> Engine
    Handlers --> Review
    Handlers --> SelfLearn

    Engine --> Phases
    Engine --> Dispatcher
    Review --> Dispatcher
    SelfLearn --> Dispatcher

    Phases --> Runner
    Dispatcher --> Runner

    Runner --> Skills
    Runner --> Base
    Ollama --> Base
    Gemini --> Base
    Claude --> Base

    Phases --> Runtime
    Engine --> StateMgr
    Engine --> Workspace

    Review --> Indexer
    Engine --> Deployer
    Runner --> Logger
    Engine --> Sensory
    Runner --> Metabolic
    SelfLearn --> Offline
    Offline --> Hippocampus
    Phases --> Buffer
```

---

## 1. How a Mission Actually Runs (The Daily Workflow)

At its core, Synapticity is driven by a state-machine. It moves through five distinct phases to get things done, and it won't move forward until the code passes some strict verification gates.

### Workflow A: The Standard Mission (launch or resume)

1. **Bootstrap**: First, `main.py` grabs your environment settings from `config.py` and figures out which command you want to run by checking `registry.py`.
2. **Initialization**: Then, the `MissionStateManager` either loads up your existing progress or creates a new `state.json` file. Meanwhile, our `OllamaAdapter` starts waking up local models in the background so there's no waiting around later.
3. **Phase 1 - Planning**:
   - The `MissionEngine` calls in the **Product Manager** agent.
   - Our `SkillRegistry.inject()` function quickly scans your goal for keywords (like "fastapi") and hands the agent the right technical playbooks.
   - We end up with a structurally sound `specs.json` file that acts as our architectural blueprint.
4. **Phase 2 - Development**:
   - The **Software Engineer** agent takes that blueprint and starts writing the actual source code.
   - Once finished, `MissionWorkspace.commit_code()` safely saves it all straight into your mission folder.
5. **Phase 3 - The Healing Cycle (Parallel QA)**:
   - This is the cool part. `RuntimeRunner` executes the new code in a secure sandbox.
   - At the exact same time, the `MissionEngine` asks both the **QA** and **Security Auditor** agents to review the results using `asyncio.gather`.
   - If they catch a bug, the **Software Engineer** gets pinged to apply a fix. This loops until everyone agrees the code is perfect.
6. **Phase 4 - Wrap Up**:
   - The **Technical Writer** drafts up your markdown documentation.
   - The **DevOps Engineer** writes the GitHub Action YAML files for your pipelines.
   - Finally, `GitDeployer` pushes everything up to your remote repository if you asked it to.
7. **Phase 5 - Looking Back**:
   - Right before shutting down, the `ReflectionEngine` reviews the entire mission log to see what it can learn, saving new skills for next time!

---

## 2. The Data Core: How Data Physically Transforms

If you want to know what the framework is actually moving around in memory, here is the exact lifecycle of our data payloads:

```mermaid
flowchart TD
    Input["User Mission String"]
    StateNode["state.json Tracker"]
    PlaybookNode["Engineering Playbooks"]
    PromptNode["Monolithic Context"]
    SpecsNode["specs.json Blueprint"]
    CodeNode["Synthesized Code"]
    ResultNode["Sandbox Result"]
    VerifiedNode["Hardened Source Code"]
    DeployNode["GitHub Repository"]
    ReflectionNode["Autonomous Lessons"]

    Input --> StateNode
    Input --> PlaybookNode
    PlaybookNode --> PromptNode
    PromptNode --> SpecsNode
    SpecsNode --> CodeNode

    CodeNode --> ResultNode
    ResultNode --> CodeNode
    ResultNode --> VerifiedNode
    VerifiedNode --> DeployNode
    VerifiedNode --> ReflectionNode

    style StateNode fill:#1E1E1E,stroke:#3498db,stroke-width:2px,color:#fff
    style PlaybookNode fill:#1E1E1E,stroke:#3498db,stroke-width:2px,color:#fff
    style SpecsNode fill:#1E1E1E,stroke:#3498db,stroke-width:2px,color:#fff
    style ReflectionNode fill:#1E1E1E,stroke:#3498db,stroke-width:2px,color:#fff
    style DeployNode fill:#2E86C1,stroke:#ECF0F1,stroke-width:2px,color:#fff
```


### The Code-Level DFD

#### Master Mission Lifecycle: The Data Journey

The following traces the **exact Python variables and method calls** as they flow through the engine in one continuous, autonomous lifecycle.

```mermaid
flowchart TD
    subgraph BOOT ["Stage A: Bootstrap"]
        R1["IntelligenceRouter.resolve() returns models"]
        R2["OllamaAdapter / GeminiAdapter / ClaudeAdapter"]
        R3["PerformanceAnalytics checks stats_file"]
        R4["6x AgentRunner created with primary + fallback"]
    end

    subgraph PLAN ["Phase 1 - Planning"]
        P1["MissionStateManager.load() returns state dict"]
        P2["_parse_custom_directives returns clean_obj + directives"]
        P3["PlanningPhase.run()"]
        P4["generate_context_hash checks specs.json cache"]
        P5["SkillRegistry.inject scans keywords"]
        P6["AgentRunner.run sends objective to PM persona"]
        P7["AbstractModel.generate returns specs string"]
        P8["specs.json written to disk with hash"]
    end

    subgraph DEV ["Phase 2 - Development"]
        D1["SkillRegistry.inject builds context string"]
        D2["AgentRunner.run sends specs to SWE persona"]
        D3["AbstractModel.generate returns raw code"]
        D4["strip_markdown_backticks cleans output"]
        D5["state code stored in state dict"]
    end

    subgraph HEAL ["Phase 3 - Healing Cycle"]
        H1["RuntimeRunner.run_python_code returns execution dict"]
        H2["RuntimeRunner.scan_quality returns clean and problems"]
        H3["asyncio.gather runs QA and Security in parallel"]
        H4["AgentRunner.run sends logs to QA persona"]
        H5["RuntimeRunner.scan_security returns Bandit JSON"]
        H6["AgentRunner.run sends scan to Security persona"]
        H7["Check VERDICT PASS and VERDICT SECURE"]
        H8["AgentRunner.run sends remediation to SWE persona"]
        H9["strip_markdown_backticks returns patched code"]
        H10["Loop back up to MAX_RETRY_ATTEMPTS"]
    end

    subgraph FINAL ["Phase 4 - Finalization"]
        F1["AgentRunner.run sends specs + code to Writer persona"]
        F2["Writer returns PROJECT_GUIDE.md string"]
        F3["AgentRunner.run sends code to DevOps persona"]
        F4["DevOps returns GitHub Actions YAML string"]
        F5["MissionWorkspace.commit_code writes to output dir"]
        F6["MissionWorkspace.commit_docs writes PROJECT_GUIDE.md"]
        F7["MissionWorkspace.commit_pipeline writes main.yml"]
        F8["MissionStateManager.save persists COMPLETED state"]
    end

    subgraph LEARN ["Phase 5 - Self-Learning"]
        L1["ReflectionEngine.analyze reads MISSION_LOG.md"]
        L2["AgentRunner.run sends audit trail to Reflector persona"]
        L3["Reflector returns lessons string"]
        L4["Lessons appended to skills autonomous-lessons skill.md"]
    end

    %% Connections across stages
    R1 --> R3
    R3 --> R2
    R2 --> R4
    R4 --> P1
    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> P5
    P5 --> P6
    P6 --> P7
    P7 --> P8
    P8 --> P3
    
    P3 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> D5
    
    D5 --> H1
    H1 --> H2
    H2 --> H3
    H3 --> H4
    H3 --> H5
    H5 --> H6
    H4 --> H7
    H6 --> H7
    H7 -->|Loop if FAIL| H8
    H8 --> H9
    H9 --> H10
    H10 --> H1
    
    H7 -->|Proceed if PASS| F1
    F1 --> F2
    F3 --> F4
    F2 --> F6
    F4 --> F7
    F5 --> F8
    F6 --> F8
    F7 --> F8
    F8 --> L1
    
    L1 --> L2
    L2 --> L3
    L3 --> L4
```

#### Cross-Cutting: AgentRunner Internal Flow

```mermaid
flowchart TD
    subgraph RUNNER ["AgentRunner._dispatch_with_monitoring"]
        A1["Read persona .md file from agents dir"]
        A2["Append USER_CUSTOM_DIRECTIVE if present"]
        A3["Build final_prompt from context + task"]
        A4["Start heartbeat monitoring thread"]
        A5["Call model_adapter.generate with system + prompt"]
        A6["MemoryLogger.log_interaction writes JSONL"]
        A7["PerformanceAnalytics.log_inference records latency"]
        A8["Return result string to caller"]
    end

    subgraph FAILOVER ["Reliability Failover"]
        B1["Current Local Model Error"]
        B2["Switch to Secondary Local Model (Local Failover)"]
        B3["Switch to Cloud Provider (Cloud Failover)"]
        B4["Retry _dispatch_with_monitoring"]
    end

    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> A5
    A5 --> A6
    A6 --> A7
    A7 --> A8

    A5 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> A5
```



---

---

## 3. Core Parts (`synaptic/core/`)

These are the main engines that run the system.

| Part | What it does |
| :--- | :--- |
| `MissionEngine` | Manages the project from start to finish. It uses the `IntelligenceRouter` to pick models and handles the final output. |
| `IntelligenceRouter`| **(NEW)** Selects the best AI model for the job based on your config and project history. |
| `AgentRunner` | Handles the actual calls to the AI and updates the status bar so you can see what's happening. |
| `PlanningPhase` | Plans the project architecture before any code is written. |
| `HealingCyclePhase`| Runs a loop of testing and fixing until the code works perfectly. |
| `ProjectReviewEngine` | Analyzes an existing project folder and suggests ways to improve it. |
| `SkillRegistry` | Matches your goal with technical rules (Skills) and sends them to the AI agents. |
| `RuntimeRunner` | Runs the AI-generated code in a safe sandbox to see if it works. |
| `ReflectionEngine` | Looks at the mission log after it's finished to learn from any mistakes. |
| `OfflineConsolidator` | **(Roadmap)** Fine-tunes local models using data from past missions. |
| `MissionStateManager` | Saves the project progress to `state.json` so you can resume it later. |
| `HippocampusController`| Stores the long-term history of your projects in a graph. |

---

## 4. AI Models (`synaptic/models/`)

Synapticity can use several different AI brains.

| Adapter | Description |
| :--- | :--- |
| `AbstractModel` | The standard set of rules that all AI adapters must follow. |
| `OllamaAdapter` | The local driver. It runs AI models on your own computer for free. |
| `GeminiAdapter` | The cloud driver for Google's Gemini models. It handles key rotation automatically. |
| `ClaudeAdapter` | The cloud driver for Anthropic's Claude models. |

---

## 5. Extra Tools (`synaptic/utils/`)

| Tool | Purpose |
| :--- | :--- |
| `SynapticDoctor` | Checks that your AI keys and connections are working correctly. |
| `GitDeployer` | Automatically creates a GitHub repo and pushes your new code. |
| `ProjectIndexer` | Reads all the files in a folder and packages them for the AI to read. |
| `MemoryLogger` | Logs every message sent to and from the AI agents. |
| `SensoryCortex` | **(Roadmap)** Looks up live documentation on the web to help the AI agents. |
| `MetabolicManager` | **(Roadmap)** Manages a pool of API keys to avoid rate limit errors. |

---

## 5. The Command Hub (`synaptic/cli/`)

| Area            | Purpose                                                                                                                           |
| :-------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `registry.py` | This acts as the map tying down exactly what Python function should be called when you type a CLI command.                        |
| `ui.py`       | This makes the CLI look pretty. It renders those awesome live dashboard tables and help menus.                                    |
| `handlers/`   | We keep the actual action scripts (like `handle_launch` or `handle_learn`) separated here so the CLI layer stays lightweight. |

---

## 6. Keeping Things Safe & Fast

The framework is designed to be fast and secure:

1. **Speed**: Processing models in VRAM and running QA and Security tests at the same time eliminates wait times.
2. **Safety**: Code sandboxing and Bandit vulnerability checks help ensure generated scripts are safe.
3. **Persistence**: The `state.json` tracker keeps project progress safe, even if the system stops unexpectedly.
4. **Resilience**: If a local AI becomes overloaded, the system fails over to cloud routing so the mission continues.
