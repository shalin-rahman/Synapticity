# Synapticity 3.3: The Master Architecture Map

Welcome to the definitive breakdown of the Synapticity framework! We've documented how all the core engines, models, and workflows plug into each other so you can quickly understand exactly how the system pulls off autonomous engineering.

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
   - At the exact same time, the `MissionEngine` asks both the **QA** and **Security Auditor** agents to review the results using `concurrent.futures`.
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

The following traces the **exact Python variables and method calls** as they flow through the engine during a full mission lifecycle. Split into three stages for clarity.

#### Stage A: Bootstrap and Planning

```mermaid
flowchart TD
    subgraph BOOT ["Engine Bootstrap"]
        R1["_resolve_optimal_routing()"]
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
```
```

#### Stage B: Development and Healing Cycle

```mermaid
flowchart TD
    subgraph DEV [Phase 2 - Development]
        D1["SkillRegistry.inject builds context string"]
        D2["AgentRunner.run sends specs to SWE persona"]
        D3["AbstractModel.generate returns raw code"]
        D4["strip_markdown_backticks cleans output"]
        D5["state code stored in state dict"]
    end

    subgraph HEAL [Phase 3 - Healing Cycle]
        H1["RuntimeRunner.run_python_code returns stdout stderr success"]
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
    H7 --> H8
    H8 --> H9
    H9 --> H10
    H10 --> H1
```

#### Stage C: Finalization and Self-Learning

```mermaid
flowchart TD
    subgraph FINAL [Phase 4 - Finalization]
        F1["AgentRunner.run sends specs + code to Writer persona"]
        F2["Writer returns TECHNICAL_DOCS.md string"]
        F3["AgentRunner.run sends code to DevOps persona"]
        F4["DevOps returns GitHub Actions YAML string"]
        F5["MissionWorkspace.commit_code writes to output dir"]
        F6["MissionWorkspace.commit_docs writes TECHNICAL_DOCS.md"]
        F7["MissionWorkspace.commit_pipeline writes main.yml"]
        F8["MissionStateManager.save persists COMPLETED state"]
    end

    subgraph LEARN [Phase 5 - Self-Learning]
        L1["ReflectionEngine.analyze reads MISSION_LOG.md"]
        L2["AgentRunner.run sends audit trail to Reflector persona"]
        L3["Reflector returns lessons string"]
        L4["Lessons appended to skills autonomous-lessons skill.md"]
    end

    subgraph PERSIST [Data Stores]
        S1["state.json on disk"]
        S2["output dir with code docs and pipeline"]
        S3["MISSION_LOG.md"]
        S4["autonomous-lessons skill.md in skills dir"]
        S5["MemoryLogger JSONL in logs dir"]
    end

    F1 --> F2
    F3 --> F4
    F2 --> F6
    F4 --> F7
    F5 --> S2
    F6 --> S2
    F7 --> S2
    F8 --> S1

    L1 --> S3
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> S4
```

#### Cross-Cutting: AgentRunner Internal Flow

```mermaid
flowchart TD
    subgraph RUNNER [AgentRunner._dispatch_with_monitoring]
        A1["Read persona .md file from agents dir"]
        A2["Append USER_CUSTOM_DIRECTIVE if present"]
        A3["Build final_prompt from context + task"]
        A4["Start heartbeat monitoring thread"]
        A5["Call model_adapter.generate with system + prompt"]
        A6["MemoryLogger.log_interaction writes JSONL"]
        A7["PerformanceAnalytics.log_inference records latency"]
        A8["Return result string to caller"]
    end

    subgraph FAILOVER [Automatic Failover]
        B1["ModelProviderError caught"]
        B2["Switch to fallback_model adapter"]
        B3["Retry _dispatch_with_monitoring"]
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
    B3 --> A5
```



---

## 3. Core Engines & Libraries (`synaptic/core/`)

Here's the breakdown of the heavy lifters making all the magic happen in the background:

| Component | What it does |
| :--- | :--- |
| `MissionEngine` | The big boss (`mission_engine.py`). It calls `run(mission_id, objective)` to walk through the 5 phases, uses `_resolve_optimal_routing()` to pick the healthiest AI model gracefully, and runs `_finalize()` to wrap up your workspace. |
| `AgentRunner` | The worker bee. Its `run(prompt, context, task)` method talks to the AI, while `_dispatch_with_monitoring()` and `_run_progress_monitor()` keep your CLI updated so you aren't left staring at a blank screen. |
| `PlanningPhase` & `HealingCyclePhase` | Found in `mission_phases.py`, these manage translating goals into specs, or managing that awesome parallel retry-loop when fixing bugs. |
| `ProjectReviewEngine` | The codebase auditor. You can point `review(project_path, ...)` at any local code folder, and it will analyze the files and suggest direct code patches. |
| `SkillRegistry` | Our digital bookshelf. When you run `inject(target_str)`, it matches keywords in your prompt with our best-practice markdown playbooks, automatically teaching the AI what it needs to know. |
| `RuntimeRunner` | The sandbox. It uses `run_python_code(code)` to test things safely and `scan_security(code)` to run Bandit static analysis so nothing dangerous slips out. |
| `ReflectionEngine` | The brains. `analyze(mission_id)` reads through old logs and figures out what the AI should remember for future tasks. |
| `OfflineConsolidator` | The trainer. Executes Unsloth QLoRA fine-tuning and "Dream State" internal simulations to optimize model weights based on failed synapses. |
| `MissionStateManager` | The memory drive. Its `load()` and `save()` methods safely write the `state.json` file so you can always resume right where you left off. |
| `HippocampusController` | The librarian. Interfaces with Logseq/Obsidian Graph API to store Long-Term Potentiation (#Synapticity_LTP) indices. |

---

## 3. The Brains: AI Intelligence (`synaptic/models/`)

| File & Class      | How it thinks                                                                                                                                         |
| :---------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AbstractModel` | The basic contract that says "If you want to be an AI brain here, you must be able to `generate()` text."                                           |
| `OllamaAdapter` | Our**Zero-Latency local driver**. It keeps models infinitely loaded in the background using a `-1 keep_alive` trick so they answer instantly. |
| `GeminiAdapter` | Our**Cloud fallback**. It automatically rotates through API keys to keep you from hitting rate limits.                                          |
| `ClaudeAdapter` | The**Heavy hitter**. When we really need to figure out complex architectural problems, we default to Claude's Sonnet or Opus brains.            |

---

## 4. Helpful Utilities (`synaptic/utils/`)

| Utility            | What it helps with                                                                                                                                                        |
| :----------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SynapticDoctor` | If you run `run_full_service()`, it checks your keys, models, and connections, and even auto-fixes things using `heal()`.                                             |
| `GitDeployer`    | Makes sharing code a breeze.`deploy(path, mission_id)` physically initializes a repo and forces it straight into GitHub.                                                |
| `ProjectIndexer` | The `build_context()` scanner can recursively unpack your entire local application folder into a single readable string so an AI can read your entire codebase at once. |
| `MemoryLogger` | Uses `log_interaction()` to quietly append JSON lines in the background. It remembers everything said during a mission. |
| `SensoryCortex` | The "Eyes". Uses Firecrawl to fetch real-time documentation and bridge the knowledge gap for recently released libraries. |
| `MetabolicManager` | The "Energy Supply". Manages a 5-key pool and performs "Seamless Synaptic Handoffs" during 429 ResourceExhausted errors. |

---

## 5. The Command Hub (`synaptic/cli/`)

| Area            | Purpose                                                                                                                           |
| :-------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `registry.py` | This acts as the map tying down exactly what Python function should be called when you type a CLI command.                        |
| `ui.py`       | This makes the CLI look pretty. It renders those awesome live dashboard tables and help menus.                                    |
| `handlers/`   | We keep the actual action scripts (like `handle_launch` or `handle_learn`) separated here so the CLI layer stays lightweight. |

---

## 6. Keeping Things Safe & Fast

We put a lot of work into making sure this framework doesn't just work, but works *well*:

1. **Speed**: We preload the models into VRAM and run QA and Security tests at the exact same time to eliminate wait times.
2. **Safety**: We sandbox the code and run Bandit vulnerability checks so generated scripts don't mess up your computer.
3. **Persistence**: `state.json` means you will never lose progress on a mission, even if your computer crashes.
4. **Resilience**: If your local AI gets overloaded, it effortlessly fails over to Gemini cloud routing so the mission never stops.
